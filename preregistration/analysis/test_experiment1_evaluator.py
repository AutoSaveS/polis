#!/usr/bin/env python3
"""End-to-end synthetic smoke test for all five Experiment 1 outcomes."""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, box

import experiment1_evaluator as evaluator


def write_status(path: Path, id_column: str, identifiers: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[id_column, "status", "evidence_reference"])
        writer.writeheader()
        for identifier in identifiers:
            writer.writerow({id_column: identifier, "status": "pass", "evidence_reference": "SYNTHETIC-SMOKE"})


def make_design(path: Path) -> None:
    world = evaluator.SITE_FILES["Suzhou"]
    origins = gpd.read_file(world, layer="analysis_origins")
    boundary = gpd.read_file(world, layer="site_geometry").geometry.iloc[0]
    centre = boundary.centroid
    network = gpd.GeoDataFrame(
        {
            "route_id": [f"R{i:04d}" for i in range(len(origins))],
            "clear_width_m": [1.8] * len(origins),
            "running_slope": [0.01] * len(origins),
            "cross_slope": [0.01] * len(origins),
        },
        geometry=[LineString([point, centre]) for point in origins.geometry],
        crs=origins.crs,
    )
    network.to_file(path, layer="accessible_network", driver="GPKG")
    provenance = "SYNTHETIC-SMOKE"
    gpd.GeoDataFrame({"entrance_id": ["E01"]}, geometry=[centre], crs=origins.crs).to_file(
        path, layer="green_entrances", driver="GPKG"
    )
    gpd.GeoDataFrame(
        {"required_destination_id": ["D01"], "provenance_reference": [provenance]},
        geometry=[centre], crs=origins.crs,
    ).to_file(path, layer="required_destinations", driver="GPKG")
    gpd.GeoDataFrame(
        {"required_destination_id": ["D01"], "provenance_reference": [provenance]},
        geometry=[centre.buffer(0.80)], crs=origins.crs,
    ).to_file(path, layer="turning_spaces", driver="GPKG")
    minx, miny, maxx, maxy = boundary.bounds
    usable_geometry = box(minx, miny, maxx, maxy).intersection(boundary)
    gpd.GeoDataFrame({"space_id": ["U01"]}, geometry=[usable_geometry], crs=origins.crs).to_file(
        path, layer="usable_spaces", driver="GPKG"
    )
    shade_geometry = box(minx, miny, minx + 0.6 * (maxx - minx), maxy).intersection(usable_geometry)
    shade_rows = []
    shade_geometries = []
    for date in sorted(evaluator.DATES):
        for time in evaluator.TIME_WEIGHTS:
            shade_rows.append({"month_day": date, "local_solar_time": time, "geometry_source": "SYNTHETIC"})
            shade_geometries.append(shade_geometry)
    gpd.GeoDataFrame(shade_rows, geometry=shade_geometries, crs=origins.crs).to_file(
        path, layer="shade_footprints", driver="GPKG"
    )
    object_geometry = box(minx, miny, minx + 0.1 * (maxx - minx), miny + 0.1 * (maxy - miny)).intersection(boundary)
    gpd.GeoDataFrame(
        {
            "object_id": ["O01"],
            "resource_class": ["vegetation"],
            "design_domain": ["vegetation"],
            "provenance_reference": [provenance],
        },
        geometry=[object_geometry],
        crs=origins.crs,
    ).to_file(path, layer="design_objects", driver="GPKG")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="polis-exp1-evaluator-") as temporary:
        temporary_path = Path(temporary)
        design = temporary_path / "synthetic_design.gpkg"
        needs_path = temporary_path / "need_results.csv"
        constraints_path = temporary_path / "constraint_results.csv"
        output = temporary_path / "outcomes.json"
        make_design(design)
        needs = pd.read_csv(evaluator.PREREG / "inputs/need_profiles.csv", dtype=str)
        identifiers = needs[needs["scenario_applicability"] == "SUZ-ALL"]["need_id"].tolist()
        write_status(needs_path, "need_id", identifiers)
        constraints = pd.read_csv(evaluator.PREREG / "constraints/site_constraints.csv", dtype=str).fillna("")
        constraint_ids = constraints[
            (constraints["site"] == "Suzhou")
            & (constraints["study_evaluator_applicability"] != "reference_only_not_scored")
        ]["constraint_id"].tolist()
        write_status(constraints_path, "constraint_id", constraint_ids + ["unresolved_critical_conflicts"])
        args = argparse.Namespace(
            scenario_id="SUZ-GE-B",
            workflow="POLIS",
            design=design,
            world_model=None,
            need_results=needs_path,
            constraint_results=constraints_path,
            output=output,
        )
        result = evaluator.evaluate(args)
        assert result["all_five_evaluated"] is True, result
        for name, item in result["outcomes"].items():
            assert item["status"] == "evaluated", (name, item)
            assert 0.0 <= item["value"] <= 1.0, (name, item)
        network = gpd.read_file(design, layer="accessible_network")
        destinations = gpd.read_file(design, layer="required_destinations")
        turning_spaces = gpd.read_file(design, layer="turning_spaces")
        objects = gpd.read_file(design, layer="design_objects")
        boundary = gpd.read_file(evaluator.SITE_FILES["Suzhou"], layer="site_geometry").geometry.iloc[0]
        evidence = evaluator.read_status_csv(constraints_path, "constraint_id")
        missing_turning = evaluator.implementation_feasibility(
            "SUZ-GE-B", "Suzhou", evidence, network, destinations, None, objects, boundary
        )
        assert missing_turning["status"] == "not_evaluable", missing_turning
        missing_regulatory_rows = evaluator.implementation_feasibility(
            "SUZ-GE-B", "Suzhou", None, network, destinations, turning_spaces, objects, boundary
        )
        assert missing_regulatory_rows["status"] == "not_evaluable", missing_regulatory_rows
        failed_network = network.copy()
        failed_network["clear_width_m"] = 1.0
        hard_failure = evaluator.implementation_feasibility(
            "SUZ-GE-B", "Suzhou", evidence, failed_network, destinations, turning_spaces, objects, boundary
        )
        assert hard_failure["value"] == 0.0, hard_failure
        assert hard_failure["hard_gate"] == 0.0, hard_failure
        assert hard_failure["all_hard_constraints_passed"] is False, hard_failure
        print({name: round(item["value"], 6) for name, item in result["outcomes"].items()})


if __name__ == "__main__":
    main()
