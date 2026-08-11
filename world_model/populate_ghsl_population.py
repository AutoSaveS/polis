#!/usr/bin/env python3
"""Populate analysis-origin weights from JRC GHSL population tiles.

The large source ZIPs are downloaded to a temporary directory and are not
retained in the replication package. Exact URLs and source hashes are saved
in metadata/population_source_register.csv; the clipped GeoTIFFs and updated
origin layers are retained.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
from shapely.ops import transform
from pyproj import Transformer


ROOT = Path(__file__).resolve().parent
VECTOR = ROOT / "vector"
RASTER = ROOT / "raster"
METADATA = ROOT / "metadata"
VALIDATION = ROOT / "validation"

TILE_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/"
TILES = {
    "SUZ": "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C30.zip",
    "LON": "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R3_C19.zip",
    "CHI": "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R5_C11.zip",
}
ANALYSIS_CRS = {"SUZ": "EPSG:32651", "LON": "EPSG:27700", "CHI": "EPSG:26916"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "POLIS-reproducible-world-model/1.0"})
    with urllib.request.urlopen(request, timeout=900) as response, path.open("wb") as out:
        shutil.copyfileobj(response, out)


def process_site(site_id: str, archive: Path) -> dict:
    gpkg = VECTOR / f"{site_id.lower()}_world_model.gpkg"
    with zipfile.ZipFile(archive) as zf:
        tif_names = [name for name in zf.namelist() if name.lower().endswith(".tif")]
        if len(tif_names) != 1:
            raise RuntimeError(f"{site_id}: expected one population TIFF, found {tif_names}")
        with tempfile.TemporaryDirectory(prefix=f"polis-{site_id.lower()}-tile-") as unpack:
            zf.extract(tif_names[0], unpack)
            source_tif = Path(unpack) / tif_names[0]
            origins = gpd.read_file(gpkg, layer="analysis_origins")
            origins = origins.to_crs("ESRI:54009")
            catchment = origins.geometry.unary_union.convex_hull.buffer(50)
            with rasterio.open(source_tif) as source:
                source_bounds = source.bounds
                minx, miny, maxx, maxy = catchment.bounds
                overlaps = not (
                    maxx <= source_bounds.left
                    or minx >= source_bounds.right
                    or maxy <= source_bounds.bottom
                    or miny >= source_bounds.top
                )
                if not overlaps:
                    raise RuntimeError(
                        f"{site_id}: GHSL tile does not cover analysis origins; "
                        f"tile={source_bounds}, origins={catchment.bounds}"
                    )
                clipped, clipped_transform = mask(source, [mapping(catchment)], crop=True)
                profile = source.profile.copy()
            clipped_path = RASTER / f"{site_id.lower()}_ghsl_pop_e2025_100m.tif"
            profile.update(
                height=clipped.shape[1],
                width=clipped.shape[2],
                transform=clipped_transform,
                compress="deflate",
            )
            with rasterio.open(clipped_path, "w", **profile) as destination:
                destination.write(clipped)

            values = []
            with rasterio.open(source_tif) as source:
                for point in origins.geometry:
                    value = next(source.sample([(point.x, point.y)]))[0]
                    values.append(float(value) if np.isfinite(value) and value >= 0 else np.nan)

    origins["population_weight"] = values
    origins["population_source_id"] = f"GHSL-POP-E2025-100M-{site_id}"
    origins["weight_status"] = np.where(
        origins["population_weight"].notna(), "REAL_GHSL_PIXEL_VALUE", "ZERO_OR_NODATA_RETAINED_AS_ZERO_OR_NA"
    )
    origins = origins.to_crs(ANALYSIS_CRS[site_id])
    origins.to_file(gpkg, layer="analysis_origins", driver="GPKG")
    return {
        "site_id": site_id,
        "source_id": f"GHSL-POP-E2025-100M-{site_id}",
        "source_url": TILE_BASE + TILES[site_id],
        "archive_sha256": sha256(archive),
        "clipped_raster": clipped_path.relative_to(ROOT).as_posix(),
        "clipped_raster_sha256": sha256(clipped_path),
        "origin_count": int(len(origins)),
        "nonmissing_origin_count": int(origins["population_weight"].notna().sum()),
        "positive_origin_count": int((origins["population_weight"].fillna(0) > 0).sum()),
        "population_sum_at_origins": float(origins["population_weight"].fillna(0).sum()),
        "source_dataset": "GHS-POP R2023A, E2025, Mollweide 54009, 100 m",
        "status": "FROZEN_LOCAL_CLIP_AND_POINT_EXTRACT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="Use pre-downloaded verified ZIP files named suz.zip, lon.zip, and chi.zip.",
    )
    args = parser.parse_args()
    RASTER.mkdir(exist_ok=True)
    METADATA.mkdir(exist_ok=True)
    if args.archive_dir:
        rows = []
        for site_id in TILES:
            archive = args.archive_dir / f"{site_id.lower()}.zip"
            if not archive.exists():
                raise FileNotFoundError(archive)
            with zipfile.ZipFile(archive) as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(f"{site_id}: corrupt archive member {bad}")
            rows.append(process_site(site_id, archive))
    else:
      with tempfile.TemporaryDirectory(prefix="polis-ghsl-download-") as temp:
        rows = []
        for site_id, filename in TILES.items():
            archive = Path(temp) / filename
            download(TILE_BASE + filename, archive)
            rows.append(process_site(site_id, archive))

    pd.DataFrame(rows).to_csv(METADATA / "population_source_register.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    source_register_path = METADATA / "source_register.csv"
    source_register = pd.read_csv(source_register_path)
    source_register = source_register[
        ~source_register["source_id"].astype(str).str.startswith(("POP-", "GHSL-POP-"))
    ].copy()
    population_sources = pd.DataFrame([
        {
            "source_id": row["source_id"],
            "site_id": row["site_id"],
            "dataset": row["source_dataset"],
            "provider": "European Commission Joint Research Centre",
            "url": row["source_url"],
            "retrieved": "2026-08-06",
            "license": "GHSL data licence (see included tile metadata)",
            "role": "A_green and E_equity origin weights",
            "status": row["status"],
            "archive_sha256": row["archive_sha256"],
        }
        for row in rows
    ])
    if "archive_sha256" not in source_register.columns:
        source_register["archive_sha256"] = ""
    source_register = pd.concat([source_register, population_sources], ignore_index=True)
    source_register.to_csv(source_register_path, index=False, quoting=csv.QUOTE_MINIMAL)
    report_path = VALIDATION / "world_model_validation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for site_report in report["sites"]:
        row = next(item for item in rows if item["site_id"] == site_report["site_id"])
        site_report["population"] = row
        site_report["blocking_items"] = [
            item for item in site_report["blocking_items"] if "population" not in item
        ]
    report["global_blocking_items"] = [
        item for item in report["global_blocking_items"] if "population" not in item
    ]
    report["status"] = "BASE_SPATIAL_PACKAGE_BUILT_WITH_REMAINING_BLOCKING_INPUTS"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    registry_path = METADATA / "site_registry.csv"
    registry = pd.read_csv(registry_path)
    for site_id in TILES:
        gpkg = VECTOR / f"{site_id.lower()}_world_model.gpkg"
        registry.loc[registry["site_id"] == site_id, "gpkg_sha256"] = sha256(gpkg)
    registry.to_csv(registry_path, index=False)

    manifest_rows = []
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path.name in {"manifest.sha256", ".DS_Store"}
            or "__pycache__" in path.parts
        ):
            continue
        manifest_rows.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    (METADATA / "manifest.sha256").write_text("\n".join(manifest_rows) + "\n", encoding="ascii")
    print(json.dumps(rows, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
