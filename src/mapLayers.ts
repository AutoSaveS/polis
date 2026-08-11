/* deck.gl layer factory — all data-driven from the pipeline result. */
import type { Layer } from '@deck.gl/core';
import {
  ArcLayer, PathLayer, PolygonLayer, ScatterplotLayer, TextLayer,
} from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import { PathStyleExtension } from '@deck.gl/extensions';

import { ellipse, mulberry32, type LngLat } from './geo';
import { SCENARIO, ROLE_LABEL, type Need, type Role } from './scenario';
import type { Pipeline } from './pipeline';
import type { Car, Ped } from './sim';

export type ViewMode = 'mobility' | 'conflict' | 'equity';

const YELLOW: [number, number, number] = [228, 208, 133];
const MINT: [number, number, number] = [170, 198, 173];
const BROWN: [number, number, number] = [170, 119, 96];
const RED: [number, number, number] = [225, 88, 87];
const STRAW: [number, number, number] = [220, 49, 47];
const CANOPY: [number, number, number] = [136, 154, 81];
const CANOPY_HI: [number, number, number] = [213, 223, 193];
const GRASS: [number, number, number] = [143, 167, 99];
const GRASS_LIGHT: [number, number, number] = [179, 199, 137];
const CURB: [number, number, number] = [233, 227, 213];
const PANEL_BG: [number, number, number, number] = [13, 19, 25, 225];

const ROLE_COLOR: Record<Role, [number, number, number]> = {
  elder: [237, 165, 164],
  wheel: [225, 88, 87],
  family: [168, 185, 119],
  commuter: [193, 193, 196],
  bike: [120, 149, 171],
};

// grapefruit ramp for the heat field
const HEAT_RANGE: Array<[number, number, number, number]> = [
  [246, 213, 199, 0], [240, 183, 159, 70], [235, 153, 119, 120],
  [224, 112, 65, 170], [191, 80, 34, 205], [134, 58, 26, 235],
];

const FONT = 'Inter, system-ui, -apple-system, sans-serif';
const dashExt = new PathStyleExtension({ dash: true });

export interface HeatPoint { pos: LngLat; w: number }

/** Deterministic scatter inside each heat ellipse; radii contract with the heat factor. */
export function makeHeatPoints(hf: number): HeatPoint[] {
  const rand = mulberry32(1234);
  const pts: HeatPoint[] = [];
  for (const z of SCENARIO.heat) {
    for (let i = 0; i < 70; i++) {
      const gx = (rand() + rand() - 1) * 0.9;   // triangular ≈ gaussian
      const gy = (rand() + rand() - 1) * 0.9;
      pts.push({
        pos: [
          z.center[0] + (gx * z.rx * hf) / 82920,
          z.center[1] + (gy * z.ry * hf) / 111132,
        ],
        w: z.severity,
      });
    }
  }
  return pts;
}

export interface PickInfo { title: string; desc: string }

export interface LayerOpts {
  step: number;
  viewMode: ViewMode;
  pipeline: Pipeline;
  peds: Ped[];
  cars: Car[];
  heatPoints: HeatPoint[];
  frame: number;
  onPick: (info: PickInfo) => void;
}

function needDesc(n: Need, P: Pipeline): string {
  const d = P.decisions.find(x => x.id === n.id);
  return `${ROLE_LABEL[n.type]} · needs "${n.label}" · est. $${n.cost.toFixed(1)}M · access now ${Math.round(n.baseAccess * 100)}%` +
    (d ? ` · orchestrator: ${d.action.toUpperCase()}${d.alloc ? ` $${d.alloc}M` : ''}` : '');
}

export function buildLayers(o: LayerOpts): Layer[] {
  const { step, viewMode, pipeline: P } = o;
  const N = SCENARIO.needs;
  const layers: (Layer | false)[] = [];
  const showNeeds = step >= 1;
  const midRoute = SCENARIO.route[Math.floor(SCENARIO.route.length / 2)];

  /* Study-derived 40 m analytical envelope and frozen OSM centreline. */
  layers.push(
    new PathLayer({
      id: 'analytical-envelope', data: [SCENARIO.route],
      getPath: d => d, getColor: [228, 208, 133, 24],
      getWidth: SCENARIO.analyticalEnvelopeM, widthUnits: 'meters',
      capRounded: true, jointRounded: true,
    }),
    new PathLayer({
      id: 'osm-centreline', data: [SCENARIO.route],
      getPath: d => d, getColor: [228, 208, 133, 145],
      getWidth: 2.2, widthUnits: 'meters',
      capRounded: true, jointRounded: true,
    }),
  );

  /* heat field — always visible, contracts with built canopy */
  layers.push(new HeatmapLayer<HeatPoint>({
    id: 'heat',
    data: o.heatPoints,
    getPosition: d => d.pos,
    getWeight: d => d.w,
    radiusPixels: 62,
    intensity: 1.15,
    threshold: 0.06,
    colorRange: HEAT_RANGE,
    aggregation: 'SUM',
    updateTriggers: { getPosition: o.heatPoints },
  }));

  /* vulnerability zones — conflict view */
  if (viewMode === 'conflict') {
    layers.push(new PolygonLayer({
      id: 'vul',
      data: SCENARIO.vul,
      getPolygon: d => ellipse(d.center, d.rx, d.ry),
      getFillColor: d => [...STRAW, 26 + d.severity * 30] as [number, number, number, number],
      getLineColor: [...STRAW, 210] as [number, number, number, number],
      getLineWidth: 2, lineWidthUnits: 'pixels',
      stroked: true, filled: true, pickable: false,
    }));
  }

  /* greenway — built geometry scales with the actual allocation */
  if (step >= 5) {
    layers.push(
      new PathLayer({
        id: 'greenway-curb', data: [SCENARIO.route],
        getPath: d => d, getColor: [...CURB, 235] as [number, number, number, number],
        getWidth: 21, widthUnits: 'meters', capRounded: true, jointRounded: true,
      }),
      new PathLayer({
        id: 'greenway-grass', data: [SCENARIO.route],
        getPath: d => d, getColor: [...GRASS, 245] as [number, number, number, number],
        getWidth: 16, widthUnits: 'meters', capRounded: true, jointRounded: true,
      }),
      new PathLayer({
        id: 'greenway-stripe', data: [SCENARIO.route],
        getPath: d => d, getColor: [...GRASS_LIGHT, 220] as [number, number, number, number],
        getWidth: 6, widthUnits: 'meters', capRounded: true, jointRounded: true,
      }),
    );
    const trees = SCENARIO.designPoints.slice(0, P.treeCount);
    layers.push(
      new ScatterplotLayer({
        id: 'tree-canopy', data: trees,
        getPosition: d => d, getRadius: 8.5, radiusUnits: 'meters', radiusMinPixels: 4,
        getFillColor: [...CANOPY, 255] as [number, number, number, number],
        getLineColor: [56, 64, 35, 255], getLineWidth: 1.5, lineWidthUnits: 'pixels', stroked: true,
        pickable: true,
        onClick: () => o.onPick({ title: 'New street tree', desc: 'Planted by the resolved allocation. Young canopy — the heat field contracts as it matures.' }),
        transitions: { getRadius: { duration: 900, enter: () => [0] } },
        updateTriggers: { getPosition: P.treeCount },
      }),
      new ScatterplotLayer({
        id: 'tree-hi', data: trees,
        getPosition: d => [d[0] - 2.6 / 82920, d[1] + 2.6 / 111132] as LngLat,
        getRadius: 3, radiusUnits: 'meters',
        getFillColor: [...CANOPY_HI, 140] as [number, number, number, number],
        transitions: { getRadius: { duration: 900, enter: () => [0] } },
        updateTriggers: { getPosition: P.treeCount },
      }),
      new ScatterplotLayer({
        id: 'benches', data: SCENARIO.benches.slice(0, P.benchCount),
        getPosition: d => d, getRadius: 2.4, radiusUnits: 'meters',
        getFillColor: [150, 119, 95, 255],
        getLineColor: [107, 83, 68, 255], getLineWidth: 1, lineWidthUnits: 'pixels', stroked: true,
        pickable: true,
        onClick: () => o.onPick({ title: 'Bench', desc: 'Seating scaled by the seating share of the resolved budget.' }),
        transitions: { getRadius: { duration: 700, enter: () => [0] } },
        updateTriggers: { getPosition: P.benchCount },
      }),
    );
  }

  /* proposal alignment — orchestration step */
  if (step === 4) {
    layers.push(new PathLayer({
      id: 'proposal', data: [SCENARIO.route],
      getPath: d => d, getColor: [...YELLOW, 235] as [number, number, number, number],
      getWidth: 9, widthUnits: 'meters', capRounded: true, jointRounded: true,
      getDashArray: [7, 5], dashJustified: true, extensions: [dashExt],
    }));
  }

  /* lifecycle review — built vs approved */
  if (step === 7) {
    layers.push(
      new PathLayer({
        id: 'implemented', data: [SCENARIO.implemented],
        getPath: d => d, getColor: [...RED, 245] as [number, number, number, number],
        getWidth: 5, widthUnits: 'meters', capRounded: true,
        getDashArray: [6, 4], extensions: [dashExt],
      }),
      new PolygonLayer({
        id: 'review-ring', data: [{ c: SCENARIO.reviewPoint }],
        getPolygon: d => ellipse(d.c, 90, 70),
        getFillColor: [...RED, 30] as [number, number, number, number],
        getLineColor: [...RED, 230] as [number, number, number, number],
        getLineWidth: 2.5, lineWidthUnits: 'pixels', stroked: true, filled: true,
      }),
      new TextLayer({
        id: 'review-label', data: [{ pos: [SCENARIO.reviewPoint[0], SCENARIO.reviewPoint[1] + 0.00062] as LngLat, txt: 'REVIEW TRIGGERED · controlled deviation > tolerance' }],
        getPosition: d => d.pos, getText: d => d.txt,
        getSize: 13, getColor: [255, 235 as number, 235, 255],
        background: true, getBackgroundColor: [90, 20, 19, 235], backgroundPadding: [8, 4],
        fontFamily: FONT, fontWeight: 700, characterSet: 'auto',
      }),
    );
  }

  /* conflict edges — computed pairs, drawn between real record positions */
  if (step === 2) {
    const seen = new Set<string>();
    const uniq = P.conflicts.filter(c => {
      const k = [c.a, c.b].sort().join('-');
      if (seen.has(k) || c.kind === 'budget') return false;
      seen.add(k); return true;
    });
    layers.push(
      new ArcLayer({
        id: 'conflicts', data: uniq,
        getSourcePosition: d => N.find(n => n.id === d.a)!.pos,
        getTargetPosition: d => N.find(n => n.id === d.b)!.pos,
        getSourceColor: [...BROWN, 235] as [number, number, number, number],
        getTargetColor: [...BROWN, 235] as [number, number, number, number],
        getWidth: 3.5, getHeight: 0.6, pickable: true,
        onClick: (info) => { const d = uniq[info.index]; o.onPick({ title: `${d.a} × ${d.b} — ${d.kind} conflict`, desc: d.detail }); },
      }),
      new TextLayer({
        id: 'conflict-count',
        data: [{ pos: [midRoute[0] + 0.0016, midRoute[1]] as LngLat, txt: `${P.conflicts.length} conflicts detected` }],
        getPosition: d => d.pos, getText: d => d.txt,
        getSize: 14, getColor: [255, 255, 255, 255],
        background: true, getBackgroundColor: PANEL_BG, backgroundPadding: [9, 5],
        fontFamily: FONT, fontWeight: 800, characterSet: 'auto',
      }),
    );
  }

  /* equity rings — sized by gap to floor */
  if (step === 3 || (viewMode === 'equity' && step > 3)) {
    layers.push(
      new ScatterplotLayer({
        id: 'equity-rings', data: P.flags,
        getPosition: d => N.find(n => n.id === d.id)!.pos,
        getRadius: d => 55 + d.gap * 220, radiusUnits: 'meters',
        getFillColor: [...STRAW, 20] as [number, number, number, number],
        getLineColor: [...STRAW, 230] as [number, number, number, number],
        getLineWidth: 2.5, lineWidthUnits: 'pixels', stroked: true, filled: true,
        transitions: { getRadius: { duration: 700, enter: () => [0] } },
      }),
      new TextLayer({
        id: 'equity-labels', data: P.flags,
        getPosition: d => N.find(n => n.id === d.id)!.pos,
        getText: d => `${Math.round(d.gap * 100)}pt below floor`,
        getSize: 12, getColor: [255, 230, 230, 255],
        getPixelOffset: [0, -46],
        background: true, getBackgroundColor: [90, 20, 19, 225], backgroundPadding: [7, 4],
        fontFamily: FONT, fontWeight: 700, characterSet: 'auto',
      }),
    );
  }

  /* demand records */
  if (showNeeds) {
    layers.push(
      new ScatterplotLayer({
        id: 'need-halo', data: N,
        getPosition: d => d.pos, getRadius: 34, radiusUnits: 'meters',
        getFillColor: [...YELLOW, 26] as [number, number, number, number],
        getLineColor: [...YELLOW, 190] as [number, number, number, number],
        getLineWidth: 1.6, lineWidthUnits: 'pixels', stroked: true, filled: true,
        transitions: { getRadius: { duration: 600, enter: () => [0] } },
      }),
      new ScatterplotLayer({
        id: 'need-pins', data: N,
        getPosition: d => d.pos, getRadius: 9, radiusUnits: 'meters', radiusMinPixels: 5,
        getFillColor: [...YELLOW, 255] as [number, number, number, number],
        getLineColor: [255, 255, 255, 255], getLineWidth: 2, lineWidthUnits: 'pixels', stroked: true,
        pickable: true,
        onClick: (info) => { const d = info.object as Need; o.onPick({ title: `${d.id} · ${d.label}`, desc: needDesc(d, P) }); },
        transitions: { getRadius: { duration: 600, enter: () => [0] } },
      }),
      new TextLayer({
        id: 'need-labels', data: N,
        getPosition: d => d.pos,
        getText: d => `${d.id} · ${d.label}`,
        getSize: 12, getColor: [255, 255, 255, 255],
        getPixelOffset: [0, -24],
        background: true, getBackgroundColor: PANEL_BG, backgroundPadding: [7, 4],
        fontFamily: FONT, fontWeight: 700, characterSet: 'auto',
      }),
    );
  }

  /* orchestrator verdicts */
  if (step >= 4 && step <= 5) {
    const verdictColor = (a: string): [number, number, number, number] =>
      a === 'retain' ? [...MINT, 255] as [number, number, number, number]
        : a === 'revise' ? [...YELLOW, 255] as [number, number, number, number]
          : [255, 170, 170, 255];
    layers.push(new TextLayer({
      id: 'verdicts', data: P.decisions,
      getPosition: d => N.find(n => n.id === d.id)!.pos,
      getText: d => `${d.action.toUpperCase()}${d.alloc ? ` $${d.alloc}M` : ''}`,
      getSize: 12, getColor: d => verdictColor(d.action),
      getPixelOffset: [0, -48],
      background: true, getBackgroundColor: PANEL_BG, backgroundPadding: [7, 4],
      fontFamily: FONT, fontWeight: 800, characterSet: 'auto',
      updateTriggers: { getText: P, getColor: P },
    }));
  }

  /* moving agents — positions updated per frame from the simulation */
  layers.push(
    new ScatterplotLayer<Car>({
      id: 'cars', data: o.cars,
      getPosition: d => d.pos, getRadius: 3.2, radiusUnits: 'meters', radiusMinPixels: 2.5,
      getFillColor: [62, 72, 84, 235],
      getLineColor: [235, 235, 235, 90], getLineWidth: 1, lineWidthUnits: 'pixels', stroked: true,
      updateTriggers: { getPosition: o.frame },
    }),
    new ScatterplotLayer<Ped>({
      id: 'peds', data: o.peds,
      getPosition: d => d.pos, getRadius: 1.7, radiusUnits: 'meters', radiusMinPixels: 2.6,
      getFillColor: d => [...ROLE_COLOR[d.role], 255] as [number, number, number, number],
      getLineColor: d => d.onGreen ? [213, 223, 193, 255] : [255, 255, 255, 210],
      getLineWidth: d => (d.onGreen ? 2 : 1), lineWidthUnits: 'pixels', stroked: true,
      pickable: true,
      onClick: (info) => {
        const d = info.object as Ped;
        o.onPick({
          title: ROLE_LABEL[d.role],
          desc: d.onGreen
            ? 'Chose the new greenway — utility of shade and seating outweighed the detour.'
            : 'Following the original sidewalk network. Route choice is re-evaluated by utility at each turn.',
        });
      },
      updateTriggers: { getPosition: o.frame, getLineColor: o.frame, getLineWidth: o.frame },
    }),
  );

  return layers.filter(Boolean) as Layer[];
}
