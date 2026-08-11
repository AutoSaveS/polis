#!/usr/bin/env python3
"""Build auditable no-field accessibility proxies for London and Chicago.

Widths come from public sidewalk polygons in Chicago and geometric clear-space
sections around mapped service routes in London. Slopes come from public bare-
earth LiDAR DTM clips. These values are analytical proxies, not ADA/BS survey
measurements and cannot establish legal compliance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyogrio import write_dataframe
from rasterio.features import geometry_mask
from shapely.geometry import GeometryCollection, LineString, Point, Polygon
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "world_model"
OUTPUT = WORLD / "auxiliary"
RASTER = WORLD / "raster"

CONFIG = {
    "London": {
        "code": "LON", "crs": "EPSG:27700", "world": WORLD / "vector/lon_world_model.gpkg",
        "boundary_layer": "site_geometry", "dtm": RASTER / "lon_ea_lidar_dtm_1m.tif",
        "output": OUTPUT / "london_accessibility_proxy.gpkg",
        "source_id": "AUX-EA-LIDAR-DTM-LON-20260806",
    },
    "Chicago": {
        "code": "CHI", "crs": "EPSG:26916", "world": WORLD / "vector/chi_world_model.gpkg",
        "boundary_layer": "analysis_boundary", "dtm": RASTER / "chi_usgs_3dep_dtm_2019_2m.tif",
        "output": OUTPUT / "chicago_accessibility_proxy.gpkg",
        "sidewalks": WORLD / "raw/chicago_city_sidewalks_2011_corridor_clip.gpkg",
        "source_id": "AUX-USGS-3DEP-DTM-CHI-20260806",
    },
}


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def empty(name: str, crs: str) -> gpd.GeoDataFrame:
    fields = {
        "path_candidates": [
            "candidate_id", "source_id", "route_class", "evidence_class", "observation_status",
            "clear_width_m_low", "clear_width_m_central", "clear_width_m_high",
            "running_slope_low", "running_slope_central", "running_slope_high",
            "cross_slope_low", "cross_slope_central", "cross_slope_high",
            "width_method", "slope_method", "formal_use_rule", "verification_status",
        ],
        "turning_space_candidates": [
            "candidate_id", "path_candidate_id", "source_id", "evidence_class", "observation_status",
            "clear_diameter_m_low", "clear_diameter_m_central", "clear_diameter_m_high",
            "diameter_method", "formal_use_rule", "verification_status",
        ],
        "sidewalk_polygons": ["source_id", "width_m_proxy", "evidence_class", "observation_status"],
        "source_footprints": ["source_id", "source_url", "retrieved", "claim_boundary"],
    }[name]
    return gpd.GeoDataFrame(pd.DataFrame(columns=fields + ["geometry"]), geometry="geometry", crs=crs)


def metric_summary(values: Iterable[float]) -> Tuple[float, float, float]:
    values = np.asarray([v for v in values if np.isfinite(v) and v >= 0], dtype=float)
    if values.size == 0:
        return np.nan, np.nan, np.nan
    # low/central/high are uncertainty quantiles, not confidence intervals.
    return float(np.quantile(values, 0.10)), float(np.quantile(values, 0.50)), float(np.quantile(values, 0.90))


def read_raster(path: Path) -> Tuple[np.ndarray, rasterio.Affine, Any, float]:
    with rasterio.open(path) as source:
        array = source.read(1).astype("float64")
        nodata = source.nodata if source.nodata is not None else -9999.0
        array[(~np.isfinite(array)) | np.isclose(array, nodata)] = np.nan
        return array, source.transform, source.crs, nodata


def sample_raster(array: np.ndarray, transform: rasterio.Affine, points: List[Point]) -> np.ndarray:
    values = []
    for point in points:
        col, row = (~transform) * (point.x, point.y)
        col, row = int(round(col)), int(round(row))
        values.append(array[row, col] if 0 <= row < array.shape[0] and 0 <= col < array.shape[1] else np.nan)
    return np.asarray(values, dtype=float)


def route_points(line: LineString, spacing: float = 2.0) -> List[Point]:
    count = max(2, int(math.ceil(line.length / spacing)))
    return [line.interpolate(i / (count - 1), normalized=True) for i in range(count)]


def line_slopes(line: LineString, array: np.ndarray, transform: rasterio.Affine) -> Tuple[float, float, float, float, float, float]:
    """Estimate terrain gradients by multi-scale local plane fitting.

    Pixel-to-pixel differences are too sensitive to railway embankments and
    DTM gridding artefacts for accessibility proxies. Three buffer scales give
    an explicit low/central/high sensitivity without inventing surface detail.
    """
    start, end = Point(line.coords[0]), Point(line.coords[-1])
    dx, dy = end.x - start.x, end.y - start.y
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    run, cross = [], []
    for radius in (3.0, 5.0, 8.0):
        mask = geometry_mask([line.buffer(radius)], array.shape, transform, invert=True)
        rows, cols = np.where(mask & np.isfinite(array))
        if len(rows) < 6:
            continue
        xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
        xs, ys = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
        x0, y0 = float(xs.mean()), float(ys.mean())
        design = np.column_stack([xs - x0, ys - y0, np.ones(len(xs))])
        a, b, _ = np.linalg.lstsq(design, array[rows, cols], rcond=None)[0]
        run.append(abs(float(a * ux + b * uy)))
        cross.append(abs(float(a * nx + b * ny)))
    rl, rc, rh = metric_summary(run)
    cl, cc, ch = metric_summary(cross)
    return rl, rc, rh, cl, cc, ch


def polygon_minor_width(geometry: Any) -> float:
    if geometry is None or geometry.is_empty:
        return np.nan
    rectangle = geometry.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)
    lengths = [Point(coords[i]).distance(Point(coords[i + 1])) for i in range(4)]
    return float(min(lengths)) if lengths else np.nan


def width_from_sidewalks(line: LineString, sidewalks: gpd.GeoDataFrame) -> Tuple[float, float, float]:
    if sidewalks.empty:
        return np.nan, np.nan, np.nan
    distances = sidewalks.geometry.distance(line)
    nearest = float(distances.min())
    nearby = sidewalks[distances <= min(2.5, nearest + 0.35)]
    widths = [polygon_minor_width(g) for g in nearby.geometry]
    widths = [v for v in widths if np.isfinite(v) and 0.4 <= v <= 8.0]
    if not widths:
        return np.nan, np.nan, np.nan
    central = float(np.median(widths))
    return central * 0.9, central, central * 1.1


def london_clear_widths(line: LineString, boundary: Any, obstacles: Any) -> Tuple[float, float, float]:
    values = []
    points = route_points(line, spacing=3.0)
    for i, point in enumerate(points):
        before = points[max(0, i - 1)]
        after = points[min(len(points) - 1, i + 1)]
        dx, dy = after.x - before.x, after.y - before.y
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        transect = LineString([(point.x - nx * 20.0, point.y - ny * 20.0), (point.x + nx * 20.0, point.y + ny * 20.0)])
        usable = transect.intersection(boundary).difference(obstacles)
        if usable.is_empty:
            continue
        segments = list(usable.geoms) if hasattr(usable, "geoms") else [usable]
        containing = [segment.length for segment in segments if segment.distance(point) < 0.01]
        if containing:
            values.append(float(max(containing)))
    low, central, high = metric_summary(values)
    return low * 0.85, central, high * 1.15


def route_rows(city: str, boundary: Any, array: np.ndarray, transform: rasterio.Affine, config: Dict[str, Any]) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    crs = config["crs"]
    world = config["world"]
    network = gpd.read_file(world, layer="transport_network").to_crs(crs)
    network = network[network.geometry.intersects(boundary)].copy()
    if city == "London":
        network = network[network["highway"].fillna("").isin(["service", "footway", "path", "pedestrian"])].copy()
        buildings = gpd.read_file(world, layer="buildings").to_crs(crs)
        barriers = gpd.read_file(world, layer="barriers").to_crs(crs)
        obstacles = unary_union(list(buildings.geometry) + [g.buffer(0.3) for g in barriers.geometry]) if not barriers.empty else unary_union(list(buildings.geometry))
        sidewalks = empty("sidewalk_polygons", crs)
    else:
        network = network[network["highway"].fillna("").isin(["footway", "path", "pedestrian", "cycleway"])].copy()
        sidewalks = gpd.read_file(config["sidewalks"], layer="sidewalk_polygons").to_crs(crs)
        sidewalks = gpd.clip(sidewalks, gpd.GeoDataFrame(geometry=[boundary], crs=crs))
        obstacles = GeometryCollection()
    rows = []
    turn_rows = []
    for index, item in enumerate(network.itertuples(), start=1):
        geometry = item.geometry.intersection(boundary)
        if geometry.is_empty:
            continue
        parts = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
        for part_index, part in enumerate(parts, start=1):
            if part.geom_type != "LineString" or part.length < 3.0:
                continue
            if city == "London":
                wl, wc, wh = london_clear_widths(part, boundary, obstacles)
                route_class = "OSM_service_clear_corridor_proxy"
                evidence = "remote_sensing_geometry_proxy"
                width_method = "perpendicular_clear_section_between_boundary_buildings_and_barriers"
            else:
                wl, wc, wh = width_from_sidewalks(part, sidewalks)
                route_class = "OSM_footway_official_sidewalk_polygon_proxy"
                evidence = "official_sidewalk_geometry_proxy"
                width_method = "nearest_city_of_chicago_sidewalk_polygon_minimum_rotated_rectangle"
            sl, sc, sh, cl, cc, ch = line_slopes(part, array, transform)
            if not all(np.isfinite(v) for v in (wl, wc, wh, sl, sc, sh, cl, cc, ch)):
                continue
            candidate_id = f"{config['code']}-ACCESS-PROXY-{index:03d}-{part_index:02d}"
            destination = part.interpolate(0.5, normalized=True)
            rows.append({
                "candidate_id": candidate_id, "source_id": config["source_id"], "route_class": route_class,
                "evidence_class": evidence, "observation_status": "remote_sensing_not_field_measured",
                "clear_width_m_low": round(wl, 3), "clear_width_m_central": round(wc, 3), "clear_width_m_high": round(wh, 3),
                "running_slope_low": round(sl, 5), "running_slope_central": round(sc, 5), "running_slope_high": round(sh, 5),
                "cross_slope_low": round(cl, 5), "cross_slope_central": round(cc, 5), "cross_slope_high": round(ch, 5),
                "width_method": width_method, "slope_method": "public_bare_earth_lidar_dtm_2m_or_1m_quantiles",
                "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
                "verification_status": "analytical_proxy_not_accessibility_survey", "geometry": part,
            })
            diameter_central = min(wc, 4.0)
            turn_rows.append({
                "candidate_id": candidate_id + "-TURN", "path_candidate_id": candidate_id, "source_id": config["source_id"],
                "evidence_class": evidence, "observation_status": "remote_sensing_not_field_measured",
                "clear_diameter_m_low": round(max(0.0, diameter_central * 0.80), 3),
                "clear_diameter_m_central": round(diameter_central, 3),
                "clear_diameter_m_high": round(min(8.0, diameter_central * 1.20), 3),
                "diameter_method": "route_midpoint_clear_width_capped_at_4m", "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
                "verification_status": "surface_and_obstruction_verification_required", "geometry": destination.buffer(diameter_central / 2.0),
            })
    paths = gpd.GeoDataFrame(rows, geometry="geometry", crs=crs) if rows else empty("path_candidates", crs)
    turns = gpd.GeoDataFrame(turn_rows, geometry="geometry", crs=crs) if turn_rows else empty("turning_space_candidates", crs)
    if city == "Chicago" and not sidewalks.empty:
        sidewalks["source_id"] = "CHI-DATA-77CN-6X4C"
        sidewalks["width_m_proxy"] = sidewalks.geometry.map(polygon_minor_width)
        sidewalks["evidence_class"] = "official_sidewalk_geometry"
        sidewalks["observation_status"] = "public_geometry_not_current_field_measured"
        sidewalks = sidewalks[["source_id", "width_m_proxy", "evidence_class", "observation_status", "geometry"]]
    return paths, turns, sidewalks


def build(city: str) -> Dict[str, Any]:
    config = CONFIG[city]
    boundary = gpd.read_file(config["world"], layer=config["boundary_layer"]).to_crs(config["crs"]).geometry.iloc[0]
    array, transform, raster_crs, _ = read_raster(config["dtm"])
    from pyproj import CRS
    if CRS.from_user_input(raster_crs).to_2d() != CRS.from_user_input(config["crs"]):
        raise ValueError(f"{city}: DTM horizontal CRS {raster_crs} does not match {config['crs']}")
    paths, turns, sidewalks = route_rows(city, boundary, array, transform, config)
    sources = gpd.GeoDataFrame([
        {"source_id": config["source_id"], "source_url": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs" if city == "London" else "https://planetarycomputer.microsoft.com/dataset/3dep-lidar-dtm", "retrieved": "2026-08-07", "claim_boundary": "DTM-derived slope proxy; not an accessibility survey.", "geometry": boundary},
        {"source_id": "CHI-DATA-77CN-6X4C" if city == "Chicago" else "LON-OSM-TRANSPORT-20260806", "source_url": "https://data.cityofchicago.org/d/77cn-6x4c" if city == "Chicago" else "https://www.openstreetmap.org/", "retrieved": "2026-08-07", "claim_boundary": "Public path geometry proxy; current clear width and obstruction status require verification.", "geometry": boundary},
    ], crs=config["crs"])
    output = config["output"]
    if output.exists():
        output.unlink()
    write_dataframe(paths, output, layer="path_candidates", driver="GPKG")
    write_dataframe(turns, output, layer="turning_space_candidates", driver="GPKG", append=True)
    write_dataframe(sidewalks, output, layer="sidewalk_polygons", driver="GPKG", append=True)
    write_dataframe(sources, output, layer="source_footprints", driver="GPKG", append=True)
    return {
        "city": city, "output": str(output.relative_to(ROOT)), "output_sha256": sha256(output),
        "path_candidates": int(len(paths)), "turning_space_candidates": int(len(turns)),
        "sidewalk_polygons": int(len(sidewalks)), "dtm_sha256": sha256(config["dtm"]),
        "sidewalk_clip_sha256": sha256(config["sidewalks"]) if city == "Chicago" else None,
        "central_clear_width_m": {
            "minimum": round(float(paths["clear_width_m_central"].min()), 3),
            "median": round(float(paths["clear_width_m_central"].median()), 3),
            "maximum": round(float(paths["clear_width_m_central"].max()), 3),
        } if not paths.empty else None,
        "central_running_slope": {
            "minimum": round(float(paths["running_slope_central"].min()), 5),
            "median": round(float(paths["running_slope_central"].median()), 5),
            "maximum": round(float(paths["running_slope_central"].max()), 5),
        } if not paths.empty else None,
        "central_cross_terrain_gradient": {
            "minimum": round(float(paths["cross_slope_central"].min()), 5),
            "median": round(float(paths["cross_slope_central"].median()), 5),
            "maximum": round(float(paths["cross_slope_central"].max()), 5),
        } if not paths.empty else None,
        "central_turning_candidates_at_least_1_525m": int((turns["clear_diameter_m_central"] >= 1.525).sum()) if not turns.empty else 0,
        "central_turning_candidates_below_1_525m": int((turns["clear_diameter_m_central"] < 1.525).sum()) if not turns.empty else 0,
        "cross_slope_resolution_warning": (
            "The 2m DTM gives cross-terrain gradient, not path-surface cross-slope; cells are wider than many sidewalks."
            if city == "Chicago" else
            "The 1m DTM gives cross-terrain gradient, not a measured paved-surface cross-slope."
        ),
        "claim_boundary": "Analytical no-field proxy only; not a field, ADA, BS, engineering, or legal compliance survey.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=("London", "Chicago", "all"), default="all")
    args = parser.parse_args()
    cities = ["London", "Chicago"] if args.city == "all" else [args.city]
    reports = [build(city) for city in cities]
    report_path = OUTPUT / "london_chicago_accessibility_completeness.json"
    report_path.write_text(json.dumps({"generated": "2026-08-07", "cities": reports}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
