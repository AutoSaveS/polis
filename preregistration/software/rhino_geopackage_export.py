#!/usr/bin/env python3
"""Convert a Rhino/Grasshopper layer bundle into the POLIS design GeoPackage.

Rhino/Grasshopper can export each layer as GeoJSON while preserving the
returned user-text attributes.  This converter is the controlled bridge to a
single GeoPackage consumed by ``experiment1_evaluator.py``.  It never invents
geometry, CRS, slope, height, budget, or provenance values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable

import geopandas as gpd
import pandas as pd
from pyogrio import list_layers, write_dataframe


REQUIRED_LAYERS = (
    "accessible_network",
    "green_entrances",
    "required_destinations",
    "turning_spaces",
    "usable_spaces",
    "shade_footprints",
    "design_objects",
)
EXPECTED_TYPES = {
    "accessible_network": {"LineString", "MultiLineString"},
    "green_entrances": {"Point", "MultiPoint"},
    "required_destinations": {"Point", "MultiPoint"},
    "turning_spaces": {"Polygon", "MultiPolygon"},
    "usable_spaces": {"Polygon", "MultiPolygon"},
    "shade_footprints": {"Polygon", "MultiPolygon"},
    "design_objects": {"Polygon", "MultiPolygon", "Point", "MultiPoint", "LineString", "MultiLineString"},
}
EMPTY_GEOMETRY_TYPE = {
    "accessible_network": "LineString",
    "green_entrances": "Point",
    "required_destinations": "Point",
    "turning_spaces": "Polygon",
    "usable_spaces": "Polygon",
    "shade_footprints": "Polygon",
    "design_objects": "Polygon",
}
REQUIRED_FIELDS = {
    "accessible_network": {"clear_width_m", "running_slope", "cross_slope", "provenance_reference"},
    "green_entrances": {"provenance_reference"},
    "required_destinations": {"required_destination_id", "provenance_reference"},
    "turning_spaces": {"required_destination_id", "provenance_reference"},
    "usable_spaces": {"provenance_reference"},
    "shade_footprints": {"month_day", "local_solar_time", "provenance_reference"},
    "design_objects": {
        "object_id", "design_domain", "resource_class", "source_need_ids", "provenance_reference"
    },
}
ALLOWED_CRS = {"EPSG:32651", "EPSG:27700", "EPSG:26916"}


class ExportError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_geojson(path: Path, layer: str, analysis_crs: str) -> gpd.GeoDataFrame:
    if not path.is_file():
        raise ExportError("{}: missing GeoJSON file {}".format(layer, path))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError("{}: invalid GeoJSON: {}".format(layer, exc))
    if raw.get("type") != "FeatureCollection":
        raise ExportError("{}: input must be a GeoJSON FeatureCollection".format(layer))
    features = raw.get("features")
    if not isinstance(features, list):
        raise ExportError("{}: features must be an array".format(layer))
    rows = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ExportError("{}[{}]: invalid Feature".format(layer, index))
        geometry = feature.get("geometry")
        if geometry is not None:
            rows.append({"type": "Feature", "geometry": geometry, "properties": feature.get("properties") or {}})
    if rows:
        frame = gpd.GeoDataFrame.from_features(rows, crs=analysis_crs)
    else:
        declared = raw.get("polis_fields", [])
        if not isinstance(declared, list) or any(not isinstance(value, str) for value in declared):
            raise ExportError("{}: empty layers require a polis_fields string array".format(layer))
        frame = gpd.GeoDataFrame(
            pd.DataFrame(columns=list(dict.fromkeys(declared)) + ["geometry"]),
            geometry="geometry",
            crs=analysis_crs,
        )
    return frame


def validate_frame(frame: gpd.GeoDataFrame, layer: str, analysis_crs: str) -> None:
    if str(frame.crs).upper() != analysis_crs.upper():
        raise ExportError("{}: CRS {} does not match {}".format(layer, frame.crs, analysis_crs))
    missing = sorted(REQUIRED_FIELDS[layer] - set(frame.columns))
    if missing:
        raise ExportError("{}: missing required fields {}".format(layer, missing))
    geometry_types = {str(value) for value in frame.geometry.geom_type.dropna()}
    invalid_types = sorted(geometry_types - EXPECTED_TYPES[layer])
    if invalid_types:
        raise ExportError("{}: unexpected geometry types {}".format(layer, invalid_types))
    if not frame.empty:
        invalid = frame.geometry.is_empty | (~frame.geometry.is_valid)
        if bool(invalid.any()):
            raise ExportError("{}: invalid or empty geometry present".format(layer))
    for field in REQUIRED_FIELDS[layer]:
        values = frame[field].fillna("").astype(str).str.strip()
        if bool((values == "").any()):
            raise ExportError("{}: required field '{}' contains blank values".format(layer, field))
    if layer == "design_objects":
        if frame["object_id"].astype(str).duplicated().any():
            raise ExportError("design_objects: duplicate object_id")
        allowed = {"vegetation", "hardscape", "hydrology", "furniture", "activity", "ecology"}
        unknown = sorted(set(frame["resource_class"].astype(str)) - allowed)
        if unknown:
            raise ExportError("design_objects: unknown resource_class {}".format(unknown))
    if layer in {"required_destinations", "turning_spaces"}:
        if layer == "required_destinations" and frame["required_destination_id"].astype(str).duplicated().any():
            raise ExportError("required_destinations: duplicate required_destination_id")


def write_layer(frame: gpd.GeoDataFrame, output: Path, layer: str, overwrite: bool) -> None:
    write_dataframe(
        frame,
        output,
        layer=layer,
        driver="GPKG",
        geometry_type=EMPTY_GEOMETRY_TYPE[layer] if frame.empty else None,
        append=not overwrite,
    )


def convert(input_dir: Path, output: Path, analysis_crs: str, overwrite: bool = False) -> Dict[str, Any]:
    if analysis_crs not in ALLOWED_CRS:
        raise ExportError("analysis_crs must be one of {}".format(sorted(ALLOWED_CRS)))
    if output.exists() and not overwrite:
        raise ExportError("output exists; pass --overwrite only for a generated dry-run/formal output")
    if output.exists():
        output.unlink()
    frames: Dict[str, gpd.GeoDataFrame] = {}
    for layer in REQUIRED_LAYERS:
        frame = read_geojson(input_dir / (layer + ".geojson"), layer, analysis_crs)
        validate_frame(frame, layer, analysis_crs)
        frames[layer] = frame
    output.parent.mkdir(parents=True, exist_ok=True)
    for layer in REQUIRED_LAYERS:
        write_layer(frames[layer], output, layer, overwrite=(layer == REQUIRED_LAYERS[0]))
    observed = {str(row[0]) for row in list_layers(output)}
    if set(REQUIRED_LAYERS) - observed:
        raise ExportError("GeoPackage is missing layers {}".format(sorted(set(REQUIRED_LAYERS) - observed)))
    return {
        "status": "exported",
        "analysis_crs": analysis_crs,
        "layers": {layer: int(len(frame)) for layer, frame in frames.items()},
        "design_geopackage": str(output),
        "design_geopackage_sha256": sha256_file(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--analysis-crs", required=True, choices=sorted(ALLOWED_CRS))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        result = convert(args.input_dir, args.output, args.analysis_crs, args.overwrite)
    except (ExportError, OSError, ValueError) as exc:
        print("EXPORT_FAILED: {}".format(exc))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
