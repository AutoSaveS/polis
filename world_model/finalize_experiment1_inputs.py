#!/usr/bin/env python3
"""Apply the frozen analytical policies and audit Experiment 1 readiness."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parent
METADATA = ROOT / "metadata"
VECTOR = ROOT / "vector"
VALIDATION = ROOT / "validation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def freeze_chicago_boundary() -> None:
    gpkg = VECTOR / "chi_world_model.gpkg"
    axis_frame = gpd.read_file(gpkg, layer="site_geometry")
    axis = axis_frame.geometry.iloc[0]
    # Rebuilding the derived grid must be idempotent: preserve any already
    # extracted population values keyed by the stable origin identifier.
    existing_origins = None
    try:
        existing_origins = gpd.read_file(gpkg, layer="analysis_origins")
    except Exception:
        pass
    preserved = {}
    if existing_origins is not None and not existing_origins.empty:
        for row in existing_origins.itertuples(index=False):
            origin_id = getattr(row, "origin_id", None)
            if origin_id is not None:
                preserved[origin_id] = {
                    "population_weight": getattr(row, "population_weight", np.nan),
                    "population_source_id": getattr(row, "population_source_id", None),
                    "weight_status": getattr(row, "weight_status", None),
                }
    boundary = axis.buffer(20.0)
    gpd.GeoDataFrame(
        [{
            "site_id": "CHI",
            "derivation": "registered_manuscript_20m_envelope_around_frozen_osm_axis",
            "source_osm_id": "624189839",
            "boundary_status": "FROZEN_ANALYTICAL_BOUNDARY_NOT_LEGAL_ROW",
            "buffer_m_each_side": 20.0,
            "geometry": boundary,
        }],
        geometry="geometry",
        crs=axis_frame.crs,
    ).to_file(gpkg, layer="analysis_boundary", driver="GPKG")

    catchment = boundary.buffer(1000.0)
    minx, miny, maxx, maxy = catchment.bounds
    rows = []
    x = math.floor(minx / 100.0) * 100.0 + 50.0
    while x <= maxx:
        y = math.floor(miny / 100.0) * 100.0 + 50.0
        while y <= maxy:
            point = Point(x, y)
            if catchment.contains(point):
                origin_id = f"CHI-ORG-{len(rows) + 1:04d}"
                old = preserved.get(origin_id, {})
                rows.append({
                    "origin_id": origin_id,
                    "site_id": "CHI",
                    "grid_m": 100,
                    "population_weight": old.get("population_weight", np.nan),
                    "population_source_id": old.get("population_source_id"),
                    "weight_status": old.get(
                        "weight_status", "BLOCKED_REAL_POPULATION_EXTRACT_REQUIRED"
                    ),
                    "geometry": point,
                })
            y += 100.0
        x += 100.0
    gpd.GeoDataFrame(rows, geometry="geometry", crs=axis_frame.crs).to_file(
        gpkg, layer="analysis_origins", driver="GPKG"
    )

    registry_path = METADATA / "site_registry.csv"
    registry = pd.read_csv(registry_path)
    mask = registry["site_id"] == "CHI"
    registry.loc[mask, "geometry_role"] = "analytical_boundary_from_registered_axis_envelope"
    registry.loc[mask, "geometry_type"] = "Polygon"
    registry.loc[mask, "area_m2"] = boundary.area
    registry.loc[mask, "axis_length_m"] = axis.length
    registry.loc[mask, "corridor_width_m"] = 40.0
    registry.loc[mask, "corridor_width_status"] = "FROZEN_STUDY_ANALYTICAL_ENVELOPE"
    registry.loc[mask, "gpkg_sha256"] = sha256(gpkg)
    registry.to_csv(registry_path, index=False)


def freeze_resource_register() -> None:
    path = METADATA / "scenario_budget_register.csv"
    frame = pd.read_csv(path)
    frame["base_capital_budget"] = np.nan
    frame["currency"] = "NOT_APPLICABLE_UNIT_LESS_INDEX"
    frame["price_base_date"] = np.nan
    frame["scenario_capital_cap"] = np.nan
    frame["budget_source_id"] = "EXP1-NORMALIZED-RESOURCE-INDEX-V1"
    frame["base_resource_units"] = 100.0
    frame["scenario_resource_cap_units"] = frame["budget_multiplier"] * 100.0
    frame["resource_catalog"] = "metadata/normalized_resource_cost_catalog.csv"
    frame["status"] = "RUNNABLE_NORMALIZED_RESOURCE_CAP_ABSOLUTE_COST_NOT_CLAIMED"
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def freeze_regulatory_scoring() -> None:
    path = METADATA / "regulatory_trigger_register.csv"
    frame = pd.read_csv(path)
    frame["experiment1_scoring_disposition"] = (
        "NOT_EVALUABLE_EXCLUDED_UNTIL_REGISTERED_TRIGGER_EVIDENCE"
    )
    frame["verification_status"] = "PROJECT_APPLICABILITY_PENDING_ANALYTICAL_RULE_RETAINED"
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def update_solar_policy() -> None:
    path = METADATA / "solar_evaluation_schedule.csv"
    frame = pd.read_csv(path)
    frame["shadow_input_status"] = "RUNNABLE_EXPLICIT_DESIGN_GEOMETRY_MISSING_BASELINE_HEIGHT_NOT_IMPUTED"
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def update_validation() -> None:
    path = VALIDATION / "world_model_validation.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    computational_phrases = (
        "verified building and tree heights",
        "absolute baseline capital and maintenance budget",
        "project-level regulatory trigger values",
        "author-confirmed Chicago analytical corridor",
    )
    for site in report["sites"]:
        site["blocking_items"] = [
            item for item in site["blocking_items"]
            if not any(phrase in item for phrase in computational_phrases)
        ]
        site["experiment1_policies"] = {
            "shade": "explicit proposed-object geometry; missing baseline height not imputed",
            "resource": "unitless frozen resource index",
            "regulation": "pending triggers are not_evaluable and excluded",
        }
        gpkg = VECTOR / f"{site['site_id'].lower()}_world_model.gpkg"
        origins = gpd.read_file(gpkg, layer="analysis_origins")
        nonmissing = int(origins["population_weight"].notna().sum())
        positive = int((origins["population_weight"].fillna(0) > 0).sum())
        site["layers"]["analysis_origins"] = int(len(origins))
        if "population" in site:
            site["population"]["origin_count"] = int(len(origins))
            site["population"]["nonmissing_origin_count"] = nonmissing
            site["population"]["positive_origin_count"] = positive
            site["population"]["population_sum_at_origins"] = float(
                origins["population_weight"].fillna(0).sum()
            )
        if nonmissing != len(origins) or positive == 0:
            site["blocking_items"].append(
                "Real population weights are incomplete or contain no positive values."
            )
        if site["site_id"] == "CHI":
            site["geometry"] = {
                "type": "Polygon",
                "area_m2": float(pd.read_csv(METADATA / "site_registry.csv").loc[
                    lambda x: x["site_id"] == "CHI", "area_m2"
                ].iloc[0]),
                "axis_length_m": float(pd.read_csv(METADATA / "site_registry.csv").loc[
                    lambda x: x["site_id"] == "CHI", "axis_length_m"
                ].iloc[0]),
                "buffer_m_each_side": 20.0,
            }
    report["global_blocking_items"] = [
        item for item in report["global_blocking_items"]
        if not any(phrase in item for phrase in (
            "shade object heights",
            "Chicago corridor",
            "absolute budgets",
            "project-level regulatory applicability",
        ))
    ]
    population_blocked_sites = [
        site["site_id"] for site in report["sites"]
        if any("population weights" in item for item in site["blocking_items"])
    ]
    if population_blocked_sites:
        report["global_blocking_items"].append(
            "Real population weights are incomplete for: " + ", ".join(population_blocked_sites)
        )
    report["engineering_implementation_ready"] = False
    report["implementation_limitations"] = [
        "Existing object heights are incomplete; Experiment 1 uses the frozen comparative shade policy.",
        "The resource cap is a unitless study index, not an absolute capital or maintenance budget.",
        "The Chicago polygon is an analytical envelope, not a legal parcel or right-of-way.",
        "Project-level regulatory and permit applicability remains pending and cannot support a compliance claim.",
    ]
    report["experiment_1_ready"] = len(report["global_blocking_items"]) == 0
    report["status"] = (
        "EXPERIMENT_1_COMPUTATIONALLY_READY_WITH_REGISTERED_LIMITATIONS"
        if report["experiment_1_ready"]
        else "EXPERIMENT_1_BLOCKED_BY_REMAINING_INPUTS"
    )
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii")


def update_manifest() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path.name in {"manifest.sha256", ".DS_Store"}
            or "__pycache__" in path.parts
        ):
            continue
        rows.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    (METADATA / "manifest.sha256").write_text("\n".join(rows) + "\n", encoding="ascii")


def main() -> None:
    freeze_chicago_boundary()
    freeze_resource_register()
    freeze_regulatory_scoring()
    update_solar_policy()
    update_validation()
    update_manifest()


if __name__ == "__main__":
    main()
