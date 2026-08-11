#!/usr/bin/env python3
"""Run the frozen POLIS coordination workflow.

The runner coordinates four strict-schema logical agents.  Geometry generation
and the five-outcome evaluator remain local handoffs; this module never
inventories missing spatial evidence and never selects a design on behalf of
the registered operator.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import jsonschema

from analysis.polis_feedback_functions import FeedbackInputError, evaluate_feedback
from software import api_preflight


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "preregistration"
SCHEMA_DIR = PREREG / "software/schemas"
PROMPT_DIR = PREREG / "software/prompts"
CONFIG_PATH = PREREG / "software/openai_responses_config.json"
CANDIDATE_SCHEMA_PATH = SCHEMA_DIR / "polis_candidate_evaluation.schema.json"
ROLES = ("demand_capture", "conflict_detection", "equity_guardian", "orchestrator")
MAX_SCHEMA_ATTEMPTS = 2
MAX_REVISION_CYCLES = 30
MAX_ELAPSED_MINUTES = 120.0
MAX_PERSON_HOURS = 8.0
MAX_COMPUTE_MINUTES = 120.0


class WorkflowError(RuntimeError):
    """Raised when a POLIS run cannot produce a valid role handoff."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parameters(value: str) -> List[str]:
    """Extract only explicitly named parameter identifiers from a predicate."""
    return sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*(?=\s*(?:>=|<=|=))", value or "")))


def load_package(path: Path) -> Dict[str, Any]:
    package = json.loads(path.read_text(encoding="utf-8"))
    if package.get("data_boundary", {}).get("participant_data_included") is not False:
        raise WorkflowError("scenario package is not explicitly participant-data free")
    if package.get("input_hash") != sha256_text(canonical({key: value for key, value in package.items() if key != "input_hash"})):
        raise WorkflowError("scenario package input_hash mismatch")
    return package


def demand_payload(package: Mapping[str, Any], need_items: Optional[List[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    records = []
    for item in need_items if need_items is not None else package.get("needs", []):
        need = item["need"]
        predicate = item["predicate"]
        records.append({
            "need_id": need["need_id"],
            "source_ids": [need["source_id"]],
            "statement": need["requested_change"],
            "predicate": need["parametric_implication"],
            "world_object_ids": [],
            "candidate_parameters": _parameters(need["parametric_implication"]),
        })
    return {
        "scenario_id": package["scenario"]["scenario_id"],
        "needs": records,
        "public_source_note": "Frozen non-participant analytical inputs only.",
    }


def conflict_payload(package: Mapping[str, Any], demand: Mapping[str, Any],
                     need_items: Optional[List[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    visible_needs = need_items if need_items is not None else package.get("needs", [])
    return {
        "scenario_id": package["scenario"]["scenario_id"],
        "needs": [
            {"need_id": item["need"]["need_id"], "source_ids": [item["need"]["source_id"]],
             "object_id": None, "area_m2": None, "conflict_links": item["need"].get("conflict_links", "")}
            for item in visible_needs
        ],
        "demand_records": demand["demand_records"],
        "resource_limits": package.get("scenario_resource_register", {}),
        "site_constraints": package.get("site_constraint_register", []),
        "world_model": package.get("world_model", {}),
        "public_source_note": "Frozen non-participant analytical inputs only.",
    }


def equity_payload(package: Mapping[str, Any], demand: Mapping[str, Any], conflicts: Mapping[str, Any],
                   need_items: Optional[List[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    # No group profile is inferred from a beneficiary label.  A study package
    # may provide frozen analytical groups explicitly; otherwise the agent must
    # report the missing evidence as unresolved.
    return {
        "scenario_id": package["scenario"]["scenario_id"],
        "groups": package.get("equity_groups", []),
        "retention_gini": package.get("retention_gini"),
        "thresholds": {
            "group_retention_floor": 0.75,
            "gini_alert": 0.20,
            "gini_reengagement": 0.25,
        },
        "demand_records": demand["demand_records"],
        "conflicts": conflicts["conflicts"],
        "need_ids": [item["need"]["need_id"] for item in (need_items if need_items is not None else package.get("needs", []))],
        "source_ids": sorted({item["need"]["source_id"] for item in (need_items if need_items is not None else package.get("needs", []))}),
        "public_source_note": "Frozen analytical groups only; no participant data.",
    }


def orchestrator_payload(
    package: Mapping[str, Any], demand: Mapping[str, Any], conflicts: Mapping[str, Any],
    equity: Mapping[str, Any], feedback: Mapping[str, Any], previous: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "scenario_id": package["scenario"]["scenario_id"],
        "validated_need_ids": sorted({item["need_id"] for item in demand.get("demand_records", [])}),
        "source_ids": sorted({source_id for item in demand.get("demand_records", []) for source_id in item.get("source_ids", [])}),
        "demand_capture": demand,
        "conflict_detection": conflicts,
        "equity_review": equity,
        "local_feedback": feedback,
        "previous_decisions": previous or {},
        "hard_constraints": [
            {"constraint_id": row.get("constraint_id", ""), "satisfied": None}
            for row in package.get("site_constraint_register", [])
        ],
        "feasible_parameters": {},
        "public_source_note": "Frozen non-participant analytical inputs only.",
    }


def _replace_fixture(value: Any, scenario_id: str, input_hash: str,
                     replacements: Optional[Mapping[str, str]] = None) -> Any:
    if isinstance(value, str):
        result = value.replace("$SCENARIO_ID", scenario_id).replace("$INPUT_HASH", input_hash)
        for source, target in (replacements or {}).items():
            result = result.replace(source, target)
        return result
    if isinstance(value, list):
        return [_replace_fixture(item, scenario_id, input_hash, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_fixture(item, scenario_id, input_hash, replacements) for key, item in value.items()}
    return value


class AgentClient:
    """Frozen Responses API client with a deterministic fixture transport."""

    def __init__(self, fixture_dir: Optional[Path] = None, api_base: str = "https://api.openai.com"):
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.fixture_dir = fixture_dir
        self.api_base = api_base.rstrip("/")
        self.audit: List[Dict[str, Any]] = []

    def _fixture(self, role: str, attempt: int, scenario_id: str, input_hash: str,
                 request_input: Mapping[str, Any]) -> Dict[str, Any]:
        candidates = [self.fixture_dir / ("{}.{}.json".format(role, attempt)), self.fixture_dir / (role + ".json")]
        path = next((item for item in candidates if item.is_file()), None)
        if path is None:
            raise WorkflowError("missing fixture for {} attempt {}".format(role, attempt))
        first_need = (request_input.get("needs") or [{}])[0]
        request_need_ids = request_input.get("validated_need_ids") or request_input.get("need_ids") or []
        request_source_ids = request_input.get("source_ids") or []
        replacements = {
            "$NEED_ID": str(first_need.get("need_id") or (request_need_ids[0] if request_need_ids else "FIXTURE-N01")),
            "$SOURCE_ID": str((first_need.get("source_ids") or request_source_ids or ["FIXTURE-SRC01"])[0]),
        }
        value = _replace_fixture(json.loads(path.read_text(encoding="utf-8")), scenario_id, input_hash, replacements)
        if value.get("output") is not None:
            return value
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(value, ensure_ascii=True)}]}]}

    def call(self, role: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        frozen_payload = dict(payload)
        first_body = api_preflight.build_request(role, frozen_payload, self.config)
        scenario_id = str(frozen_payload.get("scenario_id", ""))
        original_input = json.loads(first_body["input"])
        input_hash = original_input["input_hash"]
        schema = first_body["text"]["format"]["schema"]
        last_error = ""
        for attempt in range(1, MAX_SCHEMA_ATTEMPTS + 1):
            body = first_body
            raw: Optional[Dict[str, Any]] = None
            headers: Dict[str, str] = {}
            if attempt == 2:
                retry_input = dict(original_input)
                retry_input["schema_validation_error"] = last_error
                body = dict(first_body)
                body["input"] = api_preflight.canonical_json(retry_input)
            started = time.time()
            started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                if self.fixture_dir:
                    raw = self._fixture(role, attempt, scenario_id, input_hash, original_input)
                    headers = {}
                else:
                    import os
                    key = os.environ.get("OPENAI_API_KEY", "")
                    if not key:
                        raise WorkflowError("OPENAI_API_KEY is not set; use --fixtures for offline validation")
                    raw, headers = api_preflight.post_json(self.api_base + "/v1/responses", body, key)
                state, parsed = api_preflight.parse_response(raw)
                entry = {"role": role, "attempt": attempt, "request": body, "response": raw, "headers": headers,
                         "request_sha256": sha256_text(canonical(body)),
                         "response_sha256": sha256_text(canonical(raw)),
                         "started_at_utc": started_utc,
                         "ended_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                         "elapsed_seconds": round(time.time() - started, 6),
                         "retry_of_attempt": 1 if attempt == 2 else None}
                if state == "refusal":
                    entry["status"] = "refusal"
                    self.audit.append(entry)
                    raise WorkflowError("{} returned a refusal".format(role))
                api_preflight.validate_schema(parsed, schema)
                if parsed.get("agent_role") != role or parsed.get("scenario_id") != scenario_id:
                    raise ValueError("role or scenario_id does not match frozen request")
                if parsed.get("input_hash") != input_hash:
                    raise ValueError("agent input_hash does not match frozen payload")
                entry["status"] = "schema_valid_non_refusal"
                self.audit.append(entry)
                return parsed
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                last_error = str(exc)
                self.audit.append({"role": role, "attempt": attempt, "status": "schema_invalid", "error": last_error,
                                   "request": body, "response": raw, "headers": headers,
                                   "request_sha256": sha256_text(canonical(body)),
                                   "response_sha256": None if raw is None else sha256_text(canonical(raw)),
                                   "started_at_utc": started_utc,
                                   "ended_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                   "elapsed_seconds": round(time.time() - started, 6),
                                   "retry_of_attempt": 1 if attempt == 2 else None})
                if attempt == MAX_SCHEMA_ATTEMPTS:
                    raise WorkflowError("{} failed schema validation after one retry: {}".format(role, last_error))
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                self.audit.append({"role": role, "attempt": attempt, "status": "transport_error", "error": str(exc),
                                   "request": body, "response": raw, "headers": headers,
                                   "request_sha256": sha256_text(canonical(body)),
                                   "response_sha256": None if raw is None else sha256_text(canonical(raw)),
                                   "started_at_utc": started_utc,
                                   "ended_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                   "elapsed_seconds": round(time.time() - started, 6),
                                   "retry_of_attempt": 1 if attempt == 2 else None})
                raise WorkflowError("{} transport failed: {}".format(role, exc))
        raise WorkflowError("unreachable agent state")


def validate_role_references(role: str, output: Mapping[str, Any], known_need_ids: set,
                             known_source_ids: set, allowed_parameters: Optional[set] = None) -> None:
    """Reject model-created provenance identifiers or design parameters."""
    if role == "demand_capture":
        records = output.get("demand_records", [])
        returned_need_ids = {item.get("need_id") for item in records}
        if returned_need_ids != known_need_ids:
            raise WorkflowError("demand_capture must return exactly the supplied need IDs")
        for item in records:
            if not set(item.get("source_ids", [])).issubset(known_source_ids):
                raise WorkflowError("demand_capture returned an unknown source ID")
            if not set(item.get("candidate_parameters", [])).issubset(allowed_parameters or set()):
                raise WorkflowError("demand_capture returned an unsupplied candidate parameter")
            if item.get("world_object_ids"):
                raise WorkflowError("demand_capture returned world-object IDs that were not supplied")
    elif role == "conflict_detection":
        for item in output.get("conflicts", []):
            if not set(item.get("need_ids", [])).issubset(known_need_ids):
                raise WorkflowError("conflict_detection returned an unknown need ID")
            if not set(item.get("evidence_source_ids", [])).issubset(known_source_ids):
                raise WorkflowError("conflict_detection returned an unknown source ID")
    elif role == "equity_guardian":
        for item in output.get("interventions", []):
            if not set(item.get("need_ids", [])).issubset(known_need_ids):
                raise WorkflowError("equity_guardian returned an unknown need ID")
            if not set(item.get("source_ids", [])).issubset(known_source_ids):
                raise WorkflowError("equity_guardian returned an unknown source ID")
    elif role == "orchestrator":
        for item in output.get("decisions", []):
            if not set(item.get("need_ids", [])).issubset(known_need_ids):
                raise WorkflowError("orchestrator returned an unknown need ID")
            if not set(item.get("source_ids", [])).issubset(known_source_ids):
                raise WorkflowError("orchestrator returned an unknown source ID")
            if not set(item.get("affected_parameters", [])).issubset(allowed_parameters or set()):
                raise WorkflowError("orchestrator returned an unsupplied affected parameter")


def run_workflow(package_path: Path, output_dir: Path, client: AgentClient,
                 candidate_evaluations: Optional[List[Mapping[str, Any]]] = None,
                 operator_id: Optional[str] = None) -> Dict[str, Any]:
    package = load_package(package_path)
    scenario_id = package["scenario"]["scenario_id"]
    demand = {"demand_records": [], "unresolved_items": []}
    conflicts: Dict[str, Any] = {"conflicts": [], "unresolved_items": []}
    equity: Dict[str, Any] = {"interventions": [], "unresolved_items": []}
    decisions: Optional[Dict[str, Any]] = None
    demand_events: List[Dict[str, Any]] = []
    visible_items: List[Mapping[str, Any]] = []
    allowed_parameters: set = set()
    for event_index, item in enumerate(package.get("needs", []), start=1):
        visible_items.append(item)
        need = item["need"]
        event_parameters = set(_parameters(need.get("parametric_implication", "")))
        allowed_parameters.update(event_parameters)
        event_demand = client.call("demand_capture", demand_payload(package, [item]))
        validate_role_references("demand_capture", event_demand, {need["need_id"]}, {need["source_id"]}, event_parameters)
        demand["demand_records"].extend(event_demand["demand_records"])
        demand["unresolved_items"].extend(event_demand.get("unresolved_items", []))
        known_need_ids = {record["need_id"] for record in demand["demand_records"]}
        known_source_ids = {source_id for record in demand["demand_records"] for source_id in record["source_ids"]}
        conflicts = client.call("conflict_detection", conflict_payload(package, demand, visible_items))
        validate_role_references("conflict_detection", conflicts, known_need_ids, known_source_ids)
        equity = client.call("equity_guardian", equity_payload(package, demand, conflicts, visible_items))
        validate_role_references("equity_guardian", equity, known_need_ids, known_source_ids)
        pending_feedback = {"status": "pending", "reason": "candidate design has not been exported", "demand_event_index": event_index}
        decisions = client.call("orchestrator", orchestrator_payload(package, demand, conflicts, equity, pending_feedback, decisions))
        validate_role_references("orchestrator", decisions, known_need_ids, known_source_ids, allowed_parameters)
        demand_events.append({"event_index": event_index, "need_id": need["need_id"], "demand_capture": event_demand,
                              "conflict_detection": conflicts, "equity_guardian": equity, "orchestrator": decisions})
    evaluations = candidate_evaluations or []
    candidate_schema = json.loads(CANDIDATE_SCHEMA_PATH.read_text(encoding="utf-8"))
    candidate_validator = jsonschema.Draft202012Validator(candidate_schema)
    records: List[Dict[str, Any]] = []
    consecutive_passes = 0
    stop_reason = "waiting_for_candidate_design"
    for index, candidate in enumerate(evaluations, start=1):
        errors = sorted(candidate_validator.iter_errors(candidate), key=lambda item: list(item.absolute_path))
        if errors:
            error = errors[0]
            location = ".".join(str(value) for value in error.absolute_path) or "$"
            raise WorkflowError("candidate evaluation {} schema error at {}: {}".format(index, location, error.message))
        state = dict(candidate)
        state["scenario_id"] = scenario_id
        state["revision_cycle"] = int(state.get("revision_cycle", index - 1))
        try:
            feedback = evaluate_feedback(state)
        except FeedbackInputError as exc:
            raise WorkflowError("candidate evaluation {} is invalid: {}".format(index, exc))
        if feedback["target_met"]:
            consecutive_passes += 1
        else:
            consecutive_passes = 0
        record = {"revision_cycle": state["revision_cycle"], "feedback": feedback,
                  "operator_id": operator_id, "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        records.append(record)
        elapsed = float(state.get("elapsed_minutes", 0.0))
        person_hours = float(state.get("professional_person_hours", 0.0))
        compute = float(state.get("scenario_compute_minutes", 0.0))
        if consecutive_passes >= 2:
            stop_reason = "internal_target_confirmed_two_consecutive_evaluations"
            break
        if state["revision_cycle"] >= MAX_REVISION_CYCLES or elapsed >= MAX_ELAPSED_MINUTES or person_hours >= MAX_PERSON_HOURS or compute >= MAX_COMPUTE_MINUTES:
            stop_reason = "cap_reached_target_not_reached"
            break
        decisions = client.call("orchestrator", orchestrator_payload(package, demand, conflicts, equity, feedback, decisions))
        validate_role_references("orchestrator", decisions, known_need_ids, known_source_ids, allowed_parameters)
    if stop_reason == "internal_target_confirmed_two_consecutive_evaluations":
        workflow_status = "completed_target_met"
    elif stop_reason == "cap_reached_target_not_reached":
        workflow_status = "completed_target_not_reached"
    elif records:
        workflow_status = "awaiting_next_candidate_evaluation"
    else:
        workflow_status = "waiting_for_candidate_design"
    output = {
        "status": workflow_status,
        "scenario_id": scenario_id,
        "operator_id": operator_id,
        "scenario_package": str(package_path),
        "scenario_package_sha256": sha256_file(package_path),
        "agent_outputs": {"demand_capture": demand, "conflict_detection": conflicts, "equity_guardian": equity, "orchestrator": decisions},
        "demand_events": demand_events,
        "candidate_evaluations": records,
        "stop_reason": stop_reason,
        "limits": {"max_revision_cycles": MAX_REVISION_CYCLES, "max_elapsed_minutes": MAX_ELAPSED_MINUTES, "max_professional_person_hours": MAX_PERSON_HOURS, "max_scenario_compute_minutes": MAX_COMPUTE_MINUTES},
        "audit": client.audit,
        "contract_files": {"config": sha256_file(CONFIG_PATH), "candidate_evaluation_schema": sha256_file(CANDIDATE_SCHEMA_PATH), "schemas": {role: sha256_file(SCHEMA_DIR / (role + ".schema.json")) for role in ROLES}, "prompts": {role: sha256_file(PROMPT_DIR / (role + ".txt")) for role in ROLES}},
        "claim_boundary": "Coordination and local feedback trace only; not legal compliance, construction readiness, resident preference, or measured thermal comfort.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "polis_workflow_output.json").write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen POLIS workflow")
    parser.add_argument("--scenario-package", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--fixtures", type=Path, help="offline response fixture directory")
    parser.add_argument("--candidate-evaluations", type=Path, help="JSON array of local evaluator states")
    parser.add_argument("--operator-id")
    parser.add_argument("--api-base", default="https://api.openai.com")
    args = parser.parse_args()
    evaluations = None if args.candidate_evaluations is None else json.loads(args.candidate_evaluations.read_text(encoding="utf-8"))
    client = AgentClient(args.fixtures, args.api_base)
    try:
        result = run_workflow(args.scenario_package, args.output_dir, client, evaluations, args.operator_id)
    except (WorkflowError, OSError, ValueError, json.JSONDecodeError) as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure = {
            "status": "failed",
            "scenario_package": str(args.scenario_package),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "failed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "audit": client.audit,
        }
        (args.output_dir / "polis_workflow_failure.json").write_text(
            json.dumps(failure, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
        )
        print("POLIS_WORKFLOW_FAILED: {}".format(exc))
        return 2
    print(json.dumps({"status": result["status"], "stop_reason": result["stop_reason"], "output": str(args.output_dir / "polis_workflow_output.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
