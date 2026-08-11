/* Pure pipeline: conflicts / equity / orchestration / design scaling.
   Ported 1:1 from the SVG prototype — distances now in metres on real geography. */
import { distM } from './geo';
import type { Scenario } from './scenario';

export interface Params { budget: number; floor: number }

export interface Conflict { kind: 'spatial' | 'timing' | 'budget'; a: string; b: string; detail: string }
export interface Flag { id: string; gap: number }
export interface Decision { id: string; action: 'retain' | 'revise' | 'reject'; alloc: number }

export interface Pipeline {
  conflicts: Conflict[];
  flags: Flag[];
  decisions: Decision[];
  counts: Record<Decision['action'], number>;
  used: number;
  treeCount: number;
  benchCount: number;
  treeShare: number;
  benchShare: number;
  heatFactor: number;
  trace: Record<number, string[]>;
}

export function computePipeline(scn: Scenario, params: Params): Pipeline {
  const N = scn.needs;
  const trace: Record<number, string[]> = { 1: [], 2: [], 3: [], 4: [], 5: [] };
  trace[1] = N.map(n => `<b>${n.id}</b> ← ${n.type} @ ${n.pos[1].toFixed(4)}N ${Math.abs(n.pos[0]).toFixed(4)}${n.pos[0] < 0 ? 'W' : 'E'} · need "${n.label}" · est. $${n.cost.toFixed(1)}M · access now ${(n.baseAccess * 100) | 0}%`);

  // conflict detection: computed, not scripted
  const conflicts: Conflict[] = [];
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
    const a = N[i], b = N[j], d = distM(a.pos, b.pos);
    if (d < scn.spatialThreshold)
      conflicts.push({ kind: 'spatial', a: a.id, b: b.id, detail: `${Math.round(d)}m apart < ${scn.spatialThreshold}m — compete for the same street space` });
    const [a0, a1] = a.window, [b0, b1] = b.window;
    if (Math.max(a0, b0) <= Math.min(a1, b1) && d < scn.spatialThreshold * 1.4)
      conflicts.push({ kind: 'timing', a: a.id, b: b.id, detail: `construction windows ${a0}–${a1} and ${b0}–${b1} overlap nearby` });
  }
  const totalCost = N.reduce((s, n) => s + n.cost, 0);
  if (totalCost > params.budget) {
    const sorted = [...N].sort((x, y) => y.cost - x.cost);
    conflicts.push({ kind: 'budget', a: sorted[0].id, b: sorted[1].id, detail: `requests total $${totalCost.toFixed(1)}M > budget $${params.budget.toFixed(1)}M` });
  }
  trace[2] = conflicts.map(c => `<b>${c.a}×${c.b}</b> ${c.kind} conflict — ${c.detail}`);
  if (!conflicts.length) trace[2] = ['No conflicts under current parameters — all records can proceed.'];

  // equity review: computed against the floor
  const flags: Flag[] = N.filter(n => n.protected && n.baseAccess < params.floor)
    .map(n => ({ id: n.id, gap: params.floor - n.baseAccess }));
  trace[3] = flags.map(f => `<b>${f.id}</b> flagged — protected group at ${((params.floor - f.gap) * 100) | 0}% access, ${Math.round(f.gap * 100)}pt below floor ${params.floor}`);
  if (!flags.length) trace[3] = [`No protected group falls below floor ${params.floor} — no equity constraint binds.`];

  // orchestration: greedy allocation, protected-first, floor enforced
  const order = [...N].sort((a, b) => {
    if (a.protected !== b.protected) return a.protected ? -1 : 1;
    return b.baseAccess < a.baseAccess ? 1 : -1; // worse access first within class
  });
  let remaining = params.budget;
  const decisions: Decision[] = [];
  for (const n of order) {
    if (remaining >= n.cost) { decisions.push({ id: n.id, action: 'retain', alloc: n.cost }); remaining -= n.cost; }
    else if (remaining >= n.cost * 0.55) { decisions.push({ id: n.id, action: 'revise', alloc: +remaining.toFixed(1) }); remaining = 0; }
    else decisions.push({ id: n.id, action: 'reject', alloc: 0 });
  }
  // floor enforcement: a flagged protected need must not be rejected —
  // pull budget from the cheapest retained non-protected need
  for (const f of flags) {
    const d = decisions.find(x => x.id === f.id)!;
    if (d.action === 'reject') {
      const donor = decisions
        .filter(x => { const n = N.find(m => m.id === x.id)!; return !n.protected && x.action !== 'reject'; })
        .sort((x, y) => x.alloc - y.alloc)[0];
      if (donor) {
        const need = N.find(m => m.id === f.id)!;
        d.action = 'revise'; d.alloc = +Math.min(need.cost, donor.alloc).toFixed(1);
        donor.action = donor.alloc > d.alloc * 1.6 ? 'revise' : 'reject';
        donor.alloc = donor.action === 'revise' ? +(donor.alloc - d.alloc).toFixed(1) : 0;
        trace[3].push(`Floor enforcement: <b>${f.id}</b> upgraded to revise by reallocating from <b>${donor.id}</b>.`);
      }
    }
  }
  decisions.sort((a, b) => (a.id < b.id ? -1 : 1));
  const used = +decisions.reduce((s, d) => s + d.alloc, 0).toFixed(1);
  trace[4] = decisions.map(d => {
    const n = N.find(m => m.id === d.id)!;
    return `<b>${d.id}</b> → ${d.action}${d.alloc ? ` · $${d.alloc}M` : ''} ${n.protected ? '(protected)' : ''}`;
  });
  trace[4].push(`R* resolved · $${used}M of $${params.budget}M allocated.`);

  // design scale follows the actual allocation to shade-type needs
  const shadeAlloc = decisions.reduce((s, d) => { const n = N.find(m => m.id === d.id)!; return s + d.alloc * n.gainShade; }, 0);
  const maxShade = N.reduce((s, n) => s + n.cost * n.gainShade, 0);
  const seatAlloc = decisions.reduce((s, d) => { const n = N.find(m => m.id === d.id)!; return s + d.alloc * n.gainSeat; }, 0);
  const maxSeat = N.reduce((s, n) => s + n.cost * n.gainSeat, 0);
  const treeShare = maxShade ? shadeAlloc / maxShade : 0;
  const benchShare = maxSeat ? seatAlloc / maxSeat : 0;
  const treeCount = Math.max(0, Math.round(treeShare * scn.designPoints.length));
  const benchCount = Math.max(0, Math.round(benchShare * scn.benches.length));
  const heatFactor = 1 - 0.5 * treeShare; // heat field contracts with real canopy built
  trace[5] = [`Allocation → geometry: ${treeCount}/${scn.designPoints.length} trees, ${benchCount}/${scn.benches.length} benches. Heat field contracts to ${Math.round(heatFactor * 100)}% of baseline.`];

  const counts = { retain: 0, revise: 0, reject: 0 };
  decisions.forEach(d => counts[d.action]++);
  return { conflicts, flags, decisions, counts, used, treeCount, benchCount, treeShare, benchShare, heatFactor, trace };
}
