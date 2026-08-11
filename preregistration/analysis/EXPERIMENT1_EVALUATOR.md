# Experiment 1 spatial evaluator

The evaluator computes the five registered outcomes without filling missing
evidence. It supports CPython 3.9.7 and reads one design GeoPackage plus two
optional row-level evidence CSV files.

## Design GeoPackage contract

All geometry must use the matching city world-model CRS.

- `accessible_network`: noded LineString features with complete
  `clear_width_m`, `running_slope`, and `cross_slope` values.
- `required_destinations`: Point features with unique
  `required_destination_id` and nonblank `provenance_reference`. Every point
  must lie within 0.10 m of the submitted accessible network.
- `turning_spaces`: Polygon features keyed by `required_destination_id`, with
  nonblank `provenance_reference`. At least one polygon for each destination
  must contain the 1.525 m clear circle centred on that destination. This
  supersedes the 1.50 m common value wherever circular turning is required.
- `green_entrances`: Point features representing connected entrances to the
  qualifying usable green space.
- `usable_spaces`: Polygon features used as the shade denominator.
- `shade_footprints`: Polygon features with `month_day` and
  `local_solar_time`. Exactly the 12 registered combinations are required:
  21 June, 21 July, and 21 August at 10:00, 12:00, 14:00, and 16:00 local solar
  time. These polygons must be exported from explicit design geometry; the
  evaluator does not infer missing object heights.
- `design_objects`: Polygon features with `resource_class`, `design_domain`,
  and a nonblank `provenance_reference`. Different design-domain footprints
  may overlap by no more than 0.01 m2 in total. Allowed resource values and
  frozen weights are in
  `world_model/metadata/normalized_resource_cost_catalog.csv`.

The accessible network must already be topologically noded at intersections.
The evaluator snaps origins and entrances to the nearest submitted node and
uses shortest-path distance. It does not add crossings or infer accessibility.

## Evidence CSV contracts

`need_results.csv` requires `need_id,status,evidence_reference`. Every frozen
need for the scenario must be present with `status` equal to `pass` or `fail`.
`not_evaluable` makes `P_ret` not evaluable rather than reducing its
denominator.

`constraint_results.csv` requires
`constraint_id,status,evidence_reference`. Status is `pass`, `fail`, or
`not_evaluable`. It must contain every scored city row in
`constraints/site_constraints.csv` plus `unresolved_critical_conflicts`.
Blank evidence references and unregistered IDs are rejected. Project-level
regulatory entries marked `not_evaluable` are excluded from `I_impl`; shared
route, turning, overlap, provenance, conflict, and resource predicates cannot
be excluded. Missing shared evidence makes `I_impl` not evaluable. Any
evaluable hard failure sets `I_impl` to zero; otherwise the score is the pass
proportion among evaluable non-hard predicates (or one when none apply).

## Cross-device Rhino/Grasshopper handoff

Rhino 8 and Grasshopper may run on a separate fixed workstation. That device
must export the seven layers above, the Rhino/Grasshopper/plugin versions,
SHA-256 values for every `.gh`, `.ghx`, and `.3dm` input, the design GeoPackage
hash, CRS, UTC export time, operator code, and any failure log. The local
analysis machine needs only the frozen GeoPackage and its completed handoff
record; it does not need Rhino installed.

## Run

```bash
python3 preregistration/analysis/experiment1_evaluator.py \
  --scenario-id SUZ-GE-B \
  --workflow POLIS \
  --design path/to/design.gpkg \
  --need-results path/to/need_results.csv \
  --constraint-results path/to/constraint_results.csv \
  --output path/to/outcomes.json
```

The output reports a value and evaluation status for each metric. The
`all_five_evaluated` flag is true only when every metric has sufficient
evidence.
