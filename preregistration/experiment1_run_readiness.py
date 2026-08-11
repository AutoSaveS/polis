#!/usr/bin/env python3
"""Audit technical readiness for the formal Experiment 1 execution.

This is intentionally not a preregistration, ethics, personnel-qualification,
or confirmatory-analysis gate.  It checks whether the 36-scenario/four-workflow
design-production and spatial-evaluation pipeline can execute end to end.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from preregistration.software.rhino_geopackage_export import (  # noqa: E402
    REQUIRED_LAYERS,
    validate_frame,
)

PREREG = ROOT / "preregistration"
WORLD = ROOT / "world_model"
OUTPUT = PREREG / "experiment1_run_readiness.json"
RHINO_INVENTORY = PREREG / "software/rhino_workstation_assets.json"
RHINO_SCHEMA = PREREG / "software/rhino_export_contract.schema.json"
DRY_RUN_DIR = PREREG / "software/rhino_dry_run"
DRY_RUN_RECORD = DRY_RUN_DIR / "rhino_export_record.json"
DRY_RUN_DESIGN = DRY_RUN_DIR / "dry_run_design.gpkg"
REQUIRED_RHINO_ASSETS = {
    "POLIS_vegetation_v1.gh", "POLIS_vegetation_v1.ghx",
    "POLIS_hardscape_v1.gh", "POLIS_hardscape_v1.ghx",
    "POLIS_hydrology_v1.gh", "POLIS_hydrology_v1.ghx",
    "POLIS_furniture_v1.gh", "POLIS_furniture_v1.ghx",
    "POLIS_activity_v1.gh", "POLIS_activity_v1.ghx",
    "POLIS_ecology_v1.gh", "POLIS_ecology_v1.ghx",
    "POLIS_workstation_master_v1.3dm",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_assets(patterns: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        found.extend(str(path.relative_to(ROOT)) for path in ROOT.rglob(pattern))
    return sorted(found)


def run_check(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def validate_rhino_inventory() -> tuple[bool, str]:
    if not RHINO_INVENTORY.is_file():
        return False, "rhino_workstation_assets.json has not been returned"
    try:
        record = json.loads(RHINO_INVENTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, "invalid Rhino inventory: {}".format(exc)
    if record.get("status") != "VERIFIED_ON_FIXED_WORKSTATION":
        return False, "Rhino inventory is not workstation-verified"
    assets = record.get("source_assets", [])
    observed = {Path(str(item.get("relative_path", ""))).name for item in assets}
    missing = sorted(REQUIRED_RHINO_ASSETS - observed)
    if missing:
        return False, "missing Rhino inventory assets: {}".format(", ".join(missing))
    invalid_hashes = [
        str(item.get("relative_path", "")) for item in assets
        if Path(str(item.get("relative_path", ""))).name in REQUIRED_RHINO_ASSETS
        and not SHA256_PATTERN.fullmatch(str(item.get("sha256", "")))
    ]
    if invalid_hashes:
        return False, "invalid Rhino asset hashes: {}".format(", ".join(invalid_hashes))
    mismatched_files = []
    missing_files = []
    for item in assets:
        name = Path(str(item.get("relative_path", ""))).name
        if name not in REQUIRED_RHINO_ASSETS:
            continue
        path = DRY_RUN_DIR / name
        if not path.is_file():
            missing_files.append(name)
        elif sha256(path) != str(item.get("sha256", "")):
            mismatched_files.append(name)
    if missing_files:
        return False, "recorded Rhino assets are absent from returned dry-run folder: {}".format(", ".join(sorted(missing_files)))
    if mismatched_files:
        return False, "returned Rhino asset hashes differ from inventory: {}".format(", ".join(sorted(mismatched_files)))
    return True, "13 returned Rhino/Grasshopper assets exist and match their recorded SHA-256"


def validate_dry_run_handoff() -> tuple[bool, str]:
    if not DRY_RUN_RECORD.is_file() or not DRY_RUN_DESIGN.is_file():
        return False, "dry-run record and GeoPackage have not both been returned"
    try:
        import jsonschema

        record = json.loads(DRY_RUN_RECORD.read_text(encoding="utf-8"))
        schema = json.loads(RHINO_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(record)
    except (OSError, json.JSONDecodeError, Exception) as exc:
        return False, "invalid dry-run handoff: {}".format(exc)
    if not str(record.get("run_id", "")).startswith("DRYRUN-"):
        return False, "dry-run record must use a DRYRUN- run_id"
    if record.get("status") != "exported":
        return False, "dry-run handoff status is not exported"
    if record.get("design_geopackage", {}).get("sha256") != sha256(DRY_RUN_DESIGN):
        return False, "dry-run GeoPackage SHA-256 does not match the handoff"
    for item in record.get("source_files", []):
        source_path = DRY_RUN_DIR / Path(str(item.get("path", ""))).name
        if not source_path.is_file():
            return False, "dry-run source file is absent: {}".format(source_path.name)
        if sha256(source_path) != str(item.get("sha256", "")):
            return False, "dry-run source hash mismatch: {}".format(source_path.name)
    try:
        import geopandas as gpd
        from pyogrio import list_layers
        from shapely.geometry import MultiPoint, box
        from shapely.ops import unary_union

        observed = {str(row[0]) for row in list_layers(DRY_RUN_DESIGN)}
        missing = sorted(set(REQUIRED_LAYERS) - observed)
        if missing:
            return False, "dry-run GeoPackage is missing layers: {}".format(", ".join(missing))
        analysis_crs = str(record.get("analysis_crs", ""))
        frames = {}
        for layer in REQUIRED_LAYERS:
            frame = gpd.read_file(DRY_RUN_DESIGN, layer=layer)
            validate_frame(frame, layer, analysis_crs)
            if frame.empty:
                return False, "dry-run layer is empty: {}".format(layer)
            frames[layer] = frame

        network = frames["accessible_network"]
        network_union = unary_union(network.geometry)
        node_coordinates = []
        for geometry in network.geometry:
            parts = list(geometry.geoms) if geometry.geom_type == "MultiLineString" else [geometry]
            for line in parts:
                node_coordinates.extend((line.coords[0], line.coords[-1]))
        network_nodes = MultiPoint(node_coordinates)
        tolerance_m = 1e-6
        for layer in ("green_entrances", "required_destinations"):
            if any(point.distance(network_nodes) > tolerance_m for point in frames[layer].geometry):
                return False, "{} contains a point that is not on a network node".format(layer)

        destinations = frames["required_destinations"]
        turning_spaces = frames["turning_spaces"]
        destination_ids = set(destinations["required_destination_id"].astype(str))
        turning_ids = set(turning_spaces["required_destination_id"].astype(str))
        if destination_ids != turning_ids:
            return False, "turning-space destination IDs do not match required destinations"
        for destination in destinations.itertuples():
            candidates = turning_spaces[
                turning_spaces["required_destination_id"].astype(str)
                == str(destination.required_destination_id)
            ]
            if not any(geometry.covers(destination.geometry) for geometry in candidates.geometry):
                return False, "required destination is not covered by its turning space: {}".format(
                    destination.required_destination_id
                )
        for geometry in turning_spaces.geometry:
            min_x, min_y, max_x, max_y = geometry.bounds
            clear_diameter = min(max_x - min_x, max_y - min_y)
            circularity = 4.0 * math.pi * geometry.area / (geometry.length ** 2)
            if clear_diameter < 1.525 - tolerance_m or circularity < 0.98:
                return False, "turning space does not preserve the 1.525 m circular clear-space rule"

        usable_union = unary_union(frames["usable_spaces"].geometry)
        if any(space.distance(network_union) > tolerance_m for space in frames["usable_spaces"].geometry):
            return False, "usable space is disconnected from the accessible network"
        if any(footprint.distance(usable_union) > tolerance_m for footprint in frames["shade_footprints"].geometry):
            return False, "shade footprint is disconnected from usable space"

        schedule = csv_rows(WORLD / "metadata/solar_evaluation_schedule.csv")
        expected_times = {
            (row["month_day"], row["local_solar_time"])
            for row in schedule if row.get("site_id") == "SUZ"
        }
        observed_times = [
            (str(row.month_day).strip(), str(row.local_solar_time).strip())
            for row in frames["shade_footprints"].itertuples()
        ]
        if len(observed_times) != len(expected_times) or set(observed_times) != expected_times:
            return False, "shade footprints do not match the frozen 12-time Suzhou schedule"

        site = gpd.read_file(WORLD / "vector/suz_world_model.gpkg", layer="site_geometry")
        if str(site.crs).upper() != analysis_crs.upper():
            site = site.to_crs(analysis_crs)
        accepted_extent = box(*site.total_bounds)
        for layer, frame in frames.items():
            if not accepted_extent.covers(unary_union(frame.geometry)):
                return False, "{} lies outside the registered Suzhou coordinate envelope".format(layer)
    except Exception as exc:
        return False, "dry-run GeoPackage fails the spatial layer contract: {}".format(exc)
    return True, (
        "dry-run handoff schema and hashes are valid; all seven non-empty layers pass geometry, "
        "field, schedule, 1.525 m turning-space, Suzhou extent, and connectivity checks"
    )


def main() -> int:
    world_report = json.loads(
        (WORLD / "validation/world_model_validation.json").read_text(encoding="utf-8")
    )
    scenarios = csv_rows(PREREG / "scenarios.csv")
    run_manifest = csv_rows(PREREG / "experiment1_run_manifest.csv")
    operators = csv_rows(PREREG / "protocols/operator_roles.csv")
    assignments = csv_rows(PREREG / "protocols/operator_assignment_plan.csv")
    api_result = json.loads(
        (PREREG / "software/api_preflight_result.json").read_text(encoding="utf-8")
    )

    scenario_package_builder = PREREG / "prepare_experiment1_scenario_packages.py"
    scenario_package_dir = PREREG / "experiment1_scenario_packages"
    scenario_packages = sorted(scenario_package_dir.glob("*.json")) if scenario_package_dir.is_dir() else []
    evaluation_runner = PREREG / "experiment1_runner.py"
    evaluator = PREREG / "analysis/experiment1_evaluator.py"
    workflow_runner = PREREG / "polis_workflow_runner.py"
    existing_builder = PREREG / "prepare_existing_condition_designs.py"
    geopackage_exporter = PREREG / "software/rhino_geopackage_export.py"
    feedback_functions = PREREG / "analysis/polis_feedback_functions.py"
    generator_dir = PREREG / "software/rhino_generators"
    generator_contract_test = generator_dir / "test_generator_contract.py"
    generator_simulation_test = generator_dir / "test_generator_simulation.py"

    python_runtime_ok = sys.version_info[:3] == (3, 9, 7)
    required_modules = ("geopandas", "jsonschema", "networkx", "openai", "ortools", "osmnx")
    module_check = run_check(
        [sys.executable, "-c", "; ".join("import {}".format(name) for name in required_modules)]
    )
    generator_contract_result = run_check([sys.executable, str(generator_contract_test)])
    generator_simulation_result = run_check([sys.executable, str(generator_simulation_test)])
    polis_workflow_test = run_check(
        [sys.executable, str(PREREG / "analysis/test_polis_feedback_and_workflow.py")]
    )
    inventory_ok, inventory_note = validate_rhino_inventory()
    dry_run_ok, dry_run_note = validate_dry_run_handoff()

    execution_gates = {
        "world_model_computationally_ready": bool(world_report.get("experiment_1_ready")),
        "thirty_six_scenarios_available": len(scenarios) == 36,
        "scenario_package_builder_present": scenario_package_builder.is_file(),
        "all_36_scenario_packages_materialized": len(scenario_packages) == 36,
        "run_manifest_has_144_rows": len(run_manifest) == 144,
        "local_python_3_9_7_runtime": python_runtime_ok,
        "local_required_python_packages_importable": bool(module_check["passed"]),
        "six_generator_source_contract_passed": bool(generator_contract_result["passed"]),
        "six_generator_geometry_simulation_passed": bool(generator_simulation_result["passed"]),
        "cross_device_rhino_export_contract_present": RHINO_SCHEMA.is_file(),
        "external_rhino_workstation_assets_verified": inventory_ok,
        "external_rhino_dry_run_handoff_valid": dry_run_ok,
        "rhino_to_geopackage_exporter_present": geopackage_exporter.is_file(),
        "existing_condition_design_builder_present": existing_builder.is_file(),
        "polis_workflow_orchestration_runner_present": workflow_runner.is_file() and bool(polis_workflow_test["passed"]),
        "six_local_feedback_functions_present": feedback_functions.is_file() and bool(polis_workflow_test["passed"]),
        "five_outcome_spatial_evaluator_present": evaluator.is_file(),
        "experiment1_evaluation_runner_present": evaluation_runner.is_file(),
        "live_terra_four_schema_preflight_passed": api_result.get("status")
        == "PASSED_LIVE_SCHEMAS_AND_LOCAL_REFUSAL_HANDLER",
        "terra_api_key_available_at_runtime": bool(os.environ.get("OPENAI_API_KEY")),
    }
    blockers = [name for name, passed in execution_gates.items() if not passed]

    active_assignments = [row for row in assignments if row.get("workflow") in {"CONVENTIONAL", "DIGITAL", "POLIS"}]
    assigned_count = sum(bool(row.get("real_operator_id")) for row in active_assignments)
    operational_status = {
        "recorded_operator_count": len(operators),
        "active_assignment_rows": len(active_assignments),
        "active_assignments_with_operator_id": assigned_count,
        "operator_note": (
            "Operator documentation is reported for scheduling and reproducibility but is not a technical execution gate."
        ),
        "api_project_data_controls_recorded": (
            PREREG / "software/api_project_data_controls_record.md"
        ).is_file(),
        "api_governance_note": (
            "The data-controls record is nonblocking here, but applicable organisational and API policies still apply to live calls."
        ),
    }

    development_prerequisites = (
        "world_model_computationally_ready",
        "thirty_six_scenarios_available",
        "scenario_package_builder_present",
        "all_36_scenario_packages_materialized",
        "local_python_3_9_7_runtime",
        "local_required_python_packages_importable",
        "six_generator_source_contract_passed",
        "six_generator_geometry_simulation_passed",
        "cross_device_rhino_export_contract_present",
        "five_outcome_spatial_evaluator_present",
    )
    parallel_development_ready = all(execution_gates[name] for name in development_prerequisites)
    report = {
        "status": (
            "READY_FOR_FORMAL_EXPERIMENT_1_EXECUTION"
            if not blockers else "NOT_READY_FOR_FORMAL_EXPERIMENT_1_EXECUTION"
        ),
        "scope_note": (
            "Technical execution gate for 36 scenarios and four workflows. It excludes preregistration freeze, ethics, "
            "author/PI threshold signatures, personnel qualification, R analysis, and registry receipt requirements."
        ),
        "parallel_development_ready": parallel_development_ready,
        "parallel_development_note": (
            "Cross-device Rhino-to-GeoPackage integration validation is complete; formal execution readiness now depends "
            "only on the remaining execution gates."
            if dry_run_ok else
            "GeoPackage export, Existing-condition construction, and POLIS orchestration can be developed now against "
            "the frozen contracts; a valid Rhino dry run is still required for cross-device integration validation."
        ),
        "execution_gates": execution_gates,
        "blocking_items": blockers,
        "operational_status_nonblocking": operational_status,
        "excluded_from_execution_gate": [
            "author_and_pi_threshold_attestation",
            "immutable_preregistration_receipt",
            "R_4_3_runtime_and_renv_lock",
            "expert_or_resident_ethics_documents",
            "operator_training_and_PI_verification",
        ],
        "observed_assets": {
            "project_rhino_binary_assets": find_assets(("*.gh", "*.ghx", "*.3dm")),
            "scenario_package_count": len(scenario_packages),
            "run_manifest_row_count": len(run_manifest),
            "rhino_inventory_note": inventory_note,
            "dry_run_note": dry_run_note,
            "python_executable": sys.executable,
            "python_version": ".".join(str(value) for value in sys.version_info[:3]),
            "module_check": module_check,
            "generator_contract_test": generator_contract_result,
            "generator_simulation_test": generator_simulation_result,
            "polis_workflow_offline_test": polis_workflow_test,
            "openai_api_key_present": bool(os.environ.get("OPENAI_API_KEY")),
        },
        "claim_boundary": (
            "A passing run supports the analytical Experiment 1 workflow only; it does not establish legal compliance, "
            "permission, cost accuracy, or construction readiness."
        ),
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
