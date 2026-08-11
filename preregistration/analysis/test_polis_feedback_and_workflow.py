#!/usr/bin/env python3
"""Offline tests for the deterministic feedback and POLIS coordination layers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PREREG = Path(__file__).resolve().parents[1]
ROOT = PREREG.parent
if str(PREREG) not in sys.path:
    sys.path.insert(0, str(PREREG))

from analysis.polis_feedback_functions import evaluate_feedback
from polis_workflow_runner import AgentClient, run_workflow


class FeedbackTests(unittest.TestCase):
    def passing_payload(self):
        return {
            "scenario_id": "TEST-001",
            "metrics": {"acc": 0.80, "sol": 0.60, "thm": 0.60, "grn": 0.35, "eco": 0.50, "bgt": 0.95},
            "critical_access_objects": [{"object_id": "R1", "access": 0.70}],
            "vulnerable_use_zones": [{"object_id": "V1", "shade_thermal_proxy": 0.50}],
            "hard_constraints": [{"constraint_id": "C1", "satisfied": True}],
            "parameter_departure": 0.0,
        }

    def test_all_thresholds_and_object_floors_pass(self):
        result = evaluate_feedback(self.passing_payload())
        self.assertTrue(result["target_met"])
        self.assertTrue(result["all_evaluable"])
        self.assertEqual(result["metrics"]["bgt"]["status"], "pass")

    def test_missing_metric_is_not_evaluable_and_cannot_pass(self):
        payload = self.passing_payload()
        del payload["metrics"]["eco"]
        result = evaluate_feedback(payload)
        self.assertEqual(result["metrics"]["eco"]["status"], "not_evaluable")
        self.assertFalse(result["target_met"])
        self.assertFalse(result["all_evaluable"])

    def test_missing_object_evidence_cannot_pass(self):
        payload = self.passing_payload()
        payload["critical_access_objects"] = []
        result = evaluate_feedback(payload)
        self.assertEqual(result["critical_access_objects"]["status"], "not_evaluable")
        self.assertFalse(result["target_met"])

def fixture(role, agent_role=None):
    role = agent_role or role
    base = {"agent_role": role, "scenario_id": "$SCENARIO_ID", "input_hash": "$INPUT_HASH", "unresolved_items": []}
    if role == "demand_capture":
        base["demand_records"] = [{"need_id": "$NEED_ID", "source_ids": ["$SOURCE_ID"], "world_object_ids": [], "candidate_parameters": [], "predicate_preserved": True}]
    elif role == "conflict_detection":
        base["conflicts"] = []
    elif role == "equity_guardian":
        base.update({"retention_gini": None, "group_retention": [], "interventions": []})
    else:
        base.update({"decisions": [{"decision_id": "D1", "action": "unresolved", "need_ids": ["SUZ-N01"], "source_ids": ["INT-PREREG"], "affected_parameters": [], "review_trigger": "candidate export", "rationale": "Fixture only."}], "hard_constraint_override": False})
    return base


class WorkflowTests(unittest.TestCase):
    def test_schema_invalid_response_is_retried_once_and_audited(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture_dir = Path(temp)
            (fixture_dir / "demand_capture.1.json").write_text(
                json.dumps(fixture("demand_capture", "conflict_detection")) + "\n", encoding="ascii"
            )
            (fixture_dir / "demand_capture.2.json").write_text(
                json.dumps(fixture("demand_capture")) + "\n", encoding="ascii"
            )
            client = AgentClient(fixture_dir)
            result = client.call("demand_capture", {"scenario_id": "TEST-RETRY", "needs": []})
            self.assertEqual(result["agent_role"], "demand_capture")
            self.assertEqual([item["status"] for item in client.audit], ["schema_invalid", "schema_valid_non_refusal"])
            self.assertIsNotNone(client.audit[0]["response"])
            self.assertEqual(client.audit[1]["retry_of_attempt"], 1)

    def test_offline_four_role_workflow_and_two_pass_stop(self):
        package = PREREG / "experiment1_scenario_packages/SUZ-GE-B.json"
        with tempfile.TemporaryDirectory() as temp:
            fixture_dir = Path(temp) / "fixtures"
            output_dir = Path(temp) / "output"
            fixture_dir.mkdir()
            for role in ("demand_capture", "conflict_detection", "equity_guardian", "orchestrator"):
                (fixture_dir / (role + ".json")).write_text(json.dumps(fixture(role)) + "\n", encoding="ascii")
            candidate = {
                "candidate_id": "SUZ-GE-B-POLIS-C00",
                "design_geopackage_sha256": "0" * 64,
                "feedback_output_sha256": "1" * 64,
                "revision_cycle": 0,
                "metrics": {"acc": 0.80, "sol": 0.60, "thm": 0.60, "grn": 0.35, "eco": 0.50, "bgt": 0.95},
                "critical_access_objects": [{"object_id": "R1", "access": 0.70, "need_ids": ["SUZ-N01"], "source_ids": ["INT-PREREG"]}],
                "vulnerable_use_zones": [{"object_id": "V1", "shade_thermal_proxy": 0.50, "need_ids": ["SUZ-N08"], "source_ids": ["INT-PREREG"]}],
                "hard_constraints": [{"constraint_id": "C1", "satisfied": True}],
                "parameter_departure": 0.0,
                "elapsed_minutes": 20.0,
                "professional_person_hours": 1.0,
                "scenario_compute_minutes": 10.0,
            }
            result = run_workflow(package, output_dir, AgentClient(fixture_dir), [candidate, candidate], "OP_TEST")
            self.assertEqual(result["status"], "completed_target_met")
            self.assertEqual(result["stop_reason"], "internal_target_confirmed_two_consecutive_evaluations")
            self.assertEqual(len(result["candidate_evaluations"]), 2)
            self.assertTrue((output_dir / "polis_workflow_output.json").is_file())
            self.assertGreaterEqual(len(result["audit"]), 33)


if __name__ == "__main__":
    unittest.main()
