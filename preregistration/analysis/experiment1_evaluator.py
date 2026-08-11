#!/usr/bin/env python3
"""Compute the five registered POLIS Experiment 1 outcomes.

The evaluator consumes a frozen world-model GeoPackage and a design GeoPackage.
It does not invent missing geometry, heights, predicate results, or regulatory
applicability. Any metric lacking its required evidence is returned as
``not_evaluable`` instead of receiving a guessed score.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from pyogrio import list_layers
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "world_model"
PREREG = ROOT / "preregistration"
SITE_FILES = {
    "Suzhou": WORLD / "vector/suz_world_model.gpkg",
    "London": WORLD / "vector/lon_world_model.gpkg",
    "Chicago": WORLD / "vector/chi_world_model.gpkg",
}
TIME_WEIGHTS = {"10:00": 0.20, "12:00": 0.30, "14:00": 0.30, "16:00": 0.20}
DATES = {"06-21", "07-21", "08-21"}
VALID_STATUSES = {"pass", "fail", "not_evaluable"}
NETWORK_SNAP_TOLERANCE_M = 0.10
TURNING_DIAMETER_M = 1.525
CROSS_DOMAIN_OVERLAP_MAX_M2 = 0.01


class EvidenceError(ValueError):
    """Raised when supplied evidence is malformed rather than merely absent."""


def layers(path: Path) -> set:
    return {str(row[0]) for row in list_layers(path)}


def read_layer(path: Path, layer: str) -> Optional[gpd.GeoDataFrame]:
    if layer not in layers(path):
        return None
    return gpd.read_file(path, layer=layer)


def metric(value: Optional[float], status: str, **details: Any) -> Dict[str, Any]:
    if value is not None and (not math.isfinite(value) or value < -1e-9 or value > 1 + 1e-9):
        raise EvidenceError(f"Metric value outside [0,1]: {value}")
    result: Dict[str, Any] = {"value": None if value is None else float(value), "status": status}
    result.update(details)
    return result


def segment_lines(geometry: Any) -> Iterable[LineString]:
    if isinstance(geometry, LineString):
        yield geometry
    elif isinstance(geometry, MultiLineString):
        yield from geometry.geoms


def node_key(x: float, y: float, precision: int = 3) -> Tuple[float, float]:
    return (round(float(x), precision), round(float(y), precision))


def build_graph(network: gpd.GeoDataFrame) -> Tuple[nx.Graph, List[Tuple[Point, Tuple[float, float]]]]:
    graph = nx.Graph()
    for geometry in network.geometry:
        if geometry is None or geometry.is_empty:
            continue
        for line in segment_lines(geometry):
            coords = list(line.coords)
            for left, right in zip(coords, coords[1:]):
                a = node_key(left[0], left[1])
                b = node_key(right[0], right[1])
                distance = math.dist(a, b)
                if distance <= 0:
                    continue
                if graph.has_edge(a, b):
                    graph[a][b]["length"] = min(graph[a][b]["length"], distance)
                else:
                    graph.add_edge(a, b, length=distance)
    points = [(Point(node), node) for node in graph.nodes]
    return graph, points


def nearest_node(point: Point, nodes: Sequence[Tuple[Point, Tuple[float, float]]]) -> Tuple[float, float]:
    if not nodes:
        raise EvidenceError("Accessible network has no graph nodes")
    return min(nodes, key=lambda item: point.distance(item[0]))[1]


def access_distances(
    origins: gpd.GeoDataFrame,
    network: gpd.GeoDataFrame,
    entrances: gpd.GeoDataFrame,
) -> np.ndarray:
    if origins.crs != network.crs:
        network = network.to_crs(origins.crs)
    if entrances.crs != origins.crs:
        entrances = entrances.to_crs(origins.crs)
    graph, graph_nodes = build_graph(network)
    if not graph_nodes or entrances.empty:
        raise EvidenceError("Access computation requires a nonempty network and entrance layer")
    entrance_nodes = {nearest_node(point, graph_nodes) for point in entrances.geometry}
    route_distance = nx.multi_source_dijkstra_path_length(graph, entrance_nodes, weight="length")
    values: List[float] = []
    for origin in origins.geometry:
        node = nearest_node(origin, graph_nodes)
        connector = origin.distance(Point(node))
        values.append(float(route_distance.get(node, math.inf) + connector))
    return np.asarray(values, dtype=float)


def access_and_equity(
    origins: gpd.GeoDataFrame,
    network: Optional[gpd.GeoDataFrame],
    entrances: Optional[gpd.GeoDataFrame],
) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[np.ndarray]]:
    required = {"population_weight", "origin_id"}
    if network is None or entrances is None or not required.issubset(origins.columns):
        reason = "missing access_network, green_entrances, or population-weight fields"
        return metric(None, "not_evaluable", reason=reason), metric(None, "not_evaluable", reason=reason), None
    weights = pd.to_numeric(origins["population_weight"], errors="coerce").to_numpy(float)
    if np.isnan(weights).any() or (weights < 0).any() or weights.sum() <= 0:
        reason = "population weights must be complete, nonnegative, and have a positive sum"
        return metric(None, "not_evaluable", reason=reason), metric(None, "not_evaluable", reason=reason), None
    try:
        distances = access_distances(origins, network, entrances)
    except EvidenceError as exc:
        return metric(None, "not_evaluable", reason=str(exc)), metric(None, "not_evaluable", reason=str(exc)), None

    population_total = float(weights.sum())
    a_green = float(weights[distances <= 300.0].sum() / population_total)
    access = np.maximum(0.0, 1.0 - distances / 1000.0)
    access[~np.isfinite(access)] = 0.0
    normalised_weights = weights / population_total
    mean_access = float(np.sum(normalised_weights * access))
    positive_weight = normalised_weights[normalised_weights > 0]
    if mean_access == 0:
        equity = 0.0
    elif len(positive_weight) == 1:
        equity = 1.0
    else:
        pairwise = np.abs(access[:, None] - access[None, :])
        weighted_gini = float(
            np.sum(normalised_weights[:, None] * normalised_weights[None, :] * pairwise)
            / (2.0 * mean_access + 1e-9)
        )
        equity = 1.0 - min(1.0, weighted_gini / (1.0 - float(positive_weight.min())))
    common = {
        "origin_count": int(len(origins)),
        "population_total": population_total,
        "finite_distance_count": int(np.isfinite(distances).sum()),
        "distance_method": "shortest path on submitted accessible_network with straight origin connector",
    }
    return (
        metric(a_green, "evaluated", threshold_m=300.0, **common),
        metric(equity, "evaluated", distance_normalisation_m=1000.0, **common),
        distances,
    )


def shade_comfort(
    usable: Optional[gpd.GeoDataFrame], shade: Optional[gpd.GeoDataFrame]
) -> Dict[str, Any]:
    if usable is None or shade is None or usable.empty or shade.empty:
        return metric(None, "not_evaluable", reason="usable_spaces or shade_footprints is absent or empty")
    required = {"month_day", "local_solar_time"}
    if not required.issubset(shade.columns):
        return metric(None, "not_evaluable", reason="shade_footprints lacks month_day/local_solar_time")
    if shade.crs != usable.crs:
        shade = shade.to_crs(usable.crs)
    usable_geometry = unary_union([g for g in usable.geometry if g is not None and not g.is_empty])
    usable_area = float(usable_geometry.area)
    if usable_area <= 0:
        return metric(None, "not_evaluable", reason="usable-space area is zero")
    expected = {(date, time) for date in DATES for time in TIME_WEIGHTS}
    observed = set(zip(shade["month_day"].astype(str), shade["local_solar_time"].astype(str)))
    missing = sorted(expected - observed)
    if missing:
        return metric(None, "not_evaluable", reason="incomplete 12-time shade schedule", missing_times=missing)
    weighted = 0.0
    diagnostics: List[Dict[str, Any]] = []
    for date in sorted(DATES):
        for time, time_weight in TIME_WEIGHTS.items():
            selection = shade[
                (shade["month_day"].astype(str) == date)
                & (shade["local_solar_time"].astype(str) == time)
            ]
            shade_geometry = unary_union([g for g in selection.geometry if g is not None and not g.is_empty])
            fraction = min(1.0, max(0.0, float(usable_geometry.intersection(shade_geometry).area / usable_area)))
            weight = (1.0 / 3.0) * time_weight
            weighted += weight * fraction
            diagnostics.append({"month_day": date, "local_solar_time": time, "shade_fraction": fraction, "weight": weight})
    return metric(
        weighted,
        "evaluated",
        usable_area_m2=usable_area,
        schedule=diagnostics,
        interpretation="comparative design-induced shade proxy; not measured thermal comfort",
    )


def read_status_csv(path: Optional[Path], id_column: str) -> Optional[pd.DataFrame]:
    if path is None or not path.is_file():
        return None
    frame = pd.read_csv(path, dtype=str).fillna("")
    required = {id_column, "status", "evidence_reference"}
    if not required.issubset(frame.columns):
        raise EvidenceError(f"{path.name} lacks required columns: {sorted(required - set(frame.columns))}")
    invalid = set(frame["status"]) - VALID_STATUSES
    if invalid:
        raise EvidenceError(f"{path.name} contains invalid statuses: {sorted(invalid)}")
    if frame[id_column].duplicated().any():
        raise EvidenceError(f"{path.name} contains duplicate {id_column} values")
    if (frame["evidence_reference"].str.strip() == "").any():
        raise EvidenceError(f"{path.name} contains blank evidence_reference values")
    return frame


def need_retention(scenario_id: str, results: Optional[pd.DataFrame]) -> Dict[str, Any]:
    needs = pd.read_csv(PREREG / "inputs/need_profiles.csv", dtype=str).fillna("")
    site_code = scenario_id.split("-")[0]
    city = {"SUZ": "Suzhou", "LON": "London", "CHI": "Chicago"}[site_code]
    base = needs[
        (needs["scenario_applicability"] == f"{site_code}-ALL")
        & (needs["site"] == city)
    ]
    if scenario_id.endswith("-S"):
        additional = needs[needs["scenario_applicability"] == scenario_id]
        expected = pd.concat([base, additional], ignore_index=True)
    else:
        expected = base
    if results is None:
        return metric(None, "not_evaluable", reason="need_results.csv is absent", expected_need_count=int(len(expected)))
    joined = expected[["need_id", "criticality"]].merge(results, on="need_id", how="left")
    missing = joined[joined["status"].isna()]["need_id"].tolist()
    if missing:
        return metric(None, "not_evaluable", reason="missing need-result rows", missing_need_ids=missing)
    unresolved = joined[joined["status"] == "not_evaluable"]["need_id"].tolist()
    if unresolved:
        return metric(
            None,
            "not_evaluable",
            reason="every frozen need must have a pass/fail result",
            not_evaluable_need_ids=unresolved,
        )
    evaluated = joined
    value = float((joined["status"] == "pass").mean())
    critical = joined[joined["criticality"] == "critical"]
    critical_evaluable = critical[critical["status"].isin(["pass", "fail"])]
    critical_retention = None if critical_evaluable.empty else float((critical_evaluable["status"] == "pass").mean())
    return metric(
        value,
        "evaluated",
        expected_count=int(len(joined)),
        evaluated_count=int(len(evaluated)),
        not_evaluable_count=0,
        critical_retention=critical_retention,
        evidence_complete=bool((evaluated["evidence_reference"].str.len() > 0).all()),
    )


def resource_check(scenario_id: str, objects: Optional[gpd.GeoDataFrame], boundary: Any) -> Dict[str, Any]:
    if objects is None or objects.empty or "resource_class" not in objects.columns:
        return {"status": "not_evaluable", "passed": None, "reason": "design_objects/resource_class absent"}
    catalog = pd.read_csv(WORLD / "metadata/normalized_resource_cost_catalog.csv").set_index("resource_class")
    unknown = sorted(set(objects["resource_class"].astype(str)) - set(catalog.index))
    if unknown:
        raise EvidenceError(f"Unknown resource classes: {unknown}")
    site_area = float(boundary.area)
    if site_area <= 0:
        raise EvidenceError("Analysis boundary area must be positive")
    weighted_fraction = 0.0
    class_areas: Dict[str, float] = {}
    for resource_class, group in objects.groupby(objects["resource_class"].astype(str)):
        area = float(unary_union(list(group.geometry)).intersection(boundary).area)
        class_areas[resource_class] = area
        weighted_fraction += (area / site_area) * float(catalog.loc[resource_class, "resource_weight"])
    denominator = float(catalog["resource_weight"].sum())
    resource_index = 100.0 * weighted_fraction / denominator
    budgets = pd.read_csv(WORLD / "metadata/scenario_budget_register.csv")
    row = budgets[budgets["scenario_id"] == scenario_id]
    if len(row) != 1:
        raise EvidenceError(f"Missing resource cap for {scenario_id}")
    cap = float(row.iloc[0]["scenario_resource_cap_units"])
    return {
        "status": "evaluated",
        "passed": bool(resource_index <= cap + 1e-9),
        "resource_index": resource_index,
        "cap_units": cap,
        "class_area_m2": class_areas,
        "interpretation": "unitless study resource index; not a monetary cost",
    }


def network_and_geometry_checks(
    network: Optional[gpd.GeoDataFrame],
    destinations: Optional[gpd.GeoDataFrame],
    turning_spaces: Optional[gpd.GeoDataFrame],
) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    specifications = (
        ("accessible_route_clear_width", "clear_width_m", lambda x: x >= 1.50, ">=1.50 m"),
        ("accessible_route_running_slope", "running_slope", lambda x: x <= 0.05, "<=0.05"),
        ("accessible_route_cross_slope", "cross_slope", lambda x: x <= 0.02, "<=0.02"),
    )
    for constraint_id, column, predicate, rule in specifications:
        if network is None or column not in network.columns:
            checks.append({"constraint_id": constraint_id, "status": "not_evaluable", "passed": None, "rule": rule})
            continue
        values = pd.to_numeric(network[column], errors="coerce")
        if values.isna().any() or values.empty:
            checks.append({"constraint_id": constraint_id, "status": "not_evaluable", "passed": None, "rule": rule})
        else:
            checks.append({"constraint_id": constraint_id, "status": "evaluated", "passed": bool(values.map(predicate).all()), "rule": rule})

    connectivity = {
        "constraint_id": "disconnected_accessible_routes",
        "status": "not_evaluable",
        "passed": None,
        "rule": "0 disconnected route components and every required destination within 0.10 m of the network",
    }
    if network is not None and destinations is not None and not destinations.empty:
        graph, graph_nodes = build_graph(network)
        if graph_nodes:
            offsets = []
            for point in destinations.geometry:
                nearest_point, _ = min(graph_nodes, key=lambda item: point.distance(item[0]))
                offsets.append(float(point.distance(nearest_point)))
            components = nx.number_connected_components(graph)
            connectivity.update({
                "status": "evaluated",
                "passed": bool(components == 1 and max(offsets) <= NETWORK_SNAP_TOLERANCE_M),
                "network_component_count": int(components),
                "maximum_destination_offset_m": max(offsets),
            })
    checks.append(connectivity)

    turning = {
        "constraint_id": "wheelchair_turning_diameter",
        "status": "not_evaluable",
        "passed": None,
        "rule": ">=1.525 m circular clear space at every required destination",
    }
    destination_fields = {"required_destination_id", "provenance_reference"}
    turning_fields = {"required_destination_id", "provenance_reference"}
    if (
        destinations is not None
        and turning_spaces is not None
        and not destinations.empty
        and destination_fields.issubset(destinations.columns)
        and turning_fields.issubset(turning_spaces.columns)
    ):
        destination_ids = destinations["required_destination_id"].astype(str)
        if destination_ids.duplicated().any() or (destination_ids.str.strip() == "").any():
            raise EvidenceError("required_destinations has blank or duplicate required_destination_id values")
        turning_ids = set(turning_spaces["required_destination_id"].astype(str))
        missing_ids = sorted(set(destination_ids) - turning_ids)
        failures: List[str] = []
        if turning_spaces.crs != destinations.crs:
            turning_spaces = turning_spaces.to_crs(destinations.crs)
        for _, destination in destinations.iterrows():
            destination_id = str(destination["required_destination_id"])
            candidates = turning_spaces[
                turning_spaces["required_destination_id"].astype(str) == destination_id
            ]
            required_circle = destination.geometry.buffer(TURNING_DIAMETER_M / 2.0, resolution=32)
            if candidates.empty or not any(
                required_circle.within(geometry.buffer(1e-6))
                for geometry in candidates.geometry
                if geometry is not None and not geometry.is_empty
            ):
                failures.append(destination_id)
        turning.update({
            "status": "evaluated",
            "passed": not missing_ids and not failures,
            "required_destination_count": int(len(destinations)),
            "missing_turning_space_ids": missing_ids,
            "insufficient_turning_space_ids": failures,
        })
    checks.append(turning)
    return checks


def object_integrity_checks(
    objects: Optional[gpd.GeoDataFrame],
    destinations: Optional[gpd.GeoDataFrame],
    turning_spaces: Optional[gpd.GeoDataFrame],
) -> List[Dict[str, Any]]:
    overlap = {
        "constraint_id": "cross_domain_overlap_area",
        "status": "not_evaluable",
        "passed": None,
        "rule": "<=0.01 m2 across different design domains",
    }
    provenance = {
        "constraint_id": "missing_required_provenance_links",
        "status": "not_evaluable",
        "passed": None,
        "rule": "0 design objects with a missing provenance_reference",
    }
    if objects is None or objects.empty:
        return [overlap, provenance]
    provenance_frames = [objects, destinations, turning_spaces]
    if all(
        frame is not None and "provenance_reference" in frame.columns
        for frame in provenance_frames
    ):
        missing_count = sum(
            int((frame["provenance_reference"].fillna("").astype(str).str.strip() == "").sum())
            for frame in provenance_frames
            if frame is not None
        )
        provenance.update({
            "status": "evaluated",
            "passed": missing_count == 0,
            "missing_count": missing_count,
        })
    if "design_domain" in objects.columns:
        domain_geometries = {
            str(domain): unary_union([g for g in group.geometry if g is not None and not g.is_empty])
            for domain, group in objects.groupby(objects["design_domain"].astype(str))
        }
        domains = sorted(domain_geometries)
        overlap_area = 0.0
        for index, left in enumerate(domains):
            for right in domains[index + 1:]:
                overlap_area += float(domain_geometries[left].intersection(domain_geometries[right]).area)
        overlap.update({
            "status": "evaluated",
            "passed": bool(overlap_area <= CROSS_DOMAIN_OVERLAP_MAX_M2 + 1e-9),
            "observed_overlap_area_m2": overlap_area,
            "design_domain_count": len(domains),
        })
    return [overlap, provenance]


def expected_constraint_ids(city: str) -> set:
    register = pd.read_csv(PREREG / "constraints/site_constraints.csv", dtype=str).fillna("")
    selected = register[
        (register["site"] == city)
        & (register["study_evaluator_applicability"] != "reference_only_not_scored")
    ]
    return set(selected["constraint_id"])


def regulatory_constraint_classes(city: str) -> Dict[str, str]:
    register = pd.read_csv(PREREG / "constraints/site_constraints.csv", dtype=str).fillna("")
    selected = register[
        (register["site"] == city)
        & (register["study_evaluator_applicability"] != "reference_only_not_scored")
    ]
    classes: Dict[str, str] = {}
    for row in selected.to_dict("records"):
        label = str(row.get("hard_or_soft", "")).lower()
        is_hard = label.startswith("binding") or label == "due_diligence_gate_for_binding_code"
        classes[str(row["constraint_id"])] = "hard" if is_hard else "soft"
    return classes


def implementation_feasibility(
    scenario_id: str,
    city: str,
    constraints: Optional[pd.DataFrame],
    network: Optional[gpd.GeoDataFrame],
    destinations: Optional[gpd.GeoDataFrame],
    turning_spaces: Optional[gpd.GeoDataFrame],
    objects: Optional[gpd.GeoDataFrame],
    boundary: Any,
) -> Dict[str, Any]:
    checks = network_and_geometry_checks(network, destinations, turning_spaces)
    checks.extend(object_integrity_checks(objects, destinations, turning_spaces))
    resource = resource_check(scenario_id, objects, boundary)
    checks.append({"constraint_id": "study_resource_cap", **resource})
    expected_regulatory = expected_constraint_ids(city)
    constraint_classes = regulatory_constraint_classes(city)
    required_evidence = {"unresolved_critical_conflicts"}
    supplied_ids = set() if constraints is None else set(constraints["constraint_id"])
    missing_rows = sorted((expected_regulatory | required_evidence) - supplied_ids)
    if constraints is not None:
        permitted_ids = expected_regulatory | required_evidence
        unknown_rows = sorted(supplied_ids - permitted_ids)
        if unknown_rows:
            raise EvidenceError(f"constraint_results.csv contains unregistered constraint IDs: {unknown_rows}")
        for row in constraints.to_dict("records"):
            checks.append({
                "constraint_id": row["constraint_id"],
                "constraint_class": constraint_classes.get(row["constraint_id"], "hard"),
                "status": "evaluated" if row["status"] in {"pass", "fail"} else "not_evaluable",
                "passed": True if row["status"] == "pass" else False if row["status"] == "fail" else None,
                "evidence_reference": row["evidence_reference"],
            })
    for constraint_id in missing_rows:
        checks.append({
            "constraint_id": constraint_id,
            "constraint_class": constraint_classes.get(constraint_id, "hard"),
            "status": "not_evaluable",
            "passed": None,
            "reason": "required constraint-results row is absent",
        })
    core_ids = {
        "accessible_route_clear_width",
        "accessible_route_running_slope",
        "accessible_route_cross_slope",
        "disconnected_accessible_routes",
        "wheelchair_turning_diameter",
        "cross_domain_overlap_area",
        "missing_required_provenance_links",
        "study_resource_cap",
        "unresolved_critical_conflicts",
    }
    for item in checks:
        item.setdefault(
            "constraint_class",
            "hard" if item["constraint_id"] in core_ids else constraint_classes.get(item["constraint_id"], "soft"),
        )
    core_not_evaluable = [
        item for item in checks
        if item["constraint_id"] in core_ids and item["status"] == "not_evaluable"
    ]
    if core_not_evaluable or missing_rows:
        return metric(
            None,
            "not_evaluable",
            reason="one or more shared predicates or required constraint rows lack evidence",
            missing_constraint_rows=missing_rows,
            checks=checks,
        )
    evaluated = [item for item in checks if item["status"] == "evaluated"]
    not_evaluable = [item for item in checks if item["status"] == "not_evaluable"]
    if not evaluated:
        return metric(None, "not_evaluable", reason="no applicable evaluable implementation predicates", checks=checks)
    hard_evaluated = [item for item in evaluated if item["constraint_class"] == "hard"]
    soft_evaluated = [item for item in evaluated if item["constraint_class"] == "soft"]
    hard_gate = 1.0 if hard_evaluated and all(bool(item["passed"]) for item in hard_evaluated) else 0.0
    soft_score = (
        sum(bool(item["passed"]) for item in soft_evaluated) / len(soft_evaluated)
        if soft_evaluated else 1.0
    )
    value = hard_gate * soft_score
    return metric(
        value,
        "evaluated",
        evaluated_count=len(evaluated),
        passed_count=sum(bool(item["passed"]) for item in evaluated),
        failed_count=sum(not bool(item["passed"]) for item in evaluated),
        not_evaluable_count=len(not_evaluable),
        hard_gate=hard_gate,
        soft_score=soft_score,
        hard_evaluated_count=len(hard_evaluated),
        soft_evaluated_count=len(soft_evaluated),
        all_hard_constraints_passed=bool(hard_evaluated) and hard_gate == 1.0,
        checks=checks,
        denominator_rule="not_evaluable predicates excluded; any evaluable hard failure sets I_impl to zero",
    )


def evaluate(args: argparse.Namespace) -> Dict[str, Any]:
    scenario_rows = pd.read_csv(PREREG / "scenarios.csv", dtype=str)
    selected = scenario_rows[scenario_rows["scenario_id"] == args.scenario_id]
    if len(selected) != 1:
        raise EvidenceError(f"Unknown scenario_id: {args.scenario_id}")
    city = str(selected.iloc[0]["site"])
    world_path = args.world_model or SITE_FILES[city]
    if not world_path.is_file() or not args.design.is_file():
        raise EvidenceError("World-model and design GeoPackages must exist")
    origins = gpd.read_file(world_path, layer="analysis_origins")
    boundary_layer = "analysis_boundary" if city == "Chicago" else "site_geometry"
    boundary_frame = gpd.read_file(world_path, layer=boundary_layer)
    boundary = boundary_frame.geometry.iloc[0]
    design_layers = layers(args.design)
    network = read_layer(args.design, "accessible_network")
    entrances = read_layer(args.design, "green_entrances")
    usable = read_layer(args.design, "usable_spaces")
    shade = read_layer(args.design, "shade_footprints")
    objects = read_layer(args.design, "design_objects")
    destinations = read_layer(args.design, "required_destinations")
    turning_spaces = read_layer(args.design, "turning_spaces")
    for frame in (network, entrances, usable, shade, objects, destinations, turning_spaces):
        if frame is not None and frame.crs != origins.crs:
            frame.to_crs(origins.crs, inplace=True)
    if boundary_frame.crs != origins.crs:
        boundary = boundary_frame.to_crs(origins.crs).geometry.iloc[0]
    access, equity, _ = access_and_equity(origins, network, entrances)
    needs = read_status_csv(args.need_results, "need_id")
    constraints = read_status_csv(args.constraint_results, "constraint_id")
    results = {
        "A_green": access,
        "E_equity": equity,
        "C_comfort": shade_comfort(usable, shade),
        "P_ret": need_retention(args.scenario_id, needs),
        "I_impl": implementation_feasibility(
            args.scenario_id, city, constraints, network, destinations, turning_spaces, objects, boundary
        ),
    }
    return {
        "schema_version": "1.0.0",
        "scenario_id": args.scenario_id,
        "workflow": args.workflow,
        "city": city,
        "world_model": str(world_path),
        "design_package": str(args.design),
        "design_layers_observed": sorted(design_layers),
        "outcomes": results,
        "all_five_evaluated": all(item["status"] == "evaluated" for item in results.values()),
        "claim_boundary": "analytical comparison only; not legal compliance, permission, cost, or construction readiness",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--workflow", required=True, choices=["EXISTING", "CONVENTIONAL", "DIGITAL", "POLIS"])
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--world-model", type=Path)
    parser.add_argument("--need-results", type=Path)
    parser.add_argument("--constraint-results", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args)
    except EvidenceError as exc:
        print(f"Evidence error: {exc}")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(args.output), "all_five_evaluated": result["all_five_evaluated"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
