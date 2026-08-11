/* Live simulation: pedestrians + cars move along real-geometry paths;
   heat exposure is accumulated per frame from agent positions — never scripted. */
import { GeoPath, distM, mulberry32, type LngLat } from './geo';
import {
  CASES, PED_PATHS, CAR_PATHS, CROSSWALK_ZONES,
  UTILITY, ROLE_SPEED, type Role,
} from './scenario';

/* The movement study runs on the Chicago corridor case only. */
const SCENARIO = CASES.chicago;

export interface Ped {
  id: number;
  role: Role;
  homePath: GeoPath;
  path: GeoPath;
  onGreen: boolean;
  corridor: boolean;      // eligible to adopt the greenway
  d: number;              // metres along path
  dir: 1 | -1;
  speed: number;          // m/s
  pauseUntil: number;
  pos: LngLat;
}

export interface Car {
  id: number;
  path: GeoPath;
  d: number;
  speed: number;          // m/s
  v: number;              // 0..1 velocity factor (braking)
  pos: LngLat;
}

export const GREEN_PATH = new GeoPath(SCENARIO.route);
const PED_GEO = PED_PATHS.map(p => new GeoPath(p));
const CAR_GEO = CAR_PATHS.map(p => new GeoPath(p));

const ROLES: Role[] = ['elder', 'wheel', 'family', 'commuter', 'bike'];

export function createPeds(): Ped[] {
  const rand = mulberry32(7);
  const peds: Ped[] = [];
  let id = 0;
  const mix: Array<[number, Role[]]> = [
    [0, ['elder', 'commuter', 'family', 'wheel', 'commuter']],
    [1, ['family', 'commuter', 'elder', 'bike', 'commuter']],
    [2, ['commuter', 'family', 'elder']],
    [3, ['family', 'commuter', 'wheel']],
    [4, ['family', 'elder', 'commuter']],
    [5, ['family', 'bike']],
    [6, ['wheel', 'elder']],
  ];
  for (const [pi, roles] of mix) {
    const gp = PED_GEO[pi];
    for (const role of roles) {
      peds.push({
        id: id++, role: ROLES.includes(role) ? role : 'commuter',
        homePath: gp, path: gp, onGreen: false,
        corridor: pi === 0 || pi === 1,          // walkers on the two parallel streets can adopt the trail
        d: rand() * gp.total, dir: rand() < 0.5 ? 1 : -1,
        speed: ROLE_SPEED[role] * (0.85 + rand() * 0.3),
        pauseUntil: 0, pos: gp.pointAt(0),
      });
    }
  }
  return peds;
}

export function createCars(): Car[] {
  const rand = mulberry32(21);
  const cars: Car[] = [];
  let id = 0;
  for (const gp of CAR_GEO) {
    for (let k = 0; k < 2; k++) {
      cars.push({
        id: id++, path: gp,
        d: rand() * gp.total,
        speed: 7 + rand() * 3,       // ~25–36 km/h
        v: 1, pos: gp.pointAt(0),
      });
    }
  }
  return cars;
}

/** Utility-based route choice — logistic, same coefficients as the SVG prototype. */
function maybeSwitchRoute(p: Ped, step: number, treeShare: number, benchShare: number): void {
  if (step < 6 || !p.corridor) { p.path = p.homePath; p.onGreen = false; return; }
  const w = UTILITY[p.role];
  const u = w.shade * treeShare + w.seat * benchShare - w.detour * 0.5;
  const pSwitch = 1 / (1 + Math.exp(-6 * u));
  if (Math.random() < pSwitch) { p.path = GREEN_PATH; p.onGreen = true; }
  else { p.path = p.homePath; p.onGreen = false; }
}

export interface SimState {
  step: number;
  treeShare: number;
  benchShare: number;
  heatFactor: number;
  simSpeed: number;
}

export function tickSim(peds: Ped[], cars: Car[], dtMs: number, now: number, s: SimState): void {
  const sdt = (dtMs * s.simSpeed) / 1000; // seconds of sim time
  for (const p of peds) {
    if (p.pauseUntil) { if (now < p.pauseUntil) continue; p.pauseUntil = 0; }
    else if (Math.random() < 0.00004 * dtMs * s.simSpeed) { p.pauseUntil = now + 1200 + Math.random() * 2000; continue; }
    p.d += p.speed * sdt * p.dir;
    if (p.d > p.path.total) {
      p.d = p.path.total; p.dir = -1;
      p.pauseUntil = now + 600 + Math.random() * 1800;
      maybeSwitchRoute(p, s.step, s.treeShare, s.benchShare);
      p.d = Math.min(p.d, p.path.total);
    } else if (p.d < 0) {
      p.d = 0; p.dir = 1;
      p.pauseUntil = now + 600 + Math.random() * 1800;
      maybeSwitchRoute(p, s.step, s.treeShare, s.benchShare);
    }
    p.pos = p.path.pointAt(p.d);
  }
  // cars brake near occupied crosswalks
  const busy = CROSSWALK_ZONES.map(z => peds.some(p => distM(p.pos, z) < 26));
  for (const c of cars) {
    let tgt = 1;
    CROSSWALK_ZONES.forEach((z, i) => { if (busy[i] && distM(c.pos, z) < 55) tgt = 0.08; });
    c.v += (tgt - c.v) * 0.12;
    c.d += c.speed * sdt * c.v;
    if (c.d > c.path.total) c.d = 0;
    c.pos = c.path.pointAt(c.d);
  }
}

export function resetRoutes(peds: Ped[]): void {
  for (const p of peds) { p.path = p.homePath; p.onGreen = false; }
}

/** Immediate re-evaluation for everyone — used when the design step goes live. */
export function reevaluateRoutes(peds: Ped[], step: number, treeShare: number, benchShare: number): void {
  for (const p of peds) {
    maybeSwitchRoute(p, step, treeShare, benchShare);
    p.d = Math.min(p.d, p.path.total);
    p.pos = p.path.pointAt(p.d);
  }
}

/* ---------- live metrics (accumulated per frame) ---------- */
export interface HistorySample { t: number; p: number; g: number; adopt: number }

export class Metrics {
  simMs = 0;
  expP = { hot: 0, total: 0 };
  expG = { hot: 0, total: 0 };
  history: HistorySample[] = [];
  private lastSample = 0;

  reset(): void {
    this.simMs = 0;
    this.expP = { hot: 0, total: 0 };
    this.expG = { hot: 0, total: 0 };
    this.history = [];
    this.lastSample = 0;
  }

  private inHeat(pos: LngLat, hf: number): boolean {
    return SCENARIO.heat.some(z => {
      const dx = ((pos[0] - z.center[0]) * 82920) / (z.rx * hf);
      const dy = ((pos[1] - z.center[1]) * 111132) / (z.ry * hf);
      return dx * dx + dy * dy <= 1;
    });
  }

  tick(dtMs: number, peds: Ped[], hf: number): void {
    this.simMs += dtMs;
    for (const p of peds) {
      const b = p.role === 'elder' || p.role === 'wheel' ? this.expP : this.expG;
      b.total += dtMs;
      if (this.inHeat(p.pos, hf)) b.hot += dtMs;
    }
    if (this.simMs - this.lastSample > 600) {
      this.lastSample = this.simMs;
      this.history.push({
        t: +(this.simMs / 1000).toFixed(1),
        p: this.rate(this.expP), g: this.rate(this.expG),
        adopt: this.adoption(peds),
      });
      if (this.history.length > 90) this.history.shift();
    }
  }

  rate(b: { hot: number; total: number }): number { return b.total ? b.hot / b.total : 0; }
  adoption(peds: Ped[]): number { return peds.length ? peds.filter(p => p.onGreen).length / peds.length : 0; }
}
