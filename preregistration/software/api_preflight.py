#!/usr/bin/env python3
"""Run the frozen POLIS OpenAI contract preflight on synthetic inputs only."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "api_preflight_result.json"
FORBIDDEN_REQUEST_FIELDS = {"temperature", "top_p", "seed", "tools", "previous_response_id"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def synthetic_inputs() -> dict[str, dict[str, Any]]:
    return {
        "demand_capture": {
            "scenario_id": "PREFLIGHT-DC-001",
            "needs": [{
                "need_id": "PF-N01",
                "source_ids": ["PF-SRC01"],
                "statement": "Provide an accessible route to the synthetic garden entrance.",
                "predicate": "route_clear_width_m >= 1.8",
                "world_object_ids": ["PF-ROUTE01"],
                "candidate_parameters": ["route_clear_width_m"],
            }],
            "public_source_note": "Synthetic non-study input; no participant data.",
        },
        "conflict_detection": {
            "scenario_id": "PREFLIGHT-CD-001",
            "needs": [
                {"need_id": "PF-N01", "source_ids": ["PF-SRC01"], "object_id": "PF-PLOT01", "area_m2": 80},
                {"need_id": "PF-N02", "source_ids": ["PF-SRC02"], "object_id": "PF-PLOT01", "area_m2": 50},
            ],
            "resource_limits": {"PF-PLOT01_available_area_m2": 100},
            "public_source_note": "Synthetic non-study input; no participant data.",
        },
        "equity_guardian": {
            "scenario_id": "PREFLIGHT-EG-001",
            "groups": [
                {"group_id": "PF-G01", "input_count": 2, "retained_count": 2, "retention": 1.0, "baseline_access": 0.4, "vulnerability_weight": 1.5},
                {"group_id": "PF-G02", "input_count": 4, "retained_count": 3, "retention": 0.75, "baseline_access": 0.7, "vulnerability_weight": 1.0},
            ],
            "retention_gini": 0.18,
            "thresholds": {"group_retention_floor": 0.8, "gini_alert": 0.2},
            "need_ids": ["PF-N01", "PF-N02"],
            "source_ids": ["PF-SRC01", "PF-SRC02"],
            "public_source_note": "Synthetic analytical groups; no participant data.",
        },
        "orchestrator": {
            "scenario_id": "PREFLIGHT-OR-001",
            "validated_need_ids": ["PF-N01", "PF-N02"],
            "source_ids": ["PF-SRC01", "PF-SRC02"],
            "conflict": {"conflict_id": "PF-C01", "status": "confirmed"},
            "equity_review": {"intervention_required": True},
            "hard_constraints": [{"constraint_id": "PF-H01", "satisfied": True}],
            "feasible_parameters": {"route_clear_width_m": 1.8},
            "public_source_note": "Synthetic non-study input; no participant data.",
        },
    }


def build_request(role: str, payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["input_hash"] = sha256_text(canonical_json(payload))
    prompt = (HERE / "prompts" / f"{role}.txt").read_text(encoding="utf-8")
    schema = json.loads((HERE / "schemas" / f"{role}.schema.json").read_text(encoding="utf-8"))
    request_body = {
        "model": config["primary_model"],
        "instructions": prompt,
        "input": canonical_json(payload),
        "reasoning": config["reasoning"],
        "text": {
            "format": {
                "type": "json_schema",
                "name": role,
                "schema": schema,
                "strict": True,
            }
        },
        "store": config["store"],
        "max_output_tokens": config["max_output_tokens"],
    }
    return request_body


def validate_schema(instance: Any, schema: dict[str, Any], location: str = "$") -> None:
    if "enum" in schema and instance not in schema["enum"]:
        raise ValueError(f"{location}: value is outside enum")

    expected = schema.get("type")
    allowed = expected if isinstance(expected, list) else [expected] if expected else []
    valid_type = not allowed or any(
        (kind == "null" and instance is None)
        or (kind == "object" and isinstance(instance, dict))
        or (kind == "array" and isinstance(instance, list))
        or (kind == "string" and isinstance(instance, str))
        or (kind == "boolean" and isinstance(instance, bool))
        or (kind == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool))
        or (kind == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
        for kind in allowed
    )
    if not valid_type:
        raise ValueError(f"{location}: wrong JSON type")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(instance)
        if missing:
            raise ValueError(f"{location}: missing required fields {sorted(missing)}")
        if schema.get("additionalProperties") is False:
            extra = set(instance) - set(properties)
            if extra:
                raise ValueError(f"{location}: unexpected fields {sorted(extra)}")
        for key, value in instance.items():
            if key in properties:
                validate_schema(value, properties[key], f"{location}.{key}")
    elif isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            raise ValueError(f"{location}: too few array items")
        if "items" in schema:
            for index, value in enumerate(instance):
                validate_schema(value, schema["items"], f"{location}[{index}]")
    elif isinstance(instance, str) and "pattern" in schema:
        if re.fullmatch(schema["pattern"], instance) is None:
            raise ValueError(f"{location}: string does not match pattern")
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise ValueError(f"{location}: value below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise ValueError(f"{location}: value above maximum")


def parse_response(response: dict[str, Any]) -> tuple[str, Any]:
    text_parts: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                return "refusal", content.get("refusal", "")
            if content.get("type") == "output_text":
                text_parts.append(content.get("text", ""))
    if not text_parts:
        raise ValueError("Response contained neither output_text nor refusal")
    return "output", json.loads("".join(text_parts))


def post_json(url: str, body: dict[str, Any], api_key: str) -> tuple[dict[str, Any], dict[str, str]]:
    request = urllib.request.Request(
        url,
        data=canonical_json(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": str(uuid.uuid4()),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = json.loads(response.read().decode("utf-8"))
        retained_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"x-request-id", "openai-processing-ms", "openai-version", "date"}
        }
        return raw, retained_headers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Send four synthetic requests to the Responses API")
    parser.add_argument("--api-base", default="https://api.openai.com", help="Approved OpenAI API base URL")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    config = json.loads((HERE / "openai_responses_config.json").read_text(encoding="utf-8"))
    bodies = {role: build_request(role, payload, config) for role, payload in synthetic_inputs().items()}
    for role, body in bodies.items():
        unexpected = FORBIDDEN_REQUEST_FIELDS & set(body)
        if unexpected:
            raise ValueError(f"{role}: prohibited request fields present: {sorted(unexpected)}")
        if body["store"] is not False or body["text"]["format"]["strict"] is not True:
            raise ValueError(f"{role}: store/strict contract mismatch")

    refusal_fixture = {
        "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "Synthetic refusal fixture"}]}]
    }
    refusal_state, _ = parse_response(refusal_fixture)
    if refusal_state != "refusal":
        raise ValueError("Local refusal-handler preflight failed")

    result: dict[str, Any] = {
        "status": "OFFLINE_CONTRACT_CHECK_ONLY",
        "run_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": config["primary_model"],
        "endpoint": "/v1/responses",
        "synthetic_input_only": True,
        "participant_data_used": False,
        "schema_request_contracts_passed": sorted(bodies),
        "local_refusal_handler_passed": True,
        "network_requests_sent": 0,
        "live_results": [],
        "not_yet_confirmed": [
            "API authentication and model access",
            "four live strict-schema responses",
            "returned model and request identifiers",
            "API project region and data-retention controls",
        ],
    }

    exit_code = 0
    if args.live:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            result["status"] = "BLOCKED_NO_OPENAI_API_KEY"
            exit_code = 2
        else:
            result["network_requests_sent"] = 4
            result["not_yet_confirmed"] = ["API project region and data-retention controls"]
            try:
                for role, body in bodies.items():
                    raw, headers = post_json(args.api_base.rstrip("/") + "/v1/responses", body, api_key)
                    state, parsed = parse_response(raw)
                    if state == "refusal":
                        raise ValueError(f"{role}: unexpected refusal in benign synthetic preflight")
                    schema = body["text"]["format"]["schema"]
                    validate_schema(parsed, schema)
                    result["live_results"].append({
                        "role": role,
                        "status": "schema_valid_non_refusal",
                        "request_body": body,
                        "response": raw,
                        "retained_response_headers": headers,
                    })
                result["status"] = "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER"
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                result["status"] = "FAILED_LIVE_PREFLIGHT"
                result["error_type"] = type(exc).__name__
                result["error"] = str(exc)
                exit_code = 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"status={result['status']} output={args.output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
