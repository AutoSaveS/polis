import type { Scenario } from './scenario';
import type { Params, Pipeline } from './pipeline';

export interface StepCopy {
  meta: string;
  title: string;
  text: string;
  state: string;
  stats: Array<[string, string | number]>;
}

export const STEP_NAMES = ['Scene', 'Demand', 'Conflict', 'Equity', 'Orchestrate', 'Design', 'Feedback', 'Review'];

export function stepCopy(scn: Scenario, step: number, P: Pipeline, params: Params): StepCopy {
  const c = P.counts;
  const SCENARIO = scn;
  const all: StepCopy[] = [
    {
      meta: 'Stage 1 · Shared world model', title: 'Sense the place',
      text: 'Alignment, envelope and movement form one shared spatial state.',
      state: 'Environment → shared world model',
      stats: [['Heat zones', SCENARIO.heat.length], ['Records', SCENARIO.needs.length], ['Protected', SCENARIO.needs.filter(n => n.protected).length], ['Flow', SCENARIO.hasMovement ? 'mixed' : '—']],
    },
    {
      meta: 'Stage 2 · Demand capture', title: 'Encode needs',
      text: 'Four needs become source-linked spatial demand records.',
      state: 'Needs → R1–R4',
      stats: [['Records', SCENARIO.needs.length], ['Cost total', `$${SCENARIO.needs.reduce((s, n) => s + n.cost, 0).toFixed(1)}M`], ['Protected', SCENARIO.needs.filter(n => n.protected).length], ['State', 'ready']],
    },
    {
      meta: 'Stage 2 · Conflict detection', title: 'Detect conflicts',
      text: 'Records collide in space, timing and budget.',
      state: 'R1–R4 → conflicts',
      stats: [
        ['Spatial', P.conflicts.filter(x => x.kind === 'spatial').length],
        ['Timing', P.conflicts.filter(x => x.kind === 'timing').length],
        ['Budget', P.conflicts.filter(x => x.kind === 'budget').length],
        ['Total', P.conflicts.length],
      ],
    },
    {
      meta: 'Stage 2 · Equity review', title: 'Protect equity',
      text: 'Protected groups below the access floor are flagged.',
      state: 'Conflicts → equity flags',
      stats: [['Floor', params.floor], ['Flags', P.flags.length], ['Protected', '2'], ['Status', 'checked']],
    },
    {
      meta: 'Stage 2 · Orchestration', title: 'Resolve the needs',
      text: 'Budget is allocated under the equity floor, protected needs first.',
      state: 'Evidence + constraints → R*',
      stats: [['Retain', c.retain], ['Revise', c.revise], ['Reject', c.reject], ['Used', `$${P.used}M`]],
    },
    {
      meta: 'Stage 3 · Parametric design', title: 'Grow the intervention',
      text: 'The resolved allocation becomes canopy and seating.',
      state: 'R* → geometry',
      stats: [['Trees', `${P.treeCount}/${SCENARIO.designPoints.length}`], ['Benches', `${P.benchCount}/${SCENARIO.benches.length}`], ['Canopy', `${Math.round(P.treeShare * 100)}%`], ['Budget', 'OK']],
    },
    {
      meta: 'Stage 3 · Local feedback', title: 'Let the city respond',
      text: SCENARIO.hasMovement
        ? 'Pedestrians re-route by utility; the metrics respond.'
        : 'The heat field contracts with the built canopy.',
      state: 'Design → updated evidence',
      stats: [['Heat field', `${Math.round(P.heatFactor * 100)}%`], ['Choice', 'utility'], ['Roles', '4'], ['Metrics', SCENARIO.hasMovement ? 'live' : '—']],
    },
    {
      meta: 'Lifecycle governance', title: 'Review implementation',
      text: 'Built is compared with approved; deviation triggers review.',
      state: 'Planned vs built',
      stats: [['Planned', 'frozen'], ['Case', 'controlled'], ['Tolerance', 'fail'], ['Review', 'on']],
    },
  ];
  return all[step];
}
