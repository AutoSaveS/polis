# POLIS Rhino 8 Workstation SOP

For a bounded package that can be sent directly to the workstation operator,
use `RHINO_DRY_RUN_HANDOFF.md` together with this SOP.

## Purpose and boundary

This SOP turns the six registered generator source scripts into real Rhino and
Grasshopper assets on the fixed design workstation.  It applies to
vegetation, hardscape, hydrology, furniture, activity zones, and ecological
features.  It does not authorise changing frozen scenario inputs, assigning
legal applicability, or inferring missing heights, budgets, or participant
needs.

The scripts in this directory are source assets.  They are not substitutes for
the actual `.gh`, `.ghx`, and `.3dm` files required for a formal Experiment 1
run.  Create those files on the fixed Rhino workstation and record their
actual hashes before the non-study dry run.

## One-time workstation setup

1. Copy the complete `preregistration/software/rhino_generators/` directory to
   a stable, access-controlled workstation folder.  Keep the copied directory
   intact; the common module is required by all six scripts.
2. Start Rhino 8.  Record the exact Rhino build and operating system in
   `software/rhino_workstation_assets.json`.  Open Grasshopper and record its
   build and every installed plugin used in a study definition.  Do not list a
   plugin merely because it is installed.
3. Add the copied `rhino_generators` directory to the Python search path for
   the Rhino 8 Python 3 Script component.  Verify that
   `import polis_generator_common` succeeds.  Use a Python 3 component, not a
   legacy component that cannot import the module.
4. Create one Grasshopper definition for each registered domain.  Give the
   definitions these exact names:

   - `POLIS_vegetation_v1.gh`
   - `POLIS_hardscape_v1.gh`
   - `POLIS_hydrology_v1.gh`
   - `POLIS_furniture_v1.gh`
   - `POLIS_activity_v1.gh`
   - `POLIS_ecology_v1.gh`

5. In each definition, add a Python 3 component with inputs `records` and
   `context`, call the corresponding module's `generate(records, context)`,
   and expose its list of geometry/attribute records as the output.  Connect
   the approved input geometry only.  Do not use random placement components.

   For example, the vegetation definition's component body is:

   ```python
   from vegetation_generator import generate

   output_records = generate(records, context)
   geometry = [item["geometry"] for item in output_records]
   attributes = [item["attributes"] for item in output_records]
   ```

   Substitute the module name for the other five domains.  Expose
   `geometry` and `attributes` as separate outputs so the attributes are not
   lost before baking or GeoPackage export.
6. Save each definition as both `.gh` and `.ghx`.  Save a Rhino document named
   `POLIS_workstation_master_v1.3dm` containing only the project layers,
   geometry conventions, and a link or documentation panel for the six
   definitions.  It must not contain a formal scenario output.

## Required input record format

Every input record is a dictionary.  All records need:

```text
geometry, source_id, source_need_ids
```

`source_need_ids` is a nonempty list of frozen need IDs from the loaded
scenario package.  The shared `context` dictionary must contain:

```text
scenario_id, analysis_crs, units="m", provenance_reference, generator_version
```

The full field contract is in
`generator_contract.json`.  Geometry is supplied in the scenario's projected
analysis CRS: EPSG:32651 for Suzhou, EPSG:27700 for London, and EPSG:26916 for
Chicago.  Ensure Rhino model units are metres before creating any geometry.

Domain-specific fields are as follows.

| Domain | Required explicit design inputs | Output |
| --- | --- | --- |
| Vegetation | planting type, species status, planting curve or point; canopy radius and height when shade eligible | planting zone or canopy circle |
| Hardscape | route centreline, clear width, running slope, cross slope, role, accessible flag | closed route footprint |
| Hydrology | closed zone, hydraulic type, design storage, drainage destination | hydrology zone |
| Furniture | insertion point, width, depth, orientation, type, clearance review flag | oriented footprint |
| Activity | closed usable-space curve, use type, accessible connection ID, unobstructed flag | activity zone |
| Ecology | closed zone, habitat type, native/adapted fraction, protected flag | ecological zone |

The scripts reject incomplete records.  A rejected record is a process failure,
not permission to substitute a plausible value.

## Per-run procedure

1. Open one frozen scenario package from
   `preregistration/experiment1_scenario_packages/`.  Verify its input hash,
   world-model hash, scenario ID, seed, and city CRS against the run manifest.
2. Load the matching world model and create only the workflow-specific design
   inputs permitted by the baseline SOP.  Preserve original input layers.
3. Populate each generator's `records` input.  The source IDs and need IDs
   must be copied from the frozen package; do not create new IDs.
4. Run all six generators.  Review the output audit fields.  Resolve an input
   error by correcting the recorded input or mark the run as failed; never
   bypass the provenance check.
5. Convert/bake accepted geometry to the project layers.  Copy every output
   attribute into the baked object's user text.  The final `design_objects`
   export must contain at least the required attributes listed in the contract.
6. Produce the seven layers required by the handoff contract:
   `accessible_network`, `green_entrances`, `required_destinations`,
   `turning_spaces`, `usable_spaces`, `shade_footprints`, and `design_objects`.
   Do not emit `shade_footprints` unless the required explicit height/crown and
   12 time-step solar inputs are available.  An absent layer is correctly
   evaluated as `not_evaluable`.
7. Export one GeoPackage in the frozen analysis CRS.  Do not relabel a DXF,
   Shapefile, or Rhino file as a GeoPackage.
8. Complete `rhino_export_record.json` from the project template, include the
   hash of each actual source definition and the exported GeoPackage, then
   validate the record with the project export schema on the analysis machine.

## Asset inventory and hash recording

After all six definitions and the master document exist, run the following on
the Rhino workstation from the project root.  Replace the three placeholder
values with observed information; no licence key or API key belongs in the
record.

```powershell
py preregistration/software/rhino_generators/collect_workstation_assets.py `
  --asset-root D:\POLIS\RhinoAssets `
  --workstation-id RHINO-WS-01 `
  --operating-system "Windows 11 Pro 23H2" `
  --rhino-version "8.<observed build>" `
  --grasshopper-version "<observed build>" `
  --operator-id OP01
```

The command refuses missing or duplicate required assets and writes
`preregistration/software/rhino_workstation_assets.json`.  Review the output,
then record it as a source asset in each formal Rhino handoff record.

Before transfer to the Rhino workstation, the analysis machine can run
`test_generator_contract.py` and `test_generator_simulation.py`.  The latter
uses a Shapely geometry shim to exercise the six input/output paths and
rejection rules.  It confirms source-code feasibility only; it does not replace
the Rhino 8 dry run or validate Grasshopper serialization.

## Non-study acceptance test

Use a practice scenario that is not one of the 36 registered scenarios.  The
test passes only when all six definition files and the master `.3dm` exist,
every source hash is recorded, the output `design_objects` features retain the
required provenance fields, and one exported GeoPackage validates against the
handoff schema.  Do not include the test output in Experiment 1.
