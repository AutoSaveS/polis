#!/usr/bin/env python3
"""Create row-level evidence for the Suzhou image-derived Existing proxy runs.

The outputs are analytical disposition records, not field observations.  The
script uses only the frozen evaluator predicates and conservative fail rules
for needs whose required evidence is absent (native planting, rest furniture,
maintenance plan, and group-level preference data).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from preregistration.analysis import experiment1_evaluator as evaluator


WORLD = ROOT / "world_model/vector/suz_world_model.gpkg"
REGISTER = ROOT / "preregistration/constraints/site_constraints.csv"
REGULATORY_REGISTER = ROOT / "world_model/metadata/regulatory_trigger_register.csv"
SUZHOU_RULE_CONFIRMATION = ROOT / "world_model/metadata/suzhou_nine_rule_confirmation.csv"


def status(pass_value: bool, reference: str, **details: Any) -> Dict[str, Any]:
    return {
        "status": "pass" if pass_value else "fail",
        "evidence_reference": reference,
        **details,
    }


def write_csv(path: Path, id_column: str, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[id_column, "status", "evidence_reference"])
        writer.writeheader()
        writer.writerows(rows)


def build(design_path: Path, variant: str, output_dir: Path) -> Dict[str, Any]:
    design_path = design_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    network = gpd.read_file(design_path, layer="accessible_network")
    entrances = gpd.read_file(design_path, layer="green_entrances")
    destinations = gpd.read_file(design_path, layer="required_destinations")
    turning = gpd.read_file(design_path, layer="turning_spaces")
    usable = gpd.read_file(design_path, layer="usable_spaces")
    shade = gpd.read_file(design_path, layer="shade_footprints")
    objects = gpd.read_file(design_path, layer="design_objects")
    boundary = gpd.read_file(WORLD, layer="site_geometry").geometry.iloc[0]

    checks = evaluator.network_and_geometry_checks(network, destinations, turning)
    integrity = evaluator.object_integrity_checks(objects, destinations, turning)
    checks_by_id = {item["constraint_id"]: item for item in checks + integrity}
    comfort = evaluator.shade_comfort(usable, shade)
    resource = evaluator.resource_check("SUZ-GE-B", objects, boundary)

    evidence_name = f"suzhou_existing_{variant}_proxy_evidence.json"
    evidence_path = output_dir / evidence_name
    evidence_ref = str(evidence_path.relative_to(ROOT))

    n01_pass = bool(checks_by_id["disconnected_accessible_routes"].get("passed"))
    n02_pass = all(
        bool(checks_by_id[key].get("passed"))
        for key in (
            "accessible_route_clear_width",
            "accessible_route_running_slope",
            "accessible_route_cross_slope",
        )
    )
    n03_pass = comfort.get("status") == "evaluated" and float(comfort.get("value", 0.0)) >= 0.60

    # The proxy package contains no rest furniture, obstruction inventory, or
    # species/planting provenance.  These are pre-specified conservative fails.
    n04_pass = False
    n05_pass = False

    activity = objects[objects["resource_class"].astype(str) == "activity"]
    path_surface = unary_union(list(network.geometry.buffer(
        pd.to_numeric(network["clear_width_m"], errors="coerce") / 2.0
    )))
    activity_area = float(unary_union(list(activity.geometry)).area) if not activity.empty else 0.0
    activity_surface_distance = (
        float(unary_union(list(activity.geometry)).distance(path_surface)) if not activity.empty else None
    )
    n06_pass = bool(
        activity_area >= 100.0
        and activity_surface_distance is not None
        and activity_surface_distance <= 1e-6
    )
    n07_pass = False

    vulnerable_ids = ["SUZ-N01", "SUZ-N02", "SUZ-N04"]
    vulnerable_statuses = {
        "SUZ-N01": n01_pass,
        "SUZ-N02": n02_pass,
        "SUZ-N04": n04_pass,
    }
    group_retention = sum(vulnerable_statuses.values()) / len(vulnerable_statuses)
    n08_pass = bool(
        checks_by_id["wheelchair_turning_diameter"].get("passed")
        and group_retention >= 0.75
    )

    needs = {
        "SUZ-N01": status(n01_pass, f"{evidence_ref}#need-SUZ-N01", predicate="disconnected_accessible_routes == 0"),
        "SUZ-N02": status(n02_pass, f"{evidence_ref}#need-SUZ-N02", predicate="clear_width >= 1.50; running_slope <= 0.05; cross_slope <= 0.02"),
        "SUZ-N03": status(n03_pass, f"{evidence_ref}#need-SUZ-N03", predicate="weighted_effective_shade_fraction >= 0.60", observed_value=comfort.get("value")),
        "SUZ-N04": status(False, f"{evidence_ref}#need-SUZ-N04", predicate="rest_interval <= 50 m and obstruction_count == 0", reason="No rest-furniture or obstruction inventory is present in the image proxy."),
        "SUZ-N05": status(False, f"{evidence_ref}#need-SUZ-N05", predicate="native_or_locally_adapted_fraction >= 0.70 and green_fraction >= 0.35", reason="No species or planting-origin evidence is present in the image proxy."),
        "SUZ-N06": status(n06_pass, f"{evidence_ref}#need-SUZ-N06", predicate="accessible_usable_activity_area_m2 >= 100", area_m2=activity_area, distance_to_path_surface_m=activity_surface_distance),
        "SUZ-N07": status(False, f"{evidence_ref}#need-SUZ-N07", predicate="budget_ratio <= 1.00 and maintenance_plan_complete == true", reason="No bill of quantities or maintenance responsibility schedule is present for an Existing baseline."),
        "SUZ-N08": status(n08_pass, f"{evidence_ref}#need-SUZ-N08", predicate="turning_diameter >= 1.525 and vulnerable_group_need_retention >= 0.75", vulnerable_need_ids=";".join(vulnerable_ids), vulnerable_group_need_retention=group_retention),
    }

    need_path = output_dir / "need_results.csv"
    write_csv(need_path, "need_id", [
        {
            "need_id": key,
            "status": value["status"],
            "evidence_reference": value["evidence_reference"],
        }
        for key, value in needs.items()
    ])

    regulatory = pd.read_csv(REGISTER, dtype=str).fillna("")
    regulatory = regulatory[
        (regulatory["site"] == "Suzhou")
        & (regulatory["study_evaluator_applicability"] != "reference_only_not_scored")
    ]
    constraints = []
    for constraint_id in regulatory["constraint_id"].tolist():
        constraints.append({
            "constraint_id": constraint_id,
            "status": "not_evaluable",
            "evidence_reference": f"{SUZHOU_RULE_CONFIRMATION.relative_to(ROOT)}#{constraint_id}",
        })
    conflict_free = all(
        bool(checks_by_id[key].get("passed"))
        for key in ("disconnected_accessible_routes", "cross_domain_overlap_area", "missing_required_provenance_links")
    )
    constraints.append({
        "constraint_id": "unresolved_critical_conflicts",
        "status": "pass" if conflict_free else "fail",
        "evidence_reference": f"{evidence_ref}#unresolved_critical_conflicts",
    })
    constraint_path = output_dir / "constraint_results.csv"
    write_csv(constraint_path, "constraint_id", constraints)

    assumptions = {
        "schema_version": "1.0.0",
        "site": "Suzhou",
        "scenario_id": "SUZ-GE-B",
        "variant": variant,
        "source_class": "image_derived_formal_proxy",
        "observation_status": "not_measured",
        "claim_boundary": "Analytical proxy only; not resident evidence, survey measurement, engineering verification, or legal project applicability.",
        "conservative_rules": {
            "missing_rest_or_obstruction_evidence": "fail",
            "missing_species_or_planting_origin_evidence": "fail",
            "missing_budget_or_maintenance_plan": "fail",
            "missing_group_level_validation": "derive from frozen encoded needs and fail below 0.75",
        },
        "activity_access_rule": "Activity area must be at least 100 m2 and touch the submitted accessible path surface; surface is the noded route buffered by its submitted clear width/2.",
        "regulatory_rule": "SUZ-C01..SUZ-C09 are confirmed for Experiment 1 analytical screening. A row remains not_evaluable when its frozen analytical trigger or design-output evidence is absent; confirmation does not establish real-project legal applicability.",
        "checks": checks_by_id,
        "comfort": comfort,
        "resource": resource,
        "need_dispositions": needs,
        "vulnerable_group_need_retention": group_retention,
        "unresolved_critical_conflicts": {"status": "pass" if conflict_free else "fail", "basis": "No disconnected route, cross-domain overlap, or missing provenance link in this proxy package."},
    }
    evidence_path.write_text(json.dumps(assumptions, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {"variant": variant, "need_results": str(need_path), "constraint_results": str(constraint_path), "evidence": str(evidence_path), "need_count": len(needs), "constraint_count": len(constraints)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--variant", choices=("central", "low", "high"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.design, args.variant, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
