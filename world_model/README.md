# POLIS three-city world-model package

This package contains the reproducible base spatial inputs for Experiment 1.
It distinguishes observed public-source data from study-derived objects and
from inputs that still require documented real evidence.

## Frozen sites

- SUZ: Xutai Road grass parcel, OSM way 741252447.
- LON: Mitre Yard, OSM way 49601059.
- CHI: selected New ERA Trail axis, OSM way 624189839, with a frozen
  analytical envelope extending 20 m from each side of the axis.

The Suzhou and London OSM ways are polygons. The Chicago source way is a line;
its 40 m nominal-width envelope is a study-derived analysis boundary with an
area of approximately 40,502.20 m2. It is not evidence of ownership, parcel
extent, legal right-of-way, or permit jurisdiction.

## Coordinate systems

Raw coordinates use EPSG:4326. Metric analysis layers use EPSG:32651 for
Suzhou, EPSG:27700 for London, and EPSG:26916 for Chicago. Each city has its
own GeoPackage because metric coordinates are not interchangeable across the
three jurisdictions.

## Contents

- `raw/`: immutable Overpass JSON snapshots, including the OSM base timestamp.
- `vector/`: per-city GeoPackages with the site geometry, transport network,
  buildings, green/blue features, mapped trees, activity/amenity features,
  mapped and derived access candidates, accessibility attributes, barriers,
  and 100 m analysis-origin locations.
- `raster/`: clipped Copernicus GLO-30 elevation context plus frozen public
  LiDAR clips for the London and Chicago analytical boundaries. Copernicus
  GLO-30 is not used for object height. The Environment Agency DSM/DTM/VOM and
  USGS 3DEP HAG clips support explicitly labelled `lidar_derived` analytical
  heights; none is an engineering or field survey.
- `metadata/site_registry.csv`: geometry, CRS, site measures, timestamps,
  hashes, and height-tag completeness.
- `metadata/solar_evaluation_schedule.csv`: registered dates, local solar
  times, time weights, site coordinates, and time zones.
- `metadata/scenario_budget_register.csv`: all 36 scenario multipliers under
  the frozen unitless resource-index policy (100 baseline; 80 under the
  registered 20% stress condition). This is not a monetary budget or cost
  estimate.
- `metadata/regulatory_trigger_register.csv`: one row per registered
  constraint. Missing project-level evidence must never be coded as pass or
  not applicable.
- `validation/world_model_validation.json`: machine-readable readiness audit.
- `metadata/manifest.sha256`: file-level integrity hashes.

## Provenance rule

OSM-mapped features are observations from the frozen public snapshot. Derived
access candidates are geometric intersections or axis endpoints and require
verification. Analysis origins are fixed 100 m points within the registered
1 km catchment. Their weights are observed values extracted from the frozen
JRC GHSL GHS-POP R2023A E2025 100 m tiles; equal weights are not used. Missing
existing building or tree heights are not silently imputed. London and Chicago
Existing shade may use the separate public-LiDAR analytical layers with
low/central/high sensitivity; stories-to-height conversion remains
`derived_proxy`, and missing values remain `not_evaluable`. Suzhou uses its
separate image-derived low/central/high package and remains `not_measured`.
Project-level regulatory triggers lacking evidence are coded
`not_evaluable` and excluded from the scoring denominator, never inferred as
pass or not applicable.

## Rebuild

Run from this directory:

```bash
python3 build_world_model.py
```

Do not rerun after registration without recording an amendment: live OSM data
may change. The committed raw snapshots, not the live API, are the canonical
inputs for the registered run.

## Population status

The JRC GHSL source, exact tile URLs, source-archive SHA-256 values, clipped
raster hashes, and extraction counts are recorded in
`metadata/population_source_register.csv`. The verified tiles are `R6_C30`
(Suzhou), `R3_C19` (London), and `R5_C11` (Chicago). The retained GeoPackages
contain nonmissing GHSL values for all 340, 350, and 523 analysis origins,
respectively. Large source ZIPs are excluded from the package; the clipped
GeoTIFFs and exact provenance records are retained.

## Readiness boundary

`validation/world_model_validation.json` marks Experiment 1 as
computationally ready under the registered analytical policies. It separately
marks engineering implementation readiness as false because object-height
coverage, monetary budgets, legal corridor boundaries, and project-level
permit applicability have not been established.

Rhino 8/Grasshopper geometry is produced on a separate fixed workstation. It
is transferred as a hashed seven-layer design GeoPackage with a JSON handoff
record conforming to
`preregistration/software/rhino_export_contract.schema.json`. The local GIS
machine does not require Rhino; it verifies the handoff and calculates the five
registered outcomes in Python 3.9.7.
