#!/usr/bin/env python3
"""Create the frozen Experiment 1 run queue without generating outcomes."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "preregistration"
WORLD = ROOT / "world_model"
OUTPUT = PREREG / "experiment1_run_manifest.csv"
WORKFLOWS = ("EXISTING", "CONVENTIONAL", "DIGITAL", "POLIS")
SITE_FILES = {
    "Suzhou": WORLD / "vector/suz_world_model.gpkg",
    "London": WORLD / "vector/lon_world_model.gpkg",
    "Chicago": WORLD / "vector/chi_world_model.gpkg",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    world_report = json.loads(
        (WORLD / "validation/world_model_validation.json").read_text(encoding="utf-8")
    )
    if not world_report.get("experiment_1_ready"):
        raise RuntimeError("World-model input gate has not passed")

    scenarios = read_csv(PREREG / "scenarios.csv")
    assignments = {
        (row["scenario_id"], row["workflow"]): row
        for row in read_csv(PREREG / "protocols/operator_assignment_plan.csv")
    }
    rows: list[dict[str, str | int]] = []
    for scenario in scenarios:
        site = scenario["site"]
        gpkg = SITE_FILES[site]
        for workflow in WORKFLOWS:
            assignment = assignments.get((scenario["scenario_id"], workflow), {})
            is_existing = workflow == "EXISTING"
            operator_id = "NOT_APPLICABLE" if is_existing else assignment.get("real_operator_id", "")
            assignment_ready = is_existing or (
                bool(operator_id)
                and assignment.get("assignment_status") == "assigned"
                and assignment.get("pi_verified", "").lower() == "yes"
            )
            rows.append({
                "run_id": f"EXP1-{scenario['scenario_id']}-{workflow}",
                "scenario_id": scenario["scenario_id"],
                "site": site,
                "decision_type": scenario["decision_type"],
                "variant": scenario["variant"],
                "workflow": workflow,
                "exp1_seed": scenario["exp1_seed"],
                "world_model_file": gpkg.relative_to(ROOT).as_posix(),
                "world_model_sha256": sha256(gpkg),
                "operator_id": operator_id,
                "operator_assignment_ready": "yes" if assignment_ready else "no",
                "input_status": "FROZEN_WORLD_MODEL",
                "run_status": "READY_EXISTING_EVALUATION" if is_existing else (
                    "READY_FOR_OPERATOR" if assignment_ready else "BLOCKED_OPERATOR_ASSIGNMENT"
                ),
                "output_geometry": "",
                "output_parameter_table": "",
                "output_need_disposition": "",
                "output_constraint_checklist": "",
                "output_process_log": "",
                "rhino_export_record": "",
                "outcome_A_green": "",
                "outcome_E_equity": "",
                "outcome_C_comfort": "",
                "outcome_P_ret": "",
                "outcome_I_impl": "",
                "failure_or_exclusion_code": "",
            })

    if len(rows) != 144:
        raise RuntimeError(f"Expected 144 Experiment 1 rows, found {len(rows)}")
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "output": OUTPUT.relative_to(ROOT).as_posix(),
                "rows": len(rows),
                "existing_rows": sum(row["workflow"] == "EXISTING" for row in rows),
                "active_rows": sum(row["workflow"] != "EXISTING" for row in rows),
                "blocked_operator_rows": sum(
                    row["run_status"] == "BLOCKED_OPERATOR_ASSIGNMENT" for row in rows
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
