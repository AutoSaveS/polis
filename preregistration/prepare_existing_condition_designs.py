#!/usr/bin/env python3
"""Build transparent Existing-condition design packages for the three cities.

Existing is a no-intervention reference.  Only observed world-model features
are carried forward.  Missing accessibility dimensions, tree/building heights,
turning spaces, and design provenance remain missing or empty; no geometry is
invented from a centroid or a default assumption.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from pyogrio import list_layers, write_dataframe
from shapely.affinity import translate
from shapely.geometry import GeometryCollection, LineString, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from preregistration.software.rhino_geopackage_export import (
    ALLOWED_CRS,
    EMPTY_GEOMETRY_TYPE,
    REQUIRED_LAYERS,
    validate_frame,
)


WORLD = ROOT / "world_model"
WORLD_FILES = {
    "Suzhou": WORLD / "vector/suz_world_model.gpkg",
    "London": WORLD / "vector/lon_world_model.gpkg",
    "Chicago": WORLD / "vector/chi_world_model.gpkg",
}
CITY_CODES = {"Suzhou": "SUZ", "London": "LON", "Chicago": "CHI"}
CRS_BY_CITY = {"Suzhou": "EPSG:32651", "London": "EPSG:27700", "Chicago": "EPSG:26916"}
SUZHOU_PROXY = ROOT / "world_model/auxiliary/suzhou_image_proxy.gpkg"
PUBLIC_HEIGHT_PROXY = {
    "London": ROOT / "world_model/auxiliary/london_public_height_proxy.gpkg",
    "Chicago": ROOT / "world_model/auxiliary/chicago_public_height_proxy.gpkg",
}
PUBLIC_ACCESS_PROXY = {
    "London": ROOT / "world_model/auxiliary/london_accessibility_proxy.gpkg",
    "Chicago": ROOT / "world_model/auxiliary/chicago_accessibility_proxy.gpkg",
}
SOURCE_ID = "AUX-ESRI-WORLD-IMAGERY-SUZ-20260806"
WALKABLE_HIGHWAYS = {
    "footway", "path", "pedestrian", "cycleway", "living_street", "track", "steps", "corridor"
}
EXCLUDED_WHEELCHAIR = {"no"}


class ExistingBuildError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def layers(path: Path) -> set[str]:
    return {str(row[0]) for row in list_layers(path)}


def read_layer(path: Path, name: str) -> gpd.GeoDataFrame:
    if name not in layers(path):
        return gpd.GeoDataFrame(geometry=[], crs=CRS_BY_CITY["Suzhou"])
    return gpd.read_file(path, layer=name)


def empty_frame(layer: str, crs: str) -> gpd.GeoDataFrame:
    fields = {
        "accessible_network": ["clear_width_m", "running_slope", "cross_slope", "provenance_reference"],
        "green_entrances": ["provenance_reference"],
        "required_destinations": ["required_destination_id", "provenance_reference"],
        "turning_spaces": ["required_destination_id", "provenance_reference"],
        "usable_spaces": ["provenance_reference"],
        "shade_footprints": ["month_day", "local_solar_time", "provenance_reference"],
        "design_objects": ["object_id", "design_domain", "resource_class", "source_need_ids", "provenance_reference"],
    }[layer]
    return gpd.GeoDataFrame(pd.DataFrame(columns=fields + ["geometry"]), geometry="geometry", crs=crs)


def source_reference(site: str, layer: str, row_index: int, row: pd.Series) -> str:
    source = row.get("osm_id", "")
    if pd.isna(source) or str(source).strip() == "":
        source = "row-{}".format(row_index)
    return "existing:{}:{}:{}".format(CITY_CODES[site], layer, source)


def parse_float(value: Any) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    text = str(value).strip().replace("m", "")
    if not text or text in {"-", "unknown", "Unknown", "nan", "None"}:
        return float("nan")
    try:
        result = float(text.rstrip("%"))
    except ValueError:
        return float("nan")
    return result / 100.0 if "%" in str(value) else result


def clipped(frame: gpd.GeoDataFrame, boundary: Any, crs: str) -> gpd.GeoDataFrame:
    if frame.empty:
        return frame.set_crs(crs, allow_override=True)
    if frame.crs is None:
        frame = frame.set_crs(crs, allow_override=True)
    elif str(frame.crs).upper() != crs.upper():
        frame = frame.to_crs(crs)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
    if frame.empty:
        return frame
    return gpd.clip(frame, boundary)


def site_boundary(world_path: Path, site: str) -> tuple[Any, gpd.GeoDataFrame]:
    boundary_layer = "analysis_boundary" if site == "Chicago" else "site_geometry"
    frame = gpd.read_file(world_path, layer=boundary_layer)
    crs = CRS_BY_CITY[site]
    if frame.crs is None:
        frame = frame.set_crs(crs, allow_override=True)
    elif str(frame.crs).upper() != crs.upper():
        frame = frame.to_crs(crs)
    if frame.empty:
        raise ExistingBuildError("{}: boundary layer is empty".format(site))
    return frame.geometry.iloc[0], frame


def build_accessible_network(world_path: Path, site: str, boundary: Any, crs: str) -> gpd.GeoDataFrame:
    frame = clipped(gpd.read_file(world_path, layer="transport_network"), boundary, crs)
    if frame.empty:
        return empty_frame("accessible_network", crs)
    highway = frame.get("highway", pd.Series("", index=frame.index)).fillna("").astype(str).str.lower()
    wheelchair = frame.get("wheelchair", pd.Series("", index=frame.index)).fillna("").astype(str).str.lower()
    frame = frame[highway.isin(WALKABLE_HIGHWAYS) & ~wheelchair.isin(EXCLUDED_WHEELCHAIR)].copy()
    if frame.empty:
        return empty_frame("accessible_network", crs)
    frame["clear_width_m"] = frame.get("width", pd.Series(np.nan, index=frame.index)).map(parse_float)
    frame["running_slope"] = frame.get("incline", pd.Series(np.nan, index=frame.index)).map(parse_float)
    # Cross-slope evidence is not present in the frozen OSM layers.
    frame["cross_slope"] = np.nan
    frame = frame.dropna(subset=["clear_width_m", "running_slope", "cross_slope"]).copy()
    if frame.empty:
        return empty_frame("accessible_network", crs)
    frame["provenance_reference"] = [source_reference(site, "transport_network", i, row) for i, (_, row) in enumerate(frame.iterrows())]
    return frame[["clear_width_m", "running_slope", "cross_slope", "provenance_reference", "geometry"]]


def build_entrances(world_path: Path, site: str, boundary: Any, crs: str) -> gpd.GeoDataFrame:
    if "mapped_access_points" not in layers(world_path):
        return empty_frame("green_entrances", crs)
    frame = clipped(gpd.read_file(world_path, layer="mapped_access_points"), boundary, crs)
    if frame.empty:
        return empty_frame("green_entrances", crs)
    frame["provenance_reference"] = [source_reference(site, "mapped_access_points", i, row) for i, (_, row) in enumerate(frame.iterrows())]
    return frame[["provenance_reference", "geometry"]]


def build_destinations(world_path: Path, site: str, boundary: Any, crs: str) -> gpd.GeoDataFrame:
    if "activity_amenities" not in layers(world_path):
        return empty_frame("required_destinations", crs)
    frame = clipped(gpd.read_file(world_path, layer="activity_amenities"), boundary, crs)
    if frame.empty:
        return empty_frame("required_destinations", crs)
    # Only observed point amenities are destinations; polygon centroids are prohibited.
    frame = frame[frame.geometry.geom_type.isin(["Point", "MultiPoint"])].copy()
    if frame.empty:
        return empty_frame("required_destinations", crs)
    frame["required_destination_id"] = ["EXIST-{}-DEST-{}".format(CITY_CODES[site], i) for i in range(len(frame))]
    frame["provenance_reference"] = [source_reference(site, "activity_amenities", i, row) for i, (_, row) in enumerate(frame.iterrows())]
    return frame[["required_destination_id", "provenance_reference", "geometry"]]


def build_usable_spaces(world_path: Path, site: str, boundary: Any, crs: str) -> gpd.GeoDataFrame:
    if "green_blue" not in layers(world_path):
        return empty_frame("usable_spaces", crs)
    frame = clipped(gpd.read_file(world_path, layer="green_blue"), boundary, crs)
    if frame.empty:
        return empty_frame("usable_spaces", crs)
    frame = frame[frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if frame.empty:
        return empty_frame("usable_spaces", crs)
    frame["provenance_reference"] = [source_reference(site, "green_blue", i, row) for i, (_, row) in enumerate(frame.iterrows())]
    return frame[["provenance_reference", "geometry"]]


def build_empty(layer: str, crs: str) -> gpd.GeoDataFrame:
    return empty_frame(layer, crs)


def proxy_value(row: pd.Series, stem: str, variant: str) -> float:
    if variant == "central":
        field = stem + "_proxy" if stem + "_proxy" in row.index else stem + "_central"
    else:
        field = stem + "_" + variant
    value = row.get(field, np.nan)
    return float(value) if pd.notna(value) else float("nan")


def solar_altitude_azimuth(month_day: str, local_time: str, latitude: float) -> tuple[float, float]:
    month, day = (int(value) for value in month_day.split("-"))
    doy = int(pd.Timestamp(year=2026, month=month, day=day).dayofyear)
    declination = math.radians(23.44 * math.sin(math.radians(360.0 * (284 + doy) / 365.0)))
    hour = float(local_time.split(":")[0]) + float(local_time.split(":")[1]) / 60.0
    hour_angle = math.radians(15.0 * (hour - 12.0))
    lat = math.radians(latitude)
    altitude = math.asin(math.sin(lat) * math.sin(declination) + math.cos(lat) * math.cos(declination) * math.cos(hour_angle))
    azimuth = math.atan2(math.sin(hour_angle), math.cos(hour_angle) * math.sin(lat) - math.tan(declination) * math.cos(lat)) + math.pi
    return altitude, azimuth


def build_proxy_shade(trees: gpd.GeoDataFrame, boundary: Any, variant: str, crs: str) -> gpd.GeoDataFrame:
    rows = []
    latitude = 31.287068393742285
    for month_day in ("06-21", "07-21", "08-21"):
        for local_time in ("10:00", "12:00", "14:00", "16:00"):
            altitude, azimuth = solar_altitude_azimuth(month_day, local_time, latitude)
            shadows = []
            if altitude > 0:
                for _, tree in trees.iterrows():
                    height = proxy_value(tree, "height_m", variant)
                    radius = proxy_value(tree, "crown_radius_m", variant)
                    if not math.isfinite(height) or not math.isfinite(radius):
                        continue
                    length = height / math.tan(altitude)
                    dx = -math.sin(azimuth) * length
                    dy = -math.cos(azimuth) * length
                    crown = tree.geometry.buffer(radius)
                    shadows.append(unary_union([crown, translate(crown, xoff=dx, yoff=dy)]).convex_hull)
            geometry = unary_union(shadows).intersection(boundary) if shadows else GeometryCollection()
            rows.append({
                "month_day": month_day,
                "local_solar_time": local_time,
                "provenance_reference": f"{SOURCE_ID}:shade:{variant}:{month_day}:{local_time}",
                "evidence_class": "image_derived_formal_proxy",
                "observation_status": "not_measured",
                "geometry": geometry,
            })
    return gpd.GeoDataFrame(rows, crs=crs)


def build_public_proxy_shade(
    trees: gpd.GeoDataFrame,
    buildings: gpd.GeoDataFrame,
    boundary: Any,
    variant: str,
    crs: str,
    latitude: float,
    source_id: str,
) -> gpd.GeoDataFrame:
    """Project public LiDAR footprints into the registered solar schedule."""
    rows = []
    for month_day in ("06-21", "07-21", "08-21"):
        for local_time in ("10:00", "12:00", "14:00", "16:00"):
            altitude, azimuth = solar_altitude_azimuth(month_day, local_time, latitude)
            shadows = []
            if altitude > 0:
                items = [(trees, "height_m"), (buildings, "height_m")]
                for frame, stem in items:
                    for _, item in frame.iterrows():
                        height = proxy_value(item, stem, variant)
                        if not math.isfinite(height) or height <= 0:
                            continue
                        footprint = item.geometry
                        length = height / math.tan(altitude)
                        dx = -math.sin(azimuth) * length
                        dy = -math.cos(azimuth) * length
                        shadows.append(unary_union([footprint, translate(footprint, xoff=dx, yoff=dy)]).convex_hull)
            geometry = unary_union(shadows).intersection(boundary) if shadows else GeometryCollection()
            rows.append({
                "month_day": month_day,
                "local_solar_time": local_time,
                "provenance_reference": f"{source_id}:shade:{variant}:{month_day}:{local_time}",
                "evidence_class": "lidar_derived_formal_proxy",
                "observation_status": "remote_sensing_not_field_measured",
                "geometry": geometry,
            })
    return gpd.GeoDataFrame(rows, crs=crs)


def build_public_height_proxy(site: str, boundary: Any, crs: str, variant: str) -> Dict[str, gpd.GeoDataFrame]:
    source_path = PUBLIC_HEIGHT_PROXY[site]
    if not source_path.is_file():
        raise ExistingBuildError("Public height proxy package is missing: {}".format(source_path))
    trees = gpd.read_file(source_path, layer="tree_crowns").to_crs(crs)
    buildings = gpd.read_file(source_path, layer="building_heights").to_crs(crs)
    trees = trees[trees.geometry.notna() & ~trees.geometry.is_empty].copy()
    buildings = buildings[buildings.geometry.notna() & ~buildings.geometry.is_empty].copy()
    object_rows = []
    for index, row in trees.iterrows():
        object_rows.append({
            "object_id": f"{CITY_CODES[site]}-EXIST-LIDAR-TREE-{index:04d}",
            "design_domain": "vegetation",
            "resource_class": "vegetation",
            "source_need_ids": "N03;N05",
            "provenance_reference": f"{row.get('source_id', source_path.name)}:{row.get('candidate_id', index)}:{variant}",
            "evidence_class": "lidar_derived_formal_proxy",
            "observation_status": "remote_sensing_not_field_measured",
            "geometry": row.geometry,
        })
    objects = gpd.GeoDataFrame(object_rows, crs=crs) if object_rows else empty_frame("design_objects", crs)
    return {
        "shade_footprints": build_public_proxy_shade(
            trees, buildings, boundary, variant, crs,
            latitude={"London": 51.5268, "Chicago": 41.7877}[site],
            source_id=f"AUX-PUBLIC-LIDAR-{CITY_CODES[site]}-20260806",
        ),
        "design_objects": objects,
    }


def build_public_access_proxy(site: str, boundary: Any, crs: str, variant: str) -> Dict[str, gpd.GeoDataFrame]:
    source_path = PUBLIC_ACCESS_PROXY[site]
    if not source_path.is_file():
        raise ExistingBuildError("Public accessibility proxy package is missing: {}".format(source_path))
    source_paths = gpd.read_file(source_path, layer="path_candidates").to_crs(crs)
    source_turns = gpd.read_file(source_path, layer="turning_space_candidates").to_crs(crs)
    if source_paths.empty:
        return {}
    rows = []
    destinations = []
    entrances = []
    turning = []
    for index, path in source_paths.iterrows():
        geometry = path.geometry.intersection(boundary)
        if geometry.is_empty or geometry.geom_type != "LineString":
            continue
        candidate_id = str(path["candidate_id"])
        destination_id = f"EXIST-{CITY_CODES[site]}-{candidate_id}-DEST"
        destination = geometry.interpolate(0.5, normalized=True)
        provenance = f"{path.get('source_id', source_path.name)}:{candidate_id}:{variant}"
        for segment_index, segment in enumerate(split_line_at_point(geometry, destination), start=1):
            rows.append({
                "clear_width_m": proxy_value(path, "clear_width_m", variant),
                "running_slope": proxy_value(path, "running_slope", variant),
                "cross_slope": proxy_value(path, "cross_slope", variant),
                "provenance_reference": provenance + f":segment-{segment_index}",
                "evidence_class": str(path.get("evidence_class", "remote_sensing_geometry_proxy")),
                "observation_status": "remote_sensing_not_field_measured",
                "geometry": segment,
            })
        destinations.append({
            "required_destination_id": destination_id,
            "provenance_reference": provenance + ":destination",
            "evidence_class": str(path.get("evidence_class", "remote_sensing_geometry_proxy")),
            "observation_status": "remote_sensing_not_field_measured",
            "geometry": destination,
        })
        entrances.append({
            "provenance_reference": provenance + ":entrance",
            "evidence_class": str(path.get("evidence_class", "remote_sensing_geometry_proxy")),
            "observation_status": "remote_sensing_not_field_measured",
            "geometry": Point(geometry.coords[0]),
        })
        matched = source_turns[source_turns["path_candidate_id"].astype(str) == candidate_id]
        if not matched.empty:
            diameter = proxy_value(matched.iloc[0], "clear_diameter_m", variant)
            turning.append({
                "required_destination_id": destination_id,
                "provenance_reference": provenance + ":turning",
                "evidence_class": str(path.get("evidence_class", "remote_sensing_geometry_proxy")),
                "observation_status": "remote_sensing_not_field_measured",
                "geometry": destination.buffer(diameter / 2.0),
            })
    return {
        "accessible_network": gpd.GeoDataFrame(rows, crs=crs),
        "green_entrances": gpd.GeoDataFrame(entrances, crs=crs),
        "required_destinations": gpd.GeoDataFrame(destinations, crs=crs),
        "turning_spaces": gpd.GeoDataFrame(turning, crs=crs),
    }


def split_line_at_point(line: LineString, point: Point) -> tuple[LineString, LineString]:
    distance = line.project(point)
    coordinates = list(line.coords)
    travelled = 0.0
    for index in range(len(coordinates) - 1):
        start = Point(coordinates[index])
        end = Point(coordinates[index + 1])
        segment_length = start.distance(end)
        if travelled + segment_length >= distance:
            split = line.interpolate(distance)
            split_coordinate = (split.x, split.y)
            return (
                LineString(coordinates[: index + 1] + [split_coordinate]),
                LineString([split_coordinate] + coordinates[index + 1 :]),
            )
        travelled += segment_length
    raise ExistingBuildError("Could not node proxy path at required destination")


def build_suzhou_proxy(world_path: Path, boundary: Any, crs: str, variant: str) -> Dict[str, gpd.GeoDataFrame]:
    if not SUZHOU_PROXY.is_file():
        raise ExistingBuildError("Suzhou image proxy package is missing: {}".format(SUZHOU_PROXY))
    path = gpd.read_file(SUZHOU_PROXY, layer="path_candidates").to_crs(crs)
    trees = gpd.read_file(SUZHOU_PROXY, layer="tree_candidates").to_crs(crs)
    turning_source = gpd.read_file(SUZHOU_PROXY, layer="turning_space_candidates").to_crs(crs)
    activity_source = gpd.read_file(SUZHOU_PROXY, layer="activity_zone_candidates").to_crs(crs)
    if path.empty or trees.empty or turning_source.empty or activity_source.empty:
        raise ExistingBuildError("Suzhou image proxy package has incomplete candidate layers")
    path_row = path.iloc[0]
    path_geometry = path_row.geometry.intersection(boundary)
    destination = path_geometry.interpolate(0.5, normalized=True)
    path_parts = split_line_at_point(path_geometry, destination)
    path_frame = gpd.GeoDataFrame([
        {
            "clear_width_m": proxy_value(path_row, "clear_width_m", variant),
            "running_slope": proxy_value(path_row, "running_slope", variant),
            "cross_slope": proxy_value(path_row, "cross_slope", variant),
            "provenance_reference": f"{SOURCE_ID}:path:{variant}:{index}",
            "evidence_class": "image_derived_formal_proxy",
            "observation_status": "not_measured",
            "geometry": geometry,
        }
        for index, geometry in enumerate(path_parts, start=1)
    ], crs=crs)
    entrance = gpd.GeoDataFrame([{
        "provenance_reference": f"{SOURCE_ID}:entrance:{variant}",
        "evidence_class": "image_derived_formal_proxy",
        "observation_status": "not_measured",
        "geometry": Point(path_geometry.coords[0]),
    }], crs=crs)
    destination_frame = gpd.GeoDataFrame([{
        "required_destination_id": f"EXIST-SUZ-PROXY-DEST-{variant}",
        "provenance_reference": f"{SOURCE_ID}:destination:{variant}",
        "evidence_class": "image_derived_formal_proxy",
        "observation_status": "not_measured",
        "geometry": destination,
    }], crs=crs)
    turning_row = turning_source.iloc[0]
    turning = gpd.GeoDataFrame([{
        "required_destination_id": f"EXIST-SUZ-PROXY-DEST-{variant}",
        "provenance_reference": f"{SOURCE_ID}:turning:{variant}",
        "evidence_class": "image_derived_formal_proxy",
        "observation_status": "not_measured",
        "geometry": destination.buffer(proxy_value(turning_row, "clear_diameter_m", variant) / 2.0),
    }], crs=crs)
    # ``design_objects`` represents non-overlapping ground-resource footprints,
    # not the aerial extent of tree crowns.  Keep crown geometry for shade
    # modelling above, then remove the proxy path surface from the vegetation
    # footprint so the evaluator does not double-count the same ground area.
    path_width = proxy_value(path_row, "clear_width_m", variant)
    path_object_geometry = path_geometry.buffer(path_width / 2.0, cap_style=2)
    tree_objects = []
    for index, (_, tree) in enumerate(trees.iterrows(), start=1):
        radius = proxy_value(tree, "crown_radius_m", variant)
        tree_objects.append({
            "object_id": f"SUZ-EXIST-TREE-{variant}-{index:02d}",
            "design_domain": "vegetation",
            "resource_class": "vegetation",
            "source_need_ids": "SUZ-N05",
            "provenance_reference": f"{SOURCE_ID}:tree:{tree['candidate_id']}:{variant}",
            "evidence_class": "image_derived_formal_proxy",
            "observation_status": "not_measured",
            "geometry": tree.geometry.buffer(radius).difference(path_object_geometry),
        })
    vegetation_geometry = unary_union([row["geometry"] for row in tree_objects])
    activity_geometry = activity_source.geometry.iloc[0].intersection(boundary)
    activity_geometry = activity_geometry.difference(vegetation_geometry).difference(path_object_geometry)
    object_rows = tree_objects + [
        {
            "object_id": f"SUZ-EXIST-PATH-{variant}-01",
            "design_domain": "hardscape",
            "resource_class": "hardscape",
            "source_need_ids": "SUZ-N01;SUZ-N02",
            "provenance_reference": f"{SOURCE_ID}:path:{variant}",
            "evidence_class": "image_derived_formal_proxy",
            "observation_status": "not_measured",
            "geometry": path_object_geometry,
        },
        {
            "object_id": f"SUZ-EXIST-ACTIVITY-{variant}-01",
            "design_domain": "activity",
            "resource_class": "activity",
            "source_need_ids": "SUZ-N06",
            "provenance_reference": f"{SOURCE_ID}:activity:{variant}",
            "evidence_class": "image_derived_formal_proxy",
            "observation_status": "not_measured",
            "geometry": activity_geometry,
        },
    ]
    design_objects = gpd.GeoDataFrame(object_rows, crs=crs)
    return {
        "accessible_network": path_frame,
        "green_entrances": entrance,
        "required_destinations": destination_frame,
        "turning_spaces": turning,
        "shade_footprints": build_proxy_shade(trees, boundary, variant, crs),
        "design_objects": design_objects,
    }


def write_design(frames: Dict[str, gpd.GeoDataFrame], output: Path, crs: str) -> None:
    if output.exists():
        output.unlink()
    for index, layer in enumerate(REQUIRED_LAYERS):
        frame = frames[layer]
        validate_frame(frame, layer, crs)
        write_dataframe(
            frame,
            output,
            layer=layer,
            driver="GPKG",
            geometry_type=EMPTY_GEOMETRY_TYPE[layer] if frame.empty else None,
            append=index > 0,
        )
    observed = {str(row[0]) for row in list_layers(output)}
    if set(REQUIRED_LAYERS) != observed.intersection(set(REQUIRED_LAYERS)):
        raise ExistingBuildError("Existing design did not produce all required layers")


def build(site: str, output: Path, proxy_variant: str = "observed") -> Dict[str, Any]:
    if site not in WORLD_FILES:
        raise ExistingBuildError("site must be Suzhou, London, or Chicago")
    world_path = WORLD_FILES[site]
    crs = CRS_BY_CITY[site]
    boundary, _ = site_boundary(world_path, site)
    frames = {
        "accessible_network": build_accessible_network(world_path, site, boundary, crs),
        "green_entrances": build_entrances(world_path, site, boundary, crs),
        "required_destinations": build_destinations(world_path, site, boundary, crs),
        "turning_spaces": build_empty("turning_spaces", crs),
        "usable_spaces": build_usable_spaces(world_path, site, boundary, crs),
        "shade_footprints": build_empty("shade_footprints", crs),
        "design_objects": build_empty("design_objects", crs),
    }
    if site == "Suzhou" and proxy_variant != "observed":
        frames.update(build_suzhou_proxy(world_path, boundary, crs, proxy_variant))
    elif site in PUBLIC_HEIGHT_PROXY and proxy_variant != "observed":
        frames.update(build_public_height_proxy(site, boundary, crs, proxy_variant))
        frames.update(build_public_access_proxy(site, boundary, crs, proxy_variant))
    write_design(frames, output, crs)
    return {
        "status": "existing_condition_exported",
        "workflow": "EXISTING",
        "site": site,
        "analysis_crs": crs,
        "world_model": str(world_path.relative_to(ROOT)),
        "world_model_sha256": sha256_file(world_path),
        "design_geopackage": str(output),
        "design_geopackage_sha256": sha256_file(output),
        "layer_counts": {layer: int(len(frame)) for layer, frame in frames.items()},
        "evidence_boundary": "observed site_geometry or Chicago author-defined analytical boundary",
        "input_mode": proxy_variant,
        "missing_rule": "Observed mode does not impute missing evidence. Central/low/high modes use public LiDAR or image-derived auxiliary packages and remain explicitly remote_sensing_not_field_measured; missing accessibility evidence is not imputed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=sorted(WORLD_FILES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suzhou-proxy-variant", choices=("observed", "central", "low", "high"), default="observed")
    args = parser.parse_args()
    try:
        report = build(args.site, args.output, args.suzhou_proxy_variant)
    except (ExistingBuildError, OSError, ValueError) as exc:
        print("EXISTING_BUILD_FAILED: {}".format(exc))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
