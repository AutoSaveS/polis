# Three-city no-field data status (updated 2026-08-07)

Counts in the original world-model GeoPackages cover each extraction context.
Counts used by a formal Existing run are clipped to the registered site polygon
(Suzhou and London) or study-defined analysis envelope (Chicago). These two
scopes must not be reported interchangeably.

## Suzhou

- Registered site area: 2,540.05 m2.
- Frozen public layers: 12 transport features, seven green/blue features, and
  340 GHSL-weighted origins.
- The frozen OSM snapshot contains zero buildings, mapped trees, activity
  amenities, entrances, accessibility features, and barriers in the retained
  extraction.
- The separate image-derived package contains 12 tree candidates, one path,
  one activity zone, and one turning-space candidate. It has complete
  `central`, `low`, and `high` Existing packages and five-outcome evidence.
- All image-derived dimensions remain `not_measured`; central results are only
  interpretable together with low/high sensitivity and cannot support an
  engineering or compliance claim.
- The path proxy central/low/high clear widths are 1.79/1.28/2.30 m, the
  corresponding longitudinal slopes are 0.020/0.000/0.050, and cross-slopes
  are 0.015/0.000/0.040. The turning-space diameter is 4.0/1.5/8.0 m. These
  are image-derived scenario values, not measurements.

## London

- Registered Mitre Yard area: 6,473.20 m2.
- The wider context contains 36 OSM buildings (24 with levels/height) and eight
  mapped tree points, but only three building footprints intersect the formal
  site and the eight mapped tree points lie outside it.
- Environment Agency 1 m DSM and DTM provide LiDAR-derived height for all three
  intersecting buildings. The 2022 1 m Vegetation Object Model yields two
  crown candidates (17.524 m2 total) after the height and component-size
  filters.
- Low/central/high Existing packages now include 12 registered solar-time
  shade layers. The height package itself does not infer accessibility fields;
  those are supplied separately by the proxy package described below.
- A separate accessibility proxy package now contains three OSM service-route
  candidates. Central clear-corridor widths range from 8.899 to 9.714 m and
  central turning diameter is 4.0 m; these widths describe geometric clearance
  between mapped obstacles and the boundary, not verified pedestrian pavement
  width. DTM-derived slope is retained only as an analytical terrain proxy.

## Chicago

- Study analysis envelope: 40,502.20 m2, created by buffering the registered
  rail/trail axis by 20 m on each side. It is not a parcel or legal boundary.
- The wider context contains 540 OSM buildings and no mapped OSM trees.
- Twelve City of Chicago official building footprints intersect the formal
  envelope. Ten have evaluable height: seven directly from the 2019 USGS 3DEP
  2 m height-above-ground raster and three from official stories with explicit
  low/central/high conversion. Two remain `not_evaluable`.
- Three non-building LiDAR crown candidates remain after rejecting components
  below 12 m2 or above 1,000 m2; their total footprint is 199.273 m2. The
  rejected very large component is continuous elevated infrastructure, not a
  defensible tree crown.
- Low/central/high Existing packages now include 12 registered solar-time
  shade layers and the separate route proxy layers. Legal/project
  applicability remains outside these remote-sensing inputs.
- The City of Chicago sidewalk polygons yield 14 OSM footway candidates. Their
  central width proxies range from 0.956 to 6.362 m (median 1.992 m), and six
  of the 14 central turning candidates are below the registered 1.525 m test
  diameter. The 2019 2 m DTM gives a median longitudinal terrain gradient of
  0.01994 but a median cross-terrain gradient of 0.21988; the latter is not a
  sidewalk cross-slope measurement because the raster resolution exceeds the
  path width and does not model curbs or surface drainage.

## Claim boundary

The added data make building-height and candidate-canopy shade modelling more
complete without field survey. They do not convert any value into a field,
topographic, arboricultural, cadastral, accessibility, or engineering
measurement. The authoritative machine-readable completeness record is
`london_chicago_public_height_completeness.json`.

The accessibility proxy completeness record is
`london_chicago_accessibility_completeness.json`. Its route and turning layers
are suitable for a no-field computational sensitivity comparison, not for
claiming that an existing route meets ADA, BS 8300, or project permit criteria.
