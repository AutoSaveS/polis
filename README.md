# POLIS · multi-agent planning on real geography

A research demo of a multi-agent urban-planning pipeline — **sense a street,
negotiate its needs, govern what gets built** — rendered on real Chicago
geography with [deck.gl](https://deck.gl) + [MapLibre](https://maplibre.org).

This is the deck.gl successor to the hand-drawn SVG prototype
(`POLIS_Product_Prototype_v9.html`). All pipeline logic was ported 1:1; the
scenario now lives on the S Kedzie Ave corridor in Little Village, with a dark
vector basemap and 3D-extruded buildings.

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
| `src/scenario.ts` | corridor data in real lng/lat (needs, zones, paths) |
| `src/pipeline.ts` | pure pipeline: conflicts / equity / orchestration |
| `src/sim.ts` | pedestrian & vehicle simulation + per-frame metrics |
| `src/mapLayers.ts` | deck.gl layer factory (heat, conflicts, greenway…) |
| `src/copy.ts` | stage copy shown in the UI |
| `src/App.tsx` | app shell: map, camera choreography, panels |

Basemap: CARTO Dark Matter (© OpenStreetMap contributors, © CARTO).
