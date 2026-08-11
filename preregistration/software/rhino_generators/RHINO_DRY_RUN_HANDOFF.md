# POLIS Rhino Dry-Run Handoff

This handoff is for a non-study software and export check.  The recipient is
not being asked to produce an Experiment 1 result.  Use only synthetic practice
geometry and the ID below.

## Give the Rhino operator

Copy these files or the complete project subdirectory:

```text
preregistration/software/rhino_generators/
preregistration/software/rhino_workstation_assets.template.json
preregistration/software/rhino_export_record.template.json
preregistration/software/rhino_export_contract.schema.json
```

The directory contains the six generator scripts, the frozen generator
contract, the asset-inventory command, and the workstation SOP.  The operator
needs a licensed Rhino 8 installation with Grasshopper and Python 3 support.
Do not provide an API key, participant data, identity-linkage files, or any
formal Experiment 1 outcome file.

## Practice run specification

Use this exact non-study identifier:

```text
DRYRUN-SUZ-GE-20260806-01
```

Use metre units and genuine `EPSG:32651` coordinates. Do not create geometry
around Rhino's `(0,0)` origin and merely label it `EPSG:32651`; translate the
practice geometry into the Suzhou test extent so the cross-device integration
check can detect CRS/georeferencing errors. The practice provenance reference
is:

```text
dryrun:DRYRUN-SUZ-GE-20260806-01
```

Create a small synthetic boundary and arrange non-overlapping practice
features.  The following values are fixed for this software check; they are
not city measurements, resident needs, legal thresholds, or study outcomes:

| Domain | Practice input |
| --- | --- |
| Vegetation | one tree point with explicit canopy radius 2.0 m and height 7.0 m; one planting polygon |
| Hardscape | one 10 m centreline, clear width 2.0 m, running slope 0.03, cross slope 0.01 |
| Hydrology | one closed 4 m by 3 m zone, explicit storage 4.5 m3 and named synthetic outfall |
| Furniture | one point, footprint 1.2 m by 0.6 m, orientation 30 degrees |
| Activity | one closed 10 m by 10 m usable zone, linked to the synthetic route |
| Ecology | one closed 15 m by 14 m zone, native/adapted fraction 0.80, protected=true |

Use IDs such as `DRYRUN-SOURCE-01` and `DRYRUN-N01`; do not copy formal need
IDs into this practice run.  The operator must supply every required field in
`generator_contract.json`.  Missing inputs must be reported as failures, not
filled with assumptions.

## Procedure

1. Copy `rhino_generators/` to a stable workstation directory and open Rhino 8
   with model units in metres.
2. Confirm that a Python 3 Grasshopper component can run
   `import polis_generator_common`.
3. Create one Grasshopper definition for each domain using the corresponding
   module's `generate(records, context)` function.  Save each definition as
   both `.gh` and `.ghx` with the names specified in the SOP.
4. Create `POLIS_workstation_master_v1.3dm` containing the project layer
   conventions only; do not save formal scenario outputs into this master file.
5. Run all six definitions with the practice inputs.  Bake or export the
   returned geometry and preserve every returned attribute in the export.
6. Prepare the seven required layers according to the geometry and field
   contract below. If a GIS/GeoPackage plugin is used,
   record its exact name and version.  Otherwise export an intermediate
   geometry-and-attribute format and state that GeoPackage conversion remains
   pending; do not rename another format to `.gpkg`.
7. Complete `rhino_export_record.json` with the practice run ID, actual source
   file hashes, CRS, and failure log.
8. Run `collect_workstation_assets.py` with the real workstation and software
   versions.  It must refuse to complete if any required `.gh`, `.ghx`, or
   `.3dm` file is absent.

## Return to the study team

Return the following files in one dated folder:

```text
POLIS_vegetation_v1.gh          POLIS_vegetation_v1.ghx
POLIS_hardscape_v1.gh           POLIS_hardscape_v1.ghx
POLIS_hydrology_v1.gh           POLIS_hydrology_v1.ghx
POLIS_furniture_v1.gh            POLIS_furniture_v1.ghx
POLIS_activity_v1.gh             POLIS_activity_v1.ghx
POLIS_ecology_v1.gh              POLIS_ecology_v1.ghx
POLIS_workstation_master_v1.3dm
rhino_workstation_assets.json
rhino_export_record.json
process_log.csv
dry_run_design.gpkg               (only if genuinely created)
failure_log.txt                   (empty only if no failures occurred)
```

Also report the Rhino build, Grasshopper build, plugin versions, operator code,
elapsed time, and any definition that failed. Screenshots may document the run
but do not replace the source files, hashes, GeoPackage, or export record.

## Seven-layer spatial contract

Layer names alone are not sufficient. The dry-run GeoPackage must pass
`preregistration/software/rhino_geopackage_export.py::validate_frame`:

| Layer | Geometry | Required content |
| --- | --- | --- |
| `accessible_network` | noded LineString | `clear_width_m`, `running_slope`, `cross_slope`, `provenance_reference`; export the centreline, not the buffered hardscape footprint |
| `green_entrances` | Point | at least one point on a network node and `provenance_reference` |
| `required_destinations` | Point | `required_destination_id`, `provenance_reference`; point must be on a network node |
| `turning_spaces` | Polygon | matching `required_destination_id`, `provenance_reference`; preserve the explicit clear circle |
| `usable_spaces` | Polygon | activity/usable polygon and `provenance_reference` |
| `shade_footprints` | Polygon | all 12 registered `month_day` and `local_solar_time` combinations plus `provenance_reference` |
| `design_objects` | generated geometry | `object_id`, `design_domain`, `resource_class`, `source_need_ids`, `provenance_reference` |

Empty practice layers do not demonstrate end-to-end integration. The route,
entrance, destination, turning-space, usable-space, and shade features must be
spatially connected in the synthetic design. The buffered route footprint
belongs in `design_objects`; it must not be duplicated as the
`accessible_network` centreline.

## Acceptance rule

Generator execution and spatial integration are separate results. Generator
execution passes when all six definitions run and the real source hashes and
provenance are recorded. Spatial integration passes only when the GeoPackage
hash matches the handoff, coordinates overlap the intended test extent, and
all seven layers pass the geometry/field contract above. No missing value may
be imputed. The returned folder must remain outside the formal Experiment 1
output directories.
