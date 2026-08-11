#!/usr/bin/env python3
"""Materialise the 36 frozen, non-participant Experiment 1 scenario packages."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "preregistration"
WORLD = ROOT / "world_model"
OUTPUT = PREREG / "experiment1_scenario_packages"
WORLD_FILES = {
    "Suzhou": WORLD / "vector/suz_world_model.gpkg",
    "London": WORLD / "vector/lon_world_model.gpkg",
    "Chicago": WORLD / "vector/chi_world_model.gpkg",
}


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (PREREG / relative_path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def main() -> None:
    scenarios = read_csv("scenarios.csv")
    needs = read_csv("inputs/need_profiles.csv")
    predicates = read_csv("inputs/need_predicates.csv")
    constraints = read_csv("constraints/site_constraints.csv")
    budgets = {row["scenario_id"]: row for row in read_csv("../world_model/metadata/scenario_budget_register.csv")}
    sources = {row["source_id"]: row for row in read_csv("inputs/source_inventory.csv")}
    predicate_by_id = {row["predicate_id"]: row for row in predicates}
    OUTPUT.mkdir(parents=True, exist_ok=True)

    expected_paths: set[Path] = set()
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        code = scenario_id.split("-", 1)[0]
        selected_needs = [
            row for row in needs
            if row["site"] == scenario["site"]
            and (
                row["scenario_applicability"] == f"{code}-ALL"
                or (scenario_id.endswith("-S") and row["scenario_applicability"] == scenario_id)
            )
        ]
        if len(selected_needs) != int(scenario["need_count"]):
            raise RuntimeError(f"{scenario_id}: expected {scenario['need_count']} needs, found {len(selected_needs)}")
        need_rows = []
        source_ids = set()
        for need in selected_needs:
            predicate = predicate_by_id.get(need["satisfaction_predicate_id"])
            if predicate is None:
                raise RuntimeError(f"{scenario_id}: missing predicate {need['satisfaction_predicate_id']}")
            source_ids.add(need["source_id"])
            need_rows.append({"need": need, "predicate": predicate})
        world_file = WORLD_FILES[scenario["site"]]
        package: dict[str, Any] = {
            "schema_version": "1.0.0",
            "scenario": scenario,
            "world_model": {
                "relative_path": world_file.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(world_file),
            },
            "needs": need_rows,
            "site_constraint_register": [row for row in constraints if row["site"] == scenario["site"]],
            "scenario_resource_register": budgets[scenario_id],
            "sources": [sources[source_id] for source_id in sorted(source_ids) if source_id in sources],
            "protocol_files": {
                "parameters_yaml_sha256": sha256_file(PREREG / "parameters.yaml"),
                "baseline_sops_sha256": sha256_file(PREREG / "baseline_SOPs.md"),
            },
            "data_boundary": {
                "participant_data_included": False,
                "rule": "Only frozen public-source and study-defined analytical inputs are included.",
            },
        }
        package["input_hash"] = hashlib.sha256(canonical_json(package).encode("utf-8")).hexdigest()
        path = OUTPUT / f"{scenario_id}.json"
        path.write_text(json.dumps(package, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
        expected_paths.add(path)

    stale = [path for path in OUTPUT.glob("*.json") if path not in expected_paths]
    if stale:
        raise RuntimeError(f"Refusing to retain stale scenario packages: {[path.name for path in stale]}")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "packages": len(expected_paths)}, indent=2))


if __name__ == "__main__":
    main()
