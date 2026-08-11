#!/usr/bin/env python3
"""Build auditable POLIS site world-model packages from frozen public data."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiPoint,
    Point,
    Polygon,
    box,
    mapping,
)


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
VECTOR = ROOT / "vector"
RASTER = ROOT / "raster"
METADATA = ROOT / "metadata"
VALIDATION = ROOT / "validation"
RETRIEVAL_DATE = date(2026, 8, 6).isoformat()

SITES = {
    "SUZ": {
        "city": "Suzhou",
        "site_name": "Xutai Road neighbourhood grass parcel",
        "osm_way_id": 741252447,
        "expected_geometry": "Polygon",
        "analysis_crs": "EPSG:32651",
        "timezone": "Asia/Shanghai",
        "bbox": [120.5852, 31.2858, 120.5878, 31.2884],
        "raw_file": "suzhou_osm_overpass_2026-08-06.json",
        "dem_url": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N31_00_E120_00_DEM/Copernicus_DSM_COG_10_N31_00_E120_00_DEM.tif",
    },
    "LON": {
        "city": "London",
        "site_name": "Mitre Yard brownfield site",
        "osm_way_id": 49601059,
        "expected_geometry": "Polygon",
        "analysis_crs": "EPSG:27700",
        "timezone": "Europe/London",
        "bbox": [-0.2380, 51.5245, -0.2328, 51.5290],
        "raw_file": "london_osm_overpass_2026-08-06.json",
        "dem_url": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N51_00_W001_00_DEM/Copernicus_DSM_COG_10_N51_00_W001_00_DEM.tif",
    },
    "CHI": {
        "city": "Chicago",
        "site_name": "Selected New ERA Trail corridor segment",
        "osm_way_id": 624189839,
        "expected_geometry": "LineString",
        "analysis_crs": "EPSG:26916",
        "timezone": "America/Chicago",
        "bbox": [-87.6790, 41.7858, -87.6620, 41.7892],
        "raw_file": "chicago_osm_overpass_2026-08-06.json",
        # The manuscript freezes the analytical study extent as the selected
        # trail segment plus a 20 m envelope. This is a study boundary, not a
        # legal right-of-way or parcel claim.
        "analysis_buffer_m": 20.0,
        "dem_url": "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N41_00_W088_00_DEM/Copernicus_DSM_COG_10_N41_00_W088_00_DEM.tif",
    },
}

SELECTED_TAGS = [
    "name",
    "highway",
    "railway",
    "building",
    "building:levels",
    "height",
    "landuse",
    "natural",
    "leisure",
    "amenity",
    "entrance",
    "barrier",
    "access",
    "wheelchair",
    "width",
    "surface",
    "smoothness",
    "incline",
    "kerb",
    "crossing",
    "tactile_paving",
]

GREEN_TAGS = {
    "landuse": {"grass", "forest", "meadow", "recreation_ground", "allotments", "orchard"},
    "natural": {"wood", "grassland", "scrub", "wetland", "water"},
    "leisure": {"park", "garden", "nature_reserve"},
}

ACTIVITY_VALUES = {
    "playground",
    "pitch",
    "sports_centre",
    "fitness_station",
    "recreation_ground",
    "community_centre",
}

ACCESS_KEYS = {
    "entrance",
    "wheelchair",
    "width",
    "incline",
    "kerb",
    "crossing",
    "tactile_paving",
    "smoothness",
    "surface",
    "step_count",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tags_record(element: dict, geometry) -> dict:
    tags = element.get("tags", {})
    record = {
        "osm_type": element["type"],
        "osm_id": str(element["id"]),
        "source": "OpenStreetMap",
        "retrieved": RETRIEVAL_DATE,
        "tags_json": json.dumps(tags, ensure_ascii=True, sort_keys=True),
        "geometry": geometry,
    }
    for key in SELECTED_TAGS:
        record[key.replace(":", "_")] = tags.get(key)
    return record


def way_geometry(element: dict):
    coords = [(p["lon"], p["lat"]) for p in element.get("geometry", [])]
    if len(coords) < 2:
        return None
    if len(coords) >= 4 and coords[0] == coords[-1]:
        try:
            polygon = Polygon(coords)
            if polygon.is_valid and not polygon.is_empty:
                return polygon
        except ValueError:
            pass
    return LineString(coords)


def matches_green(tags: dict) -> bool:
    return any(tags.get(key) in values for key, values in GREEN_TAGS.items())


def matches_activity(tags: dict) -> bool:
    return tags.get("leisure") in ACTIVITY_VALUES or tags.get("amenity") in ACTIVITY_VALUES


def matches_accessibility(tags: dict) -> bool:
    return bool(ACCESS_KEYS.intersection(tags)) or tags.get("highway") in {"steps", "crossing", "elevator"}


def extract_points(geometry):
    if geometry.is_empty:
        return []
    if isinstance(geometry, Point):
        return [geometry]
    if isinstance(geometry, MultiPoint):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        points = []
        for child in geometry.geoms:
            points.extend(extract_points(child))
        return points
    return []


def write_layer(records: list[dict], layer: str, gpkg: Path, crs: str) -> int:
    if not records:
        # Keep the same layer names in all three GeoPackages, including a
        # genuine empty layer where the frozen source has no mapped features.
        columns = [
            "osm_type",
            "osm_id",
            "source",
            "retrieved",
            "tags_json",
            *[key.replace(":", "_") for key in SELECTED_TAGS],
        ]
        empty = pd.DataFrame({column: pd.Series(dtype="object") for column in columns})
        empty["geometry"] = gpd.GeoSeries([], crs="EPSG:4326")
        gpd.GeoDataFrame(empty, geometry="geometry", crs="EPSG:4326").to_crs(crs).to_file(
            gpkg, layer=layer, driver="GPKG"
        )
        return 0
    frame = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326").to_crs(crs)
    frame.to_file(gpkg, layer=layer, driver="GPKG")
    return len(frame)


def clip_dem(site_id: str, cfg: dict) -> dict:
    target = RASTER / f"{site_id.lower()}_copernicus_dem30_context.tif"
    with rasterio.open(cfg["dem_url"]) as source:
        clipped, transform = mask(source, [mapping(box(*cfg["bbox"]))], crop=True)
        profile = source.profile.copy()
        profile.update(
            height=clipped.shape[1],
            width=clipped.shape[2],
            transform=transform,
            compress="deflate",
        )
        with rasterio.open(target, "w", **profile) as destination:
            destination.write(clipped)
        band = clipped[0].astype(float)
        nodata = source.nodata
        if nodata is not None:
            band = band[band != nodata]
        band = band[np.isfinite(band)]
    return {
        "file": target.relative_to(ROOT).as_posix(),
        "sha256": sha256(target),
        "valid_cells": int(band.size),
        "min_elevation_m": float(np.min(band)) if band.size else None,
        "max_elevation_m": float(np.max(band)) if band.size else None,
        "mean_elevation_m": float(np.mean(band)) if band.size else None,
        "note": "30 m Copernicus DEM context; not an object-height or engineering-grade survey.",
    }


def make_origin_grid(site_id: str, site_metric, crs: str) -> list[dict]:
    catchment = site_metric.buffer(1000)
    minx, miny, maxx, maxy = catchment.bounds
    spacing = 100.0
    rows = []
    x = math.floor(minx / spacing) * spacing + spacing / 2
    while x <= maxx:
        y = math.floor(miny / spacing) * spacing + spacing / 2
        while y <= maxy:
            point = Point(x, y)
            if catchment.contains(point):
                rows.append(
                    {
                        "origin_id": f"{site_id}-ORG-{len(rows) + 1:04d}",
                        "site_id": site_id,
                        "grid_m": 100,
                        "population_weight": np.nan,
                        "population_source_id": None,
                        "weight_status": "BLOCKED_REAL_POPULATION_EXTRACT_REQUIRED",
                        "geometry": point,
                    }
                )
            y += spacing
        x += spacing
    return rows


def build_site(site_id: str, cfg: dict) -> tuple[dict, list[dict], list[dict]]:
    raw_path = RAW / cfg["raw_file"]
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    gpkg = VECTOR / f"{site_id.lower()}_world_model.gpkg"
    if gpkg.exists():
        gpkg.unlink()

    buckets = {
        "site_geometry": [],
        "context_extent": [],
        "transport_network": [],
        "buildings": [],
        "green_blue": [],
        "trees": [],
        "activity_amenities": [],
        "mapped_access_points": [],
        "accessibility_features": [],
        "barriers": [],
    }
    all_network_records = []
    relation_count = 0

    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        if element["type"] == "node":
            if "lon" not in element or "lat" not in element:
                continue
            geometry = Point(element["lon"], element["lat"])
            record = tags_record(element, geometry)
            if tags.get("natural") == "tree":
                buckets["trees"].append(record)
            if tags.get("entrance") or tags.get("barrier") in {"gate", "entrance"} or tags.get("highway") == "crossing":
                buckets["mapped_access_points"].append(record)
            if matches_activity(tags) or tags.get("amenity"):
                buckets["activity_amenities"].append(record)
            if matches_accessibility(tags):
                buckets["accessibility_features"].append(record)
            if tags.get("barrier"):
                buckets["barriers"].append(record)
            continue

        if element["type"] == "relation":
            relation_count += 1
            continue
        if element["type"] != "way":
            continue

        geometry = way_geometry(element)
        if geometry is None:
            continue
        record = tags_record(element, geometry)
        if element["id"] == cfg["osm_way_id"]:
            buckets["site_geometry"].append(record)
        if tags.get("highway") or tags.get("railway"):
            network_geometry = LineString(geometry.exterior.coords) if isinstance(geometry, Polygon) else geometry
            network_record = tags_record(element, network_geometry)
            buckets["transport_network"].append(network_record)
            all_network_records.append(network_record)
        if tags.get("building") and isinstance(geometry, Polygon):
            buckets["buildings"].append(record)
        if matches_green(tags) and isinstance(geometry, Polygon):
            buckets["green_blue"].append(record)
        if matches_activity(tags):
            buckets["activity_amenities"].append(record)
        if matches_accessibility(tags):
            buckets["accessibility_features"].append(record)
        if tags.get("barrier"):
            buckets["barriers"].append(record)

    if len(buckets["site_geometry"]) != 1:
        raise RuntimeError(f"{site_id}: expected one OSM site geometry, found {len(buckets['site_geometry'])}")

    site_wgs = buckets["site_geometry"][0]["geometry"]
    if site_wgs.geom_type != cfg["expected_geometry"]:
        raise RuntimeError(f"{site_id}: expected {cfg['expected_geometry']}, found {site_wgs.geom_type}")

    extent_element = {
        "type": "derived",
        "id": f"{site_id}-CONTEXT",
        "tags": {"derivation": "registered_query_bbox", "role": "source_context_extent"},
    }
    buckets["context_extent"].append(tags_record(extent_element, box(*cfg["bbox"])))

    layer_counts = {}
    for layer, records in buckets.items():
        layer_counts[layer] = write_layer(records, layer, gpkg, cfg["analysis_crs"])

    raw_site_metric = gpd.GeoSeries([site_wgs], crs="EPSG:4326").to_crs(cfg["analysis_crs"]).iloc[0]
    buffer_m = cfg.get("analysis_buffer_m")
    site_metric = raw_site_metric.buffer(float(buffer_m)) if buffer_m else raw_site_metric
    if buffer_m:
        boundary_frame = gpd.GeoDataFrame(
            [{
                "site_id": site_id,
                "derivation": "registered_manuscript_20m_envelope_around_frozen_osm_axis",
                "source_osm_id": str(cfg["osm_way_id"]),
                "boundary_status": "FROZEN_ANALYTICAL_BOUNDARY_NOT_LEGAL_ROW",
                "buffer_m_each_side": float(buffer_m),
                "geometry": site_metric,
            }],
            geometry="geometry",
            crs=cfg["analysis_crs"],
        )
        boundary_frame.to_file(gpkg, layer="analysis_boundary", driver="GPKG")
        layer_counts["analysis_boundary"] = 1
    network_metric = gpd.GeoDataFrame(all_network_records, geometry="geometry", crs="EPSG:4326").to_crs(cfg["analysis_crs"])
    candidate_records = []
    if site_metric.geom_type == "Polygon":
        boundary = site_metric.boundary
        for _, row in network_metric.iterrows():
            for point in extract_points(row.geometry.intersection(boundary)):
                candidate_records.append(
                    {
                        "candidate_id": f"{site_id}-ACC-{len(candidate_records) + 1:03d}",
                        "site_id": site_id,
                        "derivation": "transport_network_intersection_with_site_boundary",
                        "osm_id": row.osm_id,
                        "verification_status": "CANDIDATE_FIELD_OR_IMAGE_VERIFICATION_REQUIRED",
                        "geometry": point,
                    }
                )
    else:
        for point, suffix in [(Point(site_metric.coords[0]), "A"), (Point(site_metric.coords[-1]), "B")]:
            candidate_records.append(
                {
                    "candidate_id": f"{site_id}-AXIS-{suffix}",
                    "site_id": site_id,
                    "derivation": "frozen_osm_axis_endpoint",
                    "osm_id": str(cfg["osm_way_id"]),
                    "verification_status": "CANDIDATE_FIELD_OR_IMAGE_VERIFICATION_REQUIRED",
                    "geometry": point,
                }
            )
    if candidate_records:
        gpd.GeoDataFrame(candidate_records, geometry="geometry", crs=cfg["analysis_crs"]).to_file(
            gpkg, layer="derived_access_candidates", driver="GPKG"
        )
    else:
        empty_candidates = gpd.GeoDataFrame(
            {
                "candidate_id": pd.Series(dtype="object"),
                "site_id": pd.Series(dtype="object"),
                "derivation": pd.Series(dtype="object"),
                "osm_id": pd.Series(dtype="object"),
                "verification_status": pd.Series(dtype="object"),
                "geometry": gpd.GeoSeries([], crs=cfg["analysis_crs"]),
            },
            geometry="geometry",
            crs=cfg["analysis_crs"],
        )
        empty_candidates.to_file(gpkg, layer="derived_access_candidates", driver="GPKG")
    layer_counts["derived_access_candidates"] = len(candidate_records)

    origins = make_origin_grid(site_id, site_metric, cfg["analysis_crs"])
    gpd.GeoDataFrame(origins, geometry="geometry", crs=cfg["analysis_crs"]).to_file(
        gpkg, layer="analysis_origins", driver="GPKG"
    )
    layer_counts["analysis_origins"] = len(origins)

    centroid_wgs = gpd.GeoSeries([site_metric.centroid], crs=cfg["analysis_crs"]).to_crs("EPSG:4326").iloc[0]
    building_records = buckets["buildings"]
    tree_records = buckets["trees"]
    building_height_count = sum(
        1
        for item in building_records
        if json.loads(item["tags_json"]).get("height") or json.loads(item["tags_json"]).get("building:levels")
    )
    tree_height_count = sum(1 for item in tree_records if json.loads(item["tags_json"]).get("height"))

    metric_row = {
        "site_id": site_id,
        "city": cfg["city"],
        "site_name": cfg["site_name"],
        "osm_way_id": cfg["osm_way_id"],
        "geometry_role": "analytical_boundary" if site_metric.geom_type == "Polygon" else "corridor_axis_only",
        "geometry_type": site_metric.geom_type,
        "source_crs": "EPSG:4326",
        "analysis_crs": cfg["analysis_crs"],
        "timezone": cfg["timezone"],
        "centroid_lon": centroid_wgs.x,
        "centroid_lat": centroid_wgs.y,
        "area_m2": site_metric.area if site_metric.geom_type == "Polygon" else np.nan,
        "axis_length_m": raw_site_metric.length if raw_site_metric.geom_type == "LineString" else np.nan,
        "corridor_width_m": (float(buffer_m) * 2 if buffer_m else np.nan),
        "corridor_width_status": "FROZEN_STUDY_ANALYTICAL_ENVELOPE" if buffer_m else "NOT_APPLICABLE",
        "raw_osm_timestamp": payload.get("osm3s", {}).get("timestamp_osm_base"),
        "raw_osm_sha256": sha256(raw_path),
        "gpkg_sha256": None,
        "building_count": len(building_records),
        "building_height_or_levels_count": building_height_count,
        "mapped_tree_count": len(tree_records),
        "mapped_tree_height_count": tree_height_count,
    }

    sun_rows = []
    for month_day in ["06-21", "07-21", "08-21"]:
        for local_time, weight in zip(["10:00", "12:00", "14:00", "16:00"], [0.20, 0.30, 0.30, 0.20]):
            sun_rows.append(
                {
                    "site_id": site_id,
                    "latitude": centroid_wgs.y,
                    "longitude": centroid_wgs.x,
                    "timezone": cfg["timezone"],
                    "reference_year": 2026,
                    "month_day": month_day,
                    "local_solar_time": local_time,
                    "time_weight": weight,
                    "shadow_input_status": "BLOCKED_OBJECT_HEIGHT_COMPLETENESS_REQUIRED",
                }
            )

    report = {
        "site_id": site_id,
        "osm_timestamp": metric_row["raw_osm_timestamp"],
        "relations_retained_raw_not_vectorised": relation_count,
        "layers": layer_counts,
        "geometry": {
            "type": metric_row["geometry_type"],
            "area_m2": None if pd.isna(metric_row["area_m2"]) else metric_row["area_m2"],
            "axis_length_m": None if pd.isna(metric_row["axis_length_m"]) else metric_row["axis_length_m"],
        },
        "height_completeness": {
            "buildings_with_height_or_levels": building_height_count,
            "building_total": len(building_records),
            "trees_with_height": tree_height_count,
            "tree_total": len(tree_records),
        },
        "blocking_items": [
            "real population values for the 100 m analysis origins",
            "verified building and tree heights for shade simulation",
            "absolute baseline capital and maintenance budget",
            "project-level regulatory trigger values",
        ],
    }

    dem = clip_dem(site_id, cfg)
    report["dem"] = dem
    metric_row["gpkg_sha256"] = sha256(gpkg)
    return metric_row, sun_rows, [report]


def write_csv(path: Path, rows: list[dict]) -> None:
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def build_budget_register() -> None:
    scenarios = pd.read_csv(ROOT.parent / "preregistration" / "scenarios.csv")
    budget = scenarios[["scenario_id", "site", "variant", "budget_multiplier"]].copy()
    budget["base_capital_budget"] = np.nan
    budget["currency"] = np.nan
    budget["price_base_date"] = np.nan
    budget["scenario_capital_cap"] = np.nan
    budget["budget_source_id"] = np.nan
    budget["status"] = "BLOCKED_AUTHOR_DOCUMENTED_REAL_BUDGET_REQUIRED"
    budget.to_csv(METADATA / "scenario_budget_register.csv", index=False)


def build_regulatory_trigger_register() -> None:
    constraints = pd.read_csv(ROOT.parent / "preregistration" / "constraints" / "site_constraints.csv")
    register = constraints[
        ["constraint_id", "site", "parameter", "applicability_condition", "source_id", "real_project_applicability_status"]
    ].copy()
    register["observed_project_value"] = np.nan
    register["observed_unit"] = np.nan
    register["evidence_file"] = np.nan
    register["verification_status"] = "BLOCKED_PROJECT_LEVEL_EVIDENCE_REQUIRED"
    register["rule"] = "Do not code pass or not_applicable from a missing trigger value."
    register.to_csv(METADATA / "regulatory_trigger_register.csv", index=False)


def build_source_register(site_reports: list[dict]) -> None:
    rows = []
    for site_id, cfg in SITES.items():
        rows.extend(
            [
                {
                    "source_id": f"OSM-{site_id}-20260806",
                    "site_id": site_id,
                    "dataset": "OpenStreetMap Overpass snapshot",
                    "provider": "OpenStreetMap contributors",
                    "url": "https://overpass-api.de/api/interpreter",
                    "retrieved": RETRIEVAL_DATE,
                    "license": "ODbL 1.0",
                    "role": "site geometry and mapped context features",
                    "status": "FROZEN_LOCAL_SNAPSHOT",
                },
                {
                    "source_id": f"COPDEM30-{site_id}",
                    "site_id": site_id,
                    "dataset": "Copernicus DEM GLO-30",
                    "provider": "Copernicus Programme",
                    "url": cfg["dem_url"],
                    "retrieved": RETRIEVAL_DATE,
                    "license": "Copernicus DEM licence",
                    "role": "context elevation only",
                    "status": "FROZEN_LOCAL_CLIP",
                },
                {
                    "source_id": f"POP-{site_id}-PENDING",
                    "site_id": site_id,
                    "dataset": "Population grid or official small-area population",
                    "provider": None,
                    "url": None,
                    "retrieved": None,
                    "license": None,
                    "role": "A_green and E_equity origin weights",
                    "status": "BLOCKED_SOURCE_AND_EXTRACT_NOT_FROZEN",
                },
            ]
        )
    write_csv(METADATA / "source_register.csv", rows)


def build_manifest() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name == "manifest.sha256":
            continue
        rows.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    (METADATA / "manifest.sha256").write_text("\n".join(rows) + "\n", encoding="ascii")


def main() -> None:
    for directory in [RAW, VECTOR, RASTER, METADATA, VALIDATION]:
        directory.mkdir(parents=True, exist_ok=True)

    metrics = []
    sun = []
    reports = []
    for site_id, cfg in SITES.items():
        metric_row, sun_rows, site_reports = build_site(site_id, cfg)
        metrics.append(metric_row)
        sun.extend(sun_rows)
        reports.extend(site_reports)

    write_csv(METADATA / "site_registry.csv", metrics)
    write_csv(METADATA / "solar_evaluation_schedule.csv", sun)
    build_budget_register()
    build_regulatory_trigger_register()
    build_source_register(reports)

    summary = {
        "package_version": "1.0.0",
        "built_on": RETRIEVAL_DATE,
        "status": "BASE_SPATIAL_PACKAGE_BUILT_WITH_BLOCKING_INPUTS",
        "site_count": len(reports),
        "sites": reports,
        "experiment_1_ready": False,
        "global_blocking_items": [
            "population weights are not yet frozen",
            "shade object heights are incomplete",
            "Chicago corridor is an axis, not an author-confirmed polygon",
            "absolute budgets are not documented",
            "project-level regulatory applicability evidence is not documented",
        ],
    }
    (VALIDATION / "world_model_validation.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
    )
    build_manifest()
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
