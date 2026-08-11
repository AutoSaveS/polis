# Rhino dry-run QA report

Audit date: 2026-08-10

## Verdict

`GENERATOR_DRY_RUN_VERIFIED; SPATIAL_INTEGRATION_DRY_RUN_VERIFIED`

The 9 August spatial-integration rerun resolves every blocking defect recorded
for the first GeoPackage. This is accepted as cross-device dry-run evidence; it
remains synthetic practice output and is not a formal Experiment 1 result.

## Verified items

- Workstation `RHINO-M1-01` remains `VERIFIED_ON_FIXED_WORKSTATION`, using
  Rhino `8.15.25019.13002`, Grasshopper `1.0.0008`, and QGIS Desktop LTR
  `3.44.12`.
- The six generator rows remain `PASS`. All 13 returned `.gh`, `.ghx`, and
  `.3dm` files match the recorded SHA-256 values; no generator changed.
- `rhino_export_record.json` passes schema version `1.1.0`, and every listed
  source-file hash matches the returned file.
- The accepted GeoPackage SHA-256 is
  `94a6c24e5ddb906b4fd286583bd5df59ec3975b0599622abfca2c3f9f21a4005`.
- The returned ZIP SHA-256 is
  `4a0eef3d30e1357f8c426d0c347286db3051ff8d68c71155c79ef2ffde7557bd`.
- All seven required layers are non-empty, valid, and genuinely use
  `EPSG:32651`. Their combined centroid transforms to approximately
  `120.58659 E, 31.28715 N`; all geometry lies within the registered Suzhou
  coordinate envelope used for this synthetic integration test.
- `accessible_network` is a LineString centreline. The entrance and required
  destination are on its nodes; the usable space touches the network.
- `turning_spaces` matches destination `DRYRUN-DEST-01`, covers that point, and
  preserves a 1.525 m circular clear space.
- `shade_footprints` contains exactly the frozen 12 combinations for 21 June,
  21 July, and 21 August at 10:00, 12:00, 14:00, and 16:00 local solar time.
  All 12 footprints intersect the usable space.
- `design_objects` contains seven unique objects and all six resource classes:
  vegetation, hardscape, hydrology, furniture, activity, and ecology.
- SQLite reports `integrity_check=ok`; the analysis-machine validation uses
  GeoPandas 0.14.4, Shapely 2.0.7, and Fiona 1.10.1.

## Claim boundary

This pass validates the synthetic Rhino-to-GeoPackage integration contract. It
does not establish formal-scenario completion, legal compliance, permission,
cost accuracy, surveyed existing conditions, or construction readiness.
