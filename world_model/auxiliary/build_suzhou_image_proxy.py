#!/usr/bin/env python3
"""Build a reproducible image-derived Suzhou proxy input.

The output is an analytical proxy, not a topographic or accessibility survey.
Central values are usable for the formal simulation only when the low/high
sensitivity variants are reported with the same prominence.
"""

from __future__ import annotations

import json
import math
import csv
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon


ROOT = Path(__file__).resolve().parents[2]
RAW_OSM = ROOT / "world_model/raw/suzhou_osm_overpass_2026-08-06.json"
OUTPUT = ROOT / "world_model/auxiliary/suzhou_image_proxy.gpkg"
SUMMARY = ROOT / "world_model/auxiliary/suzhou_image_proxy_summary.json"
PARAMETERS = ROOT / "world_model/auxiliary/suzhou_image_proxy_parameters.csv"

ZOOM = 19
TILE_X_MIN = 437759
TILE_Y_MIN = 214128
SITE_ID = "SUZ"
SOURCE_ID = "AUX-ESRI-WORLD-IMAGERY-SUZ-20260806"
ANALYSIS_CRS = "EPSG:32651"


def pixel_to_lonlat(x: float, y: float) -> tuple[float, float]:
    n = 2**ZOOM
    world_x = (TILE_X_MIN * 256 + x) / 256
    world_y = (TILE_Y_MIN * 256 + y) / 256
    lon = world_x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * world_y / n))))
    return lon, lat


def registered_boundary() -> gpd.GeoDataFrame:
    payload = json.loads(RAW_OSM.read_text(encoding="utf-8"))
    feature = next(item for item in payload["elements"] if item.get("id") == 741252447)
    polygon = Polygon([(p["lon"], p["lat"]) for p in feature["geometry"]])
    return gpd.GeoDataFrame(
        [{"site_id": SITE_ID, "source": "OSM way 741252447", "geometry": polygon}],
        crs="EPSG:4326",
    ).to_crs(ANALYSIS_CRS)


def tree_candidates(boundary: Polygon) -> gpd.GeoDataFrame:
    # Pixel centres and approximate canopy diameters are manually interpreted
    # from the frozen z19 audit mosaic. They are candidates, not observations.
    interpreted = [
        (382, 245, 18),
        (369, 270, 14),
        (400, 275, 19),
        (382, 300, 17),
        (416, 302, 16),
        (433, 325, 18),
        (450, 346, 15),
        (470, 365, 16),
        (481, 390, 13),
        (510, 410, 17),
        (520, 445, 20),
        (540, 470, 16),
    ]
    resolution = 156543.03392804097 * math.cos(math.radians(31.2870684)) / (2**ZOOM)
    points = gpd.GeoSeries(
        [Point(pixel_to_lonlat(x, y)) for x, y, _ in interpreted], crs="EPSG:4326"
    ).to_crs(ANALYSIS_CRS)
    rows = []
    for index, ((_, _, diameter_px), point) in enumerate(zip(interpreted, points), start=1):
        if not boundary.covers(point):
            continue
        crown_diameter = diameter_px * resolution
        crown_radius = crown_diameter / 2.0
        rows.append(
            {
                "candidate_id": f"SUZ-TREE-PROXY-{index:02d}",
                "site_id": SITE_ID,
                "source_id": SOURCE_ID,
                "evidence_class": "image_derived_formal_proxy",
                "observation_status": "not_measured",
                "confidence": "low",
                "crown_radius_m_proxy": round(crown_radius, 3),
                "crown_radius_m_low": round(crown_radius * 0.75, 3),
                "crown_radius_m_high": round(crown_radius * 1.25, 3),
                "height_m_proxy": round(crown_diameter * 1.50, 3),
                "height_m_low": round(crown_diameter * 0.75, 3),
                "height_m_high": round(crown_diameter * 2.50, 3),
                "height_method": "crown_diameter_sensitivity_heuristic_no_species_or_lidar",
                "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
                "engineering_or_compliance_use": "prohibited",
                "geometry": point,
            }
        )
    return gpd.GeoDataFrame(rows, crs=ANALYSIS_CRS)


def path_candidate(boundary: Polygon) -> gpd.GeoDataFrame:
    pixels = [(376, 255), (367, 285), (365, 320), (374, 355), (395, 395), (420, 435), (455, 475)]
    line = gpd.GeoSeries(
        [LineString([pixel_to_lonlat(x, y) for x, y in pixels])], crs="EPSG:4326"
    ).to_crs(ANALYSIS_CRS).iloc[0]
    line = line.intersection(boundary)
    return gpd.GeoDataFrame(
        [
            {
                "candidate_id": "SUZ-PATH-PROXY-01",
                "site_id": SITE_ID,
                "source_id": SOURCE_ID,
                "evidence_class": "image_derived_formal_proxy",
                "observation_status": "not_measured",
                "confidence": "low",
                "clear_width_m_proxy": 1.79,
                "clear_width_m_low": 1.28,
                "clear_width_m_high": 2.30,
                "running_slope_proxy": 0.020,
                "running_slope_low": 0.000,
                "running_slope_high": 0.050,
                "cross_slope_proxy": 0.015,
                "cross_slope_low": 0.000,
                "cross_slope_high": 0.040,
                "slope_method": "scenario_proxy_not_resolved_by_30m_dem_or_imagery",
                "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
                "engineering_or_compliance_use": "prohibited",
                "geometry": line,
            }
        ],
        crs=ANALYSIS_CRS,
    )


def activity_candidate(boundary: Polygon) -> gpd.GeoDataFrame:
    # Visually open ground interpreted from the same image mosaic. The polygon
    # is a candidate activity zone; it is not a surveyed use or land-use record.
    pixels = [(401, 365), (474, 377), (517, 430), (475, 470), (425, 442)]
    polygon = gpd.GeoSeries(
        [Polygon([pixel_to_lonlat(x, y) for x, y in pixels])], crs="EPSG:4326"
    ).to_crs(ANALYSIS_CRS).iloc[0]
    polygon = polygon.intersection(boundary)
    return gpd.GeoDataFrame(
        [{
            "candidate_id": "SUZ-ACTIVITY-PROXY-01",
            "site_id": SITE_ID,
            "source_id": SOURCE_ID,
            "evidence_class": "image_derived_formal_proxy",
            "observation_status": "not_measured",
            "confidence": "low",
            "area_m2_proxy": round(float(polygon.area), 3),
            "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
            "engineering_or_compliance_use": "prohibited",
            "geometry": polygon,
        }],
        crs=ANALYSIS_CRS,
    )


def turning_candidate(boundary: Polygon) -> gpd.GeoDataFrame:
    centre = gpd.GeoSeries([Point(pixel_to_lonlat(420, 435))], crs="EPSG:4326").to_crs(ANALYSIS_CRS).iloc[0]
    diameter = 4.00
    geometry = centre.buffer(diameter / 2.0).intersection(boundary)
    return gpd.GeoDataFrame(
        [
            {
                "candidate_id": "SUZ-TURN-PROXY-01",
                "site_id": SITE_ID,
                "source_id": SOURCE_ID,
                "evidence_class": "image_derived_formal_proxy",
                "observation_status": "not_measured",
                "confidence": "low",
                "clear_diameter_m_proxy": diameter,
                "clear_diameter_m_low": 1.50,
                "clear_diameter_m_high": 8.00,
                "registered_test_diameter_m": 1.525,
                "surface_and_obstruction_status": "not_observed",
                "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
                "engineering_or_compliance_use": "prohibited",
                "geometry": geometry,
            }
        ],
        crs=ANALYSIS_CRS,
    )


def main() -> None:
    boundary_frame = registered_boundary()
    boundary = boundary_frame.geometry.iloc[0]
    trees = tree_candidates(boundary)
    path = path_candidate(boundary)
    turning = turning_candidate(boundary)
    activity = activity_candidate(boundary)
    if OUTPUT.exists():
        OUTPUT.unlink()
    boundary_frame.to_file(OUTPUT, layer="site_boundary_reference", driver="GPKG")
    trees.to_file(OUTPUT, layer="tree_candidates", driver="GPKG")
    path.to_file(OUTPUT, layer="path_candidates", driver="GPKG")
    turning.to_file(OUTPUT, layer="turning_space_candidates", driver="GPKG")
    activity.to_file(OUTPUT, layer="activity_zone_candidates", driver="GPKG")
    parameter_rows = []
    for row in trees.drop(columns="geometry").to_dict("records"):
        parameter_rows.append(
            {
                "feature_id": row["candidate_id"],
                "feature_type": "tree",
                "parameter": "crown_radius_m",
                "central": row["crown_radius_m_proxy"],
                "low": row["crown_radius_m_low"],
                "high": row["crown_radius_m_high"],
                "unit": "m",
                "status": row["observation_status"],
                "method": row["height_method"],
            }
        )
        parameter_rows.append(
            {
                "feature_id": row["candidate_id"],
                "feature_type": "tree",
                "parameter": "height_m",
                "central": row["height_m_proxy"],
                "low": row["height_m_low"],
                "high": row["height_m_high"],
                "unit": "m",
                "status": row["observation_status"],
                "method": row["height_method"],
            }
        )
    path_row = path.drop(columns="geometry").iloc[0].to_dict()
    for parameter, central, low, high, unit, method in [
        ("clear_width_m", path_row["clear_width_m_proxy"], path_row["clear_width_m_low"], path_row["clear_width_m_high"], "m", path_row["slope_method"]),
        ("running_slope", path_row["running_slope_proxy"], path_row["running_slope_low"], path_row["running_slope_high"], "fraction", path_row["slope_method"]),
        ("cross_slope", path_row["cross_slope_proxy"], path_row["cross_slope_low"], path_row["cross_slope_high"], "fraction", path_row["slope_method"]),
    ]:
        parameter_rows.append({"feature_id": path_row["candidate_id"], "feature_type": "path", "parameter": parameter, "central": central, "low": low, "high": high, "unit": unit, "status": path_row["observation_status"], "method": method})
    turn_row = turning.drop(columns="geometry").iloc[0].to_dict()
    parameter_rows.append({"feature_id": turn_row["candidate_id"], "feature_type": "turning_space", "parameter": "clear_diameter_m", "central": turn_row["clear_diameter_m_proxy"], "low": turn_row["clear_diameter_m_low"], "high": turn_row["clear_diameter_m_high"], "unit": "m", "status": turn_row["observation_status"], "method": "image_open_area_proxy_not_measured"})
    activity_row = activity.drop(columns="geometry").iloc[0].to_dict()
    parameter_rows.append({"feature_id": activity_row["candidate_id"], "feature_type": "activity_zone", "parameter": "area_m2", "central": activity_row["area_m2_proxy"], "low": round(activity_row["area_m2_proxy"] * 0.75, 3), "high": round(activity_row["area_m2_proxy"] * 1.25, 3), "unit": "m2", "status": activity_row["observation_status"], "method": "image_open_ground_proxy_not_measured"})
    with PARAMETERS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["feature_id", "feature_type", "parameter", "central", "low", "high", "unit", "status", "method"])
        writer.writeheader()
        writer.writerows(parameter_rows)
    summary = {
        "status": "FORMAL_ANALYTICAL_PROXY_NOT_SURVEY",
        "site_id": SITE_ID,
        "output": str(OUTPUT.relative_to(ROOT)),
        "parameters": str(PARAMETERS.relative_to(ROOT)),
        "tree_candidate_count": int(len(trees)),
        "path_candidate_count": int(len(path)),
        "turning_space_candidate_count": int(len(turning)),
        "activity_zone_candidate_count": int(len(activity)),
        "central_values_are_observations": False,
        "formal_use_condition": "Run central, low, and high variants; report proxy status and prohibit engineering/compliance interpretation.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
