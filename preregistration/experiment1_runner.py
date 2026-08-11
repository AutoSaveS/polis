#!/usr/bin/env python3
"""Run one frozen Experiment 1 evaluation and verify its input provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

from analysis import experiment1_evaluator


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "preregistration"
RUN_MANIFEST = PREREG / "experiment1_run_manifest.csv"
RHINO_SCHEMA = PREREG / "software/rhino_export_contract.schema.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_run(run_id: str) -> dict[str, str]:
    with RUN_MANIFEST.open(newline="", encoding="utf-8") as stream:
        matches = [row for row in csv.DictReader(stream) if row["run_id"] == run_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one frozen run row for {run_id}, found {len(matches)}")
    return matches[0]


def validate_handoff(path: Path, design: Path, run_id: str) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(RHINO_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(record)
    if record["run_id"] != run_id:
        raise ValueError("Rhino handoff run_id does not match requested run")
    if record["status"] != "exported":
        raise ValueError("Rhino handoff status is not exported")
    if record["design_geopackage"]["sha256"] != sha256(design):
        raise ValueError("Design GeoPackage SHA-256 does not match Rhino handoff")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--rhino-export-record", required=True, type=Path)
    parser.add_argument("--need-results", required=True, type=Path)
    parser.add_argument("--constraint-results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    run = read_run(args.run_id)
    assignment_note = ""
    if run["workflow"] != "EXISTING" and run["operator_assignment_ready"] != "yes":
        assignment_note = (
            "operator_assignment_ready is not yes; continuing because personnel/PI verification "
            "is tracked outside this technical execution runner"
        )
    world_model = ROOT / run["world_model_file"]
    if sha256(world_model) != run["world_model_sha256"]:
        raise ValueError("Frozen world-model SHA-256 mismatch")
    handoff = validate_handoff(args.rhino_export_record, args.design, args.run_id)
    evaluator_args = argparse.Namespace(
        scenario_id=run["scenario_id"], workflow=run["workflow"], design=args.design,
        world_model=world_model, need_results=args.need_results,
        constraint_results=args.constraint_results, output=args.output,
    )
    result = experiment1_evaluator.evaluate(evaluator_args)
    result.update({
        "run_id": args.run_id,
        "operator_id": handoff["operator_id"],
        "world_model_sha256": run["world_model_sha256"],
        "design_geopackage_sha256": sha256(args.design),
        "rhino_export_record": str(args.rhino_export_record),
        "rhino_workstation_id": handoff["workstation_id"],
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "operational_note": assignment_note,
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(args.output), "all_five_evaluated": result["all_five_evaluated"]}, indent=2))
    return 0 if result["all_five_evaluated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
