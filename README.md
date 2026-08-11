# POLIS · multi-agent planning on real geography

A research demo of a multi-agent urban-planning pipeline — **sense a street,
negotiate its needs, govern what gets built** — rendered on real geography
with [deck.gl](https://deck.gl) + [MapLibre](https://maplibre.org).

Three cases run through the same pipeline, each on frozen OpenStreetMap
geometry with a locally packaged CARTO Dark Matter vector style and
3D-extruded buildings:

- **Chicago** — selected New ERA Trail corridor segment (OSM way `624189839`)
  with its study-derived 40 m analytical envelope and live movement simulation
- **London** — Mitre Yard brownfield (OSM way `49601059`), multi-constraint case
- **Suzhou** — pocket retrofit parcel (OSM way `741252447`), low-complexity anchor

The interface is a workflow demonstrator. Its R1-R4 records, heat/vulnerability
fields, live movement metrics and controlled implementation deviation are
frozen illustrative inputs or outputs, not resident observations or completed
Experiment 1 results.

## Run

```bash
npm install
npm run dev        # http://localhost:5173
```

## What is computed (not scripted)

- **Conflict Detection** — pairwise distances in metres (spatial), overlapping
  construction windows (timing), and the budget line (funding).
- **Equity Review** — every protected group checked against an adjustable
  access floor.
- **Orchestrator** — greedy budget allocation, protected needs first, with
  floor enforcement that reallocates from non-protected needs.
- **Design** — trees and benches scale with the money that actually reached
  them; the heat field contracts with built canopy.
- **Feedback** — pedestrians re-evaluate routes by role-weighted utility;
  heat exposure is accumulated per frame from moving agents.
- **Lifecycle review** — the as-built alignment is compared against the
  approved design and flags oversight.

Drag the **budget** and **equity floor** sliders at any step — the whole
pipeline recomputes and re-renders in real time. `Export run` downloads the
full pipeline state, decision trace and live metrics as JSON.

## Structure

| file | role |
|---|---|
| `src/scenario.ts` | the three cases in real lng/lat (needs, zones, paths) |
| `src/pipeline.ts` | pure pipeline: conflicts / equity / orchestration |
| `src/sim.ts` | pedestrian & vehicle simulation + per-frame metrics |
| `src/mapLayers.ts` | deck.gl layer factory (heat, conflicts, greenway…) |
| `src/copy.ts` | stage copy shown in the UI |
| `src/App.tsx` | app shell: map, camera choreography, panels |

Basemap: CARTO Dark Matter (© OpenStreetMap contributors, © CARTO).
