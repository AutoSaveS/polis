#!/usr/bin/env python3
"""Derive auditable London and Chicago height layers from public LiDAR.

The products are remote-sensing derivatives, not field measurements.  Building
height is summarized from pixels inside public building footprints.  Tree
crowns are connected components of height-above-ground pixels outside those
footprints and therefore remain candidates rather than confirmed individual
trees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyogrio import write_dataframe
from rasterio.features import geometry_mask, shapes
from scipy import ndimage
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
RASTER = ROOT / "world_model/raster"
RAW = ROOT / "world_model/raw"
OUTPUT = ROOT / "world_model/auxiliary"

CITY = {
    "London": {
        "code": "LON",
        "crs": "EPSG:27700",
        "world": ROOT / "world_model/vector/lon_world_model.gpkg",
        "boundary_layer": "site_geometry",
        "surface": RASTER / "lon_ea_lidar_dsm_1m.tif",
        "terrain": RASTER / "lon_ea_lidar_dtm_1m.tif",
        "vegetation": RASTER / "lon_ea_vom_2022_1m.tif",
        "output": OUTPUT / "london_public_height_proxy.gpkg",
        "building_source": "EA-LIDAR-COMPOSITE-DSM-DTM-1M",
        "tree_source": "EA-VOM-2022-1M",
    },
    "Chicago": {
        "code": "CHI",
        "crs": "EPSG:26916",
        "world": ROOT / "world_model/vector/chi_world_model.gpkg",
        "boundary_layer": "analysis_boundary",
        "hag": RASTER / "chi_usgs_3dep_hag_2019_2m.tif",
        "official_buildings": RAW / "chicago_city_building_footprints_2026-08-06.geojson",
        "output": OUTPUT / "chicago_public_height_proxy.gpkg",
        "building_source": "CHI-DATA-SYP8-UEZG+USGS-3DEP-HAG-2019",
        "tree_source": "USGS-3DEP-HAG-2019",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_array(dataset: rasterio.io.DatasetReader) -> np.ndarray:
    array = dataset.read(1).astype("float64")
    invalid = ~np.isfinite(array)
    if dataset.nodata is not None:
        invalid |= np.isclose(array, dataset.nodata)
    array[invalid] = np.nan
    return array


def pixel_values(
    array: np.ndarray,
    transform: rasterio.Affine,
    geometry: Any,
) -> np.ndarray:
    inside = geometry_mask([geometry], array.shape, transform, invert=True)
    values = array[inside & np.isfinite(array)]
    return values[values >= 0.0]


def height_summary(values: np.ndarray) -> Tuple[float, float, float, int]:
    if values.size == 0:
        return np.nan, np.nan, np.nan, 0
    return (
        float(np.quantile(values, 0.50)),
        float(np.quantile(values, 0.90)),
        float(np.quantile(values, 0.95)),
        int(values.size),
    )


def write_gpkg(path: Path, layers: Iterable[Tuple[str, gpd.GeoDataFrame]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    for index, (name, frame) in enumerate(layers):
        write_dataframe(frame, path, layer=name, driver="GPKG", append=index > 0)


def component_crowns(
    height: np.ndarray,
    transform: rasterio.Affine,
    boundary: Any,
    buildings: gpd.GeoDataFrame,
    crs: str,
    city_code: str,
    source_id: str,
    threshold_m: float,
    minimum_area_m2: float,
    maximum_area_m2: float = 1000.0,
) -> gpd.GeoDataFrame:
    boundary_pixels = geometry_mask([boundary], height.shape, transform, invert=True)
    building_pixels = geometry_mask(
        list(buildings.geometry), height.shape, transform, invert=True
    ) if not buildings.empty else np.zeros(height.shape, dtype=bool)
    candidates = (
        np.isfinite(height)
        & (height >= threshold_m)
        & boundary_pixels
        & ~building_pixels
    )
    labels, count = ndimage.label(candidates, structure=np.ones((3, 3), dtype=int))
    rows = []
    sequence = 0
    for label_id in range(1, count + 1):
        mask = labels == label_id
        area = float(mask.sum() * abs(transform.a * transform.e))
        # Very large connected components in a narrow corridor are normally
        # elevated infrastructure or merged built surfaces, not defensible
        # individual/stand-level crown candidates.
        if area < minimum_area_m2 or area > maximum_area_m2:
            continue
        values = height[mask]
        values = values[np.isfinite(values)]
        if values.size == 0:
            continue
        polygons = [shape(geometry) for geometry, value in shapes(mask.astype("uint8"), mask=mask, transform=transform) if value == 1]
        if not polygons:
            continue
        geometry = max(polygons, key=lambda item: item.area).intersection(boundary)
        if geometry.is_empty:
            continue
        sequence += 1
        low, central, high, pixels = height_summary(values)
        rows.append({
            "candidate_id": f"{city_code}-LIDAR-CROWN-{sequence:04d}",
            "source_id": source_id,
            "evidence_class": "lidar_derived",
            "observation_status": "remote_sensing_not_field_measured",
            "height_m_low": round(low, 3),
            "height_m_central": round(central, 3),
            "height_m_high": round(high, 3),
            "height_pixel_count": pixels,
            "crown_area_m2": round(float(geometry.area), 3),
            "extraction_method": f"connected_component_hag_ge_{threshold_m:g}m_outside_buildings",
            "formal_use_rule": "central_with_mandatory_low_high_sensitivity",
            "engineering_or_compliance_use": "prohibited",
            "geometry": geometry,
        })
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


def source_footprint(boundary: Any, crs: str, rows: list[dict[str, str]]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame([{**row, "geometry": boundary} for row in rows], crs=crs)


def london() -> Dict[str, Any]:
    config = CITY["London"]
    boundary_frame = gpd.read_file(config["world"], layer=config["boundary_layer"]).to_crs(config["crs"])
    boundary = boundary_frame.geometry.iloc[0]
    buildings = gpd.read_file(config["world"], layer="buildings").to_crs(config["crs"])
    buildings = gpd.clip(buildings, boundary).reset_index(drop=True)

    with rasterio.open(config["surface"]) as dsm_source, rasterio.open(config["terrain"]) as dtm_source, rasterio.open(config["vegetation"]) as vom_source:
        dsm = valid_array(dsm_source)
        dtm = valid_array(dtm_source)
        if dsm.shape != dtm.shape or dsm_source.transform != dtm_source.transform:
            raise ValueError("London DSM and DTM grids are not aligned")
        ndsm = dsm - dtm
        ndsm[(ndsm < 0.0) | ~np.isfinite(ndsm)] = np.nan
        vom = valid_array(vom_source)
        building_rows = []
        for index, row in buildings.iterrows():
            values = pixel_values(ndsm, dsm_source.transform, row.geometry)
            low, central, high, pixels = height_summary(values)
            levels = pd.to_numeric(pd.Series([row.get("building_levels")]), errors="coerce").iloc[0]
            method = "ea_lidar_dsm_minus_dtm_quantiles"
            evidence = "lidar_derived"
            if not np.isfinite(central) or central <= 0.5:
                if pd.notna(levels) and float(levels) > 0:
                    low, central, high = float(levels) * 2.7, float(levels) * 3.0, float(levels) * 3.6
                    method = "osm_levels_conversion_sensitivity"
                    evidence = "derived_proxy"
                else:
                    low = central = high = np.nan
                    method = "not_evaluable_no_valid_height_pixels_or_levels"
                    evidence = "not_evaluable"
            building_rows.append({
                "building_id": f"LON-OSM-{row.get('osm_id', index)}",
                "source_id": config["building_source"],
                "source_building_levels": None if pd.isna(levels) else float(levels),
                "evidence_class": evidence,
                "observation_status": "remote_sensing_not_field_measured",
                "height_m_low": None if not np.isfinite(low) else round(low, 3),
                "height_m_central": None if not np.isfinite(central) else round(central, 3),
                "height_m_high": None if not np.isfinite(high) else round(high, 3),
                "height_pixel_count": pixels,
                "height_method": method,
                "engineering_or_compliance_use": "prohibited",
                "geometry": row.geometry,
            })
        height_buildings = gpd.GeoDataFrame(building_rows, crs=config["crs"])
        crowns = component_crowns(
            vom,
            vom_source.transform,
            boundary,
            height_buildings,
            config["crs"],
            config["code"],
            config["tree_source"],
            threshold_m=2.0,
            minimum_area_m2=4.0,
        )

    footprint = source_footprint(boundary, config["crs"], [
        {"source_id": config["building_source"], "source_url": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs", "retrieved": "2026-08-06", "claim_boundary": "LiDAR-derived height; not field survey."},
        {"source_id": config["tree_source"], "source_url": "https://environment.data.gov.uk/spatialdata/vegetation-object-model/wcs", "retrieved": "2026-08-06", "claim_boundary": "Remote-sensing crown candidates; not confirmed individual trees."},
    ])
    write_gpkg(config["output"], [("building_heights", height_buildings), ("tree_crowns", crowns), ("source_footprints", footprint)])
    return report_for("London", config, height_buildings, crowns)


def chicago() -> Dict[str, Any]:
    config = CITY["Chicago"]
    boundary_frame = gpd.read_file(config["world"], layer=config["boundary_layer"]).to_crs(config["crs"])
    boundary = boundary_frame.geometry.iloc[0]
    buildings = gpd.read_file(config["official_buildings"]).to_crs(config["crs"])
    buildings = gpd.clip(buildings, boundary).reset_index(drop=True)

    with rasterio.open(config["hag"]) as source:
        hag = valid_array(source)
        building_rows = []
        for index, row in buildings.iterrows():
            values = pixel_values(hag, source.transform, row.geometry)
            low, central, high, pixels = height_summary(values)
            stories = pd.to_numeric(pd.Series([row.get("stories")]), errors="coerce").iloc[0]
            method = "usgs_3dep_hag_quantiles"
            evidence = "lidar_derived"
            if not np.isfinite(central) or central <= 0.5:
                if pd.notna(stories) and float(stories) > 0:
                    low, central, high = float(stories) * 2.7, float(stories) * 3.0, float(stories) * 3.6
                    method = "official_stories_conversion_sensitivity"
                    evidence = "derived_proxy"
                else:
                    low = central = high = np.nan
                    method = "not_evaluable_no_valid_height_pixels_or_stories"
                    evidence = "not_evaluable"
            building_rows.append({
                "building_id": str(row.get("bldg_id") or f"CHI-OFFICIAL-{index}"),
                "source_id": config["building_source"],
                "official_stories": None if pd.isna(stories) else float(stories),
                "official_year_built": str(row.get("year_built") or ""),
                "official_status": str(row.get("bldg_statu") or ""),
                "evidence_class": evidence,
                "observation_status": "remote_sensing_not_field_measured",
                "height_m_low": None if not np.isfinite(low) else round(low, 3),
                "height_m_central": None if not np.isfinite(central) else round(central, 3),
                "height_m_high": None if not np.isfinite(high) else round(high, 3),
                "height_pixel_count": pixels,
                "height_method": method,
                "engineering_or_compliance_use": "prohibited",
                "geometry": row.geometry,
            })
        height_buildings = gpd.GeoDataFrame(building_rows, crs=config["crs"])
        crowns = component_crowns(
            hag,
            source.transform,
            boundary,
            height_buildings,
            config["crs"],
            config["code"],
            config["tree_source"],
            threshold_m=2.5,
            minimum_area_m2=12.0,
        )

    footprint = source_footprint(boundary, config["crs"], [
        {"source_id": "CHI-DATA-SYP8-UEZG", "source_url": "https://data.cityofchicago.org/d/syp8-uezg", "retrieved": "2026-08-06", "claim_boundary": "Official footprint and attribute data; stories are not measured height."},
        {"source_id": config["tree_source"], "source_url": "https://planetarycomputer.microsoft.com/dataset/3dep-lidar-hag", "retrieved": "2026-08-06", "claim_boundary": "2019 2 m LiDAR-derived height and crown candidates; not field survey."},
    ])
    write_gpkg(config["output"], [("building_heights", height_buildings), ("tree_crowns", crowns), ("source_footprints", footprint)])
    return report_for("Chicago", config, height_buildings, crowns)


def report_for(city: str, config: Dict[str, Any], buildings: gpd.GeoDataFrame, crowns: gpd.GeoDataFrame) -> Dict[str, Any]:
    evaluable = pd.to_numeric(buildings["height_m_central"], errors="coerce").notna()
    lidar = buildings["evidence_class"].eq("lidar_derived")
    proxy = buildings["evidence_class"].eq("derived_proxy")
    context_buildings = gpd.read_file(config["world"], layer="buildings")
    context_trees = gpd.read_file(config["world"], layer="trees")
    inputs = {}
    for key in ("surface", "terrain", "vegetation", "hag", "official_buildings"):
        path = config.get(key)
        if path is not None:
            inputs[str(path.relative_to(ROOT))] = sha256(path)
    return {
        "city": city,
        "count_scope": "Formal registered site/analysis boundary; context counts are reported separately.",
        "world_model_context_building_count": int(len(context_buildings)),
        "world_model_context_mapped_tree_count": int(len(context_trees)),
        "output": str(config["output"].relative_to(ROOT)),
        "output_sha256": sha256(config["output"]),
        "formal_boundary_building_footprints": int(len(buildings)),
        "buildings_with_evaluable_height": int(evaluable.sum()),
        "buildings_lidar_derived": int(lidar.sum()),
        "buildings_levels_or_stories_proxy": int(proxy.sum()),
        "buildings_not_evaluable": int((~evaluable).sum()),
        "lidar_tree_crown_candidates": int(len(crowns)),
        "tree_crown_area_m2": round(float(crowns.geometry.area.sum()), 3) if not crowns.empty else 0.0,
        "input_sha256": inputs,
        "claim_boundary": "Remote-sensing analytical input only; not a field, arboricultural, accessibility, cadastral, or engineering survey.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=("London", "Chicago", "all"), default="all")
    args = parser.parse_args()
    reports = []
    if args.city in ("London", "all"):
        reports.append(london())
    if args.city in ("Chicago", "all"):
        reports.append(chicago())
    output = OUTPUT / "london_chicago_public_height_completeness.json"
    output.write_text(json.dumps({"generated": "2026-08-06", "cities": reports}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "cities": reports}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
