#!/usr/bin/env python3
"""Frozen deterministic local indicator feedback for the POLIS workflow.

This module accepts only indicator values already computed by the local
workflow.  It never estimates missing geometry, population, legal status, or
cost.  Missing or malformed evidence is ``not_evaluable`` and cannot satisfy
the stopping target.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any, Dict, Iterable, Mapping, Optional


METRIC_SPECS = {
    "acc": {"label": "access", "threshold": 0.80, "weight": 0.25},
    "sol": {"label": "solar", "threshold": 0.60, "weight": 0.10},
    "thm": {"label": "shade_thermal_proxy", "threshold": 0.60, "weight": 0.20},
    "grn": {"label": "green_coverage", "threshold": 0.35, "weight": 0.15},
    "eco": {"label": "ecology", "threshold": 0.50, "weight": 0.15},
    "bgt": {"label": "budget_performance", "threshold": 0.95, "weight": 0.15},
}
CRITICAL_ACCESS_FLOOR = 0.70
VULNERABLE_SHADE_FLOOR = 0.50
DEPARTURE_PENALTY = 0.10


class FeedbackInputError(ValueError):
    """Raised for malformed supplied indicator evidence."""


def _number(value: Any, name: str) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise FeedbackInputError("{} must be numeric, not boolean".format(name))
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise FeedbackInputError("{} must be numeric".format(name))
    if not math.isfinite(result):
        raise FeedbackInputError("{} must be finite".format(name))
    if result < 0.0 or result > 1.0:
        raise FeedbackInputError("{} must be in [0, 1]".format(name))
    return result


def _metric_result(code: str, value: Any) -> Dict[str, Any]:
    spec = METRIC_SPECS[code]
    observed = _number(value, code)
    if observed is None:
        return {
            "metric": code,
            "label": spec["label"],
            "value": None,
            "threshold": spec["threshold"],
            "weight": spec["weight"],
            "status": "not_evaluable",
            "gap": None,
            "action_required": True,
            "reason": "indicator evidence is absent",
        }
    gap = spec["threshold"] - observed
    return {
        "metric": code,
        "label": spec["label"],
        "value": observed,
        "threshold": spec["threshold"],
        "weight": spec["weight"],
        "status": "pass" if observed >= spec["threshold"] else "fail",
        "gap": round(gap, 10),
        "action_required": observed < spec["threshold"],
    }


def feedback_access(value: Any) -> Dict[str, Any]:
    return _metric_result("acc", value)


def feedback_solar(value: Any) -> Dict[str, Any]:
    return _metric_result("sol", value)


def feedback_shade_thermal(value: Any) -> Dict[str, Any]:
    return _metric_result("thm", value)


def feedback_green_coverage(value: Any) -> Dict[str, Any]:
    return _metric_result("grn", value)


def feedback_ecology(value: Any) -> Dict[str, Any]:
    return _metric_result("eco", value)


def feedback_budget(value: Any) -> Dict[str, Any]:
    return _metric_result("bgt", value)


FEEDBACK_FUNCTIONS = {
    "acc": feedback_access,
    "sol": feedback_solar,
    "thm": feedback_shade_thermal,
    "grn": feedback_green_coverage,
    "eco": feedback_ecology,
    "bgt": feedback_budget,
}


def _object_floor(
    name: str,
    records: Any,
    floor: float,
    value_key: str,
    action: str,
) -> Dict[str, Any]:
    if records is None:
        records = []
    if not isinstance(records, list):
        raise FeedbackInputError("{} must be an array".format(name))
    results = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise FeedbackInputError("{}[{}] must be an object".format(name, index))
        object_id = str(record.get("object_id", ""))
        if not object_id:
            raise FeedbackInputError("{}[{}] is missing object_id".format(name, index))
        value = _number(record.get(value_key), "{}.{}".format(name, object_id))
        status = "not_evaluable" if value is None else ("pass" if value >= floor else "fail")
        need_ids = record.get("need_ids", [])
        source_ids = record.get("source_ids", [])
        if not isinstance(need_ids, list) or not isinstance(source_ids, list):
            raise FeedbackInputError("{}.{} need_ids/source_ids must be arrays".format(name, object_id))
        results.append({
            "object_id": object_id,
            "value": value,
            "threshold": floor,
            "status": status,
            "action_required": status != "pass",
            "required_action": None if status == "pass" else action,
            "need_ids": need_ids,
            "source_ids": source_ids,
        })
    if not results:
        group_status = "not_evaluable"
    elif all(item["status"] == "pass" for item in results):
        group_status = "pass"
    elif any(item["status"] == "not_evaluable" for item in results):
        group_status = "not_evaluable"
    else:
        group_status = "fail"
    return {
        "name": name,
        "threshold": floor,
        "objects": results,
        "status": group_status,
        "evaluable": bool(results) and all(item["status"] != "not_evaluable" for item in results),
    }


def evaluate_feedback(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate all six local feedback dimensions and object-level floors."""
    if not isinstance(payload, Mapping):
        raise FeedbackInputError("feedback payload must be an object")
    metrics = payload.get("metrics", {})
    if not isinstance(metrics, Mapping):
        raise FeedbackInputError("metrics must be an object")
    unknown_metrics = sorted(set(metrics) - set(METRIC_SPECS))
    if unknown_metrics:
        raise FeedbackInputError("unknown metrics: {}".format(unknown_metrics))
    results = {code: FEEDBACK_FUNCTIONS[code](metrics.get(code)) for code in METRIC_SPECS}
    critical = _object_floor(
        "critical_access_objects", payload.get("critical_access_objects", []),
        CRITICAL_ACCESS_FLOOR, "access", "raise local access to at least 0.70",
    )
    vulnerable = _object_floor(
        "vulnerable_use_zones", payload.get("vulnerable_use_zones", []),
        VULNERABLE_SHADE_FLOOR, "shade_thermal_proxy", "raise local shade/thermal proxy to at least 0.50",
    )
    metric_target = all(item["status"] == "pass" for item in results.values())
    object_target = critical["status"] == "pass" and vulnerable["status"] == "pass"
    hard_constraints = payload.get("hard_constraints", [])
    if not isinstance(hard_constraints, list):
        raise FeedbackInputError("hard_constraints must be an array")
    hard_results = []
    for index, item in enumerate(hard_constraints):
        if not isinstance(item, Mapping) or not item.get("constraint_id"):
            raise FeedbackInputError("hard_constraints[{}] needs constraint_id".format(index))
        satisfied = item.get("satisfied")
        if not (satisfied is True or satisfied is False or satisfied is None):
            raise FeedbackInputError("hard_constraints[{}].satisfied must be true, false, or null".format(index))
        status = "not_evaluable" if satisfied is None else ("pass" if satisfied is True else "fail")
        hard_results.append({"constraint_id": str(item["constraint_id"]), "status": status})
    hard_target = bool(hard_results) and all(item["status"] == "pass" for item in hard_results)
    parameter_departure = _number(payload.get("parameter_departure", 0.0), "parameter_departure")
    departure = 0.0 if parameter_departure is None else parameter_departure
    observed_values = [item["value"] for item in results.values() if item["value"] is not None]
    objective_score = None
    if len(observed_values) == len(METRIC_SPECS):
        objective_score = round(sum(results[code]["value"] * METRIC_SPECS[code]["weight"] for code in METRIC_SPECS) - DEPARTURE_PENALTY * departure, 10)
    actions = [
        {"metric": item["metric"], "required_action": "raise {} to at least {}".format(item["label"], item["threshold"])}
        for item in results.values() if item["action_required"]
    ]
    actions.extend(
        {"metric": "object_floor", "object_id": item["object_id"], "required_action": item["required_action"]}
        for group in (critical, vulnerable) for item in group["objects"] if item["action_required"]
    )
    return {
        "scenario_id": payload.get("scenario_id"),
        "revision_cycle": payload.get("revision_cycle", 0),
        "metrics": results,
        "critical_access_objects": critical,
        "vulnerable_use_zones": vulnerable,
        "hard_constraints": hard_results,
        "objective_score": objective_score,
        "parameter_departure": departure,
        "target_met": metric_target and object_target and hard_target,
        "all_evaluable": all(item["status"] != "not_evaluable" for item in results.values()) and critical["evaluable"] and vulnerable["evaluable"] and all(item["status"] != "not_evaluable" for item in hard_results),
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate frozen POLIS local feedback")
    parser.add_argument("--input", required=True, type=argparse.FileType("r", encoding="utf-8"))
    parser.add_argument("--output", required=True, type=argparse.FileType("w", encoding="utf-8"))
    args = parser.parse_args()
    result = evaluate_feedback(json.load(args.input))
    json.dump(result, args.output, indent=2, ensure_ascii=True)
    args.output.write("\n")
    return 0 if result["all_evaluable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
