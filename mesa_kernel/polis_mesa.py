"""POLIS Mesa kernel.

A faithful port of the POLIS simulation kernel (src/pipeline.ts, src/sim.ts)
to Mesa, the standard Python agent-based modelling framework.

The TypeScript front end remains the agency-facing interface; this kernel is
the science-facing implementation: headless, seeded, batch-runnable, and
DataCollector-instrumented, so Monte Carlo sweeps and sensitivity analysis
run in the Python ecosystem (pandas / SALib) without touching the browser.

Correspondence with the TypeScript implementation
-------------------------------------------------
compute_pipeline()   <->  src/pipeline.ts  computePipeline()   (pure function)
Ped(mesa.Agent)      <->  src/sim.ts       Ped + maybeSwitchRoute()
PolisModel.step()    <->  src/sim.ts       tickSim() + Metrics.tick()
DataCollector        <->  src/sim.ts       Metrics (per-frame accumulation)
batch_run()          <->  the interface's slider recomputation, swept as a grid

All analytical records are the same frozen, illustrative demonstrator values
used by the interface — not resident observations or completed study results.

Run:
    python3 polis_mesa.py            # one seeded run + a budget x floor sweep
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import mesa
import pandas as pd

# --------------------------------------------------------------------------
# Frozen scenario data — Chicago · New ERA Trail corridor (OSM way 624189839).
# Identical values to src/scenario.ts.
# --------------------------------------------------------------------------

M_PER_DEG_LON = 82920.0   # at ~41.79 N, matches the TS implementation
M_PER_DEG_LAT = 111132.0


@dataclass(frozen=True)
class Need:
    id: str
    pos: tuple
    label: str
    cost: float
    base_access: float
    protected: bool
    window: tuple
    gain_shade: float
    gain_seat: float


@dataclass(frozen=True)
class HeatZone:
    center: tuple
    rx: float
    ry: float
    severity: float


NEEDS = [
    Need('R1', (-87.67424, 41.78764), 'Shade',         8.4, 0.46, True,  (2027, 2029), 0.9, 0.6),
    Need('R2', (-87.67061, 41.78768), 'Access',        6.2, 0.38, True,  (2027, 2028), 0.3, 0.4),
    Need('R3', (-87.66673, 41.78774), 'Green access',  9.8, 0.61, False, (2028, 2030), 0.6, 0.5),
    Need('R4', (-87.67158, 41.78767), 'Safe crossing', 5.6, 0.57, False, (2027, 2028), 0.2, 0.2),
]

HEAT_ZONES = [
    HeatZone((-87.67445, 41.78765), 235, 125, 0.92),
    HeatZone((-87.67055, 41.78769), 225, 115, 0.74),
    HeatZone((-87.66655, 41.78774), 190, 105, 0.58),
]

SPATIAL_THRESHOLD_M = 330.0
N_DESIGN_POINTS = 7
N_BENCHES = 3

GREEN_ROUTE = [
    (-87.6764078, 41.7876116), (-87.6742425, 41.7876362), (-87.6740119, 41.7876387),
    (-87.6730422, 41.7876506), (-87.6727942, 41.7876537), (-87.6718300, 41.7876680),
    (-87.6715805, 41.7876717), (-87.6706096, 41.7876837), (-87.6703681, 41.7876867),
    (-87.6693932, 41.7877019), (-87.6691531, 41.7877057), (-87.6669712, 41.7877363),
    (-87.6667311, 41.7877397), (-87.6646016, 41.7877635),
]

PED_PATHS = [
    # West 58th Street, north of the proposed trail.
    [(-87.6741459, 41.7884472), (-87.6729482, 41.7884675), (-87.6705166, 41.7884926),
     (-87.6680979, 41.7885228), (-87.6656513, 41.7885534), (-87.6645036, 41.7885678)],
    # West 59th Street, south of the proposed trail.
    [(-87.6766852, 41.7865990), (-87.6740971, 41.7866255), (-87.6716800, 41.7866577),
     (-87.6692682, 41.7866898), (-87.6668322, 41.7867222), (-87.6643306, 41.7867557)],
    # South Damen Avenue.
    [(-87.6740507, 41.7848896), (-87.6740971, 41.7866255), (-87.6741217, 41.7875466),
     (-87.6741459, 41.7884472), (-87.6741807, 41.7897448)],
    # South Wood Street.
    [(-87.6692131, 41.7847931), (-87.6692506, 41.7862348), (-87.6692682, 41.7866898),
     (-87.66929, 41.78770), (-87.66932, 41.78851)],
    # South Paulina Street.
    [(-87.6667829, 41.7848222), (-87.6668202, 41.7862610), (-87.6668322, 41.7867222),
     (-87.66686, 41.78774), (-87.66688, 41.78854)],
    # South Marshfield Avenue.
    [(-87.6655731, 41.7849982), (-87.6656036, 41.7862742), (-87.6656147, 41.7867384),
     (-87.66565, 41.78775), (-87.6656513, 41.7885534)],
    # Short connector used by mobility actors at the west access.
    [(-87.6741459, 41.7884472), (-87.67414, 41.78805), (-87.67413, 41.78768),
     (-87.67410, 41.7866255)],
]

# Role-specific utility weights — discrete-choice form (same table as the UI).
UTILITY = {
    'elder':    {'shade': 0.9,  'seat': 0.65, 'detour': 0.15},
    'wheel':    {'shade': 0.55, 'seat': 0.45, 'detour': 0.1},
    'family':   {'shade': 0.6,  'seat': 0.4,  'detour': 0.3},
    'commuter': {'shade': 0.2,  'seat': 0.05, 'detour': 0.85},
    'bike':     {'shade': 0.3,  'seat': 0.05, 'detour': 0.75},
}

ROLE_SPEED = {'elder': 0.9, 'wheel': 1.0, 'family': 1.1, 'commuter': 1.45, 'bike': 3.4}

PROTECTED_ROLES = {'elder', 'wheel'}

# Same population mix as createPeds() in src/sim.ts.
PED_MIX = [
    (0, ['elder', 'commuter', 'family', 'wheel', 'commuter']),
    (1, ['family', 'commuter', 'elder', 'bike', 'commuter']),
    (2, ['commuter', 'family', 'elder']),
    (3, ['family', 'commuter', 'wheel']),
    (4, ['family', 'elder', 'commuter']),
    (5, ['family', 'bike']),
    (6, ['wheel', 'elder']),
]


# --------------------------------------------------------------------------
# Geometry helpers — port of src/geo.ts (equirectangular metres, polyline walk).
# --------------------------------------------------------------------------

def dist_m(a, b):
    dx = (a[0] - b[0]) * M_PER_DEG_LON
    dy = (a[1] - b[1]) * M_PER_DEG_LAT
    return math.hypot(dx, dy)


class GeoPath:
    """A polyline on real geography, walkable by metre offset."""

    def __init__(self, points):
        self.points = points
        self.cum = [0.0]
        for i in range(1, len(points)):
            self.cum.append(self.cum[-1] + dist_m(points[i - 1], points[i]))
        self.total = self.cum[-1]

    def point_at(self, d):
        d = max(0.0, min(d, self.total))
        for i in range(1, len(self.points)):
            if d <= self.cum[i]:
                seg = self.cum[i] - self.cum[i - 1]
                t = 0.0 if seg == 0 else (d - self.cum[i - 1]) / seg
                a, b = self.points[i - 1], self.points[i]
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return self.points[-1]


GREEN_PATH = GeoPath(GREEN_ROUTE)
PED_GEO = [GeoPath(p) for p in PED_PATHS]


# --------------------------------------------------------------------------
# Planning pipeline — pure function, port of src/pipeline.ts computePipeline().
# --------------------------------------------------------------------------

def compute_pipeline(budget: float, floor: float) -> dict:
    """Conflicts -> equity flags -> protected-first allocation -> design scale.

    Returns the same fields as the TS implementation, including the trace.
    """
    trace = []

    # Conflict detection: computed, not scripted.
    conflicts = []
    for i in range(len(NEEDS)):
        for j in range(i + 1, len(NEEDS)):
            a, b = NEEDS[i], NEEDS[j]
            d = dist_m(a.pos, b.pos)
            if d < SPATIAL_THRESHOLD_M:
                conflicts.append(('spatial', a.id, b.id, f'{d:.0f}m apart < {SPATIAL_THRESHOLD_M:.0f}m'))
            (a0, a1), (b0, b1) = a.window, b.window
            if max(a0, b0) <= min(a1, b1) and d < SPATIAL_THRESHOLD_M * 1.4:
                conflicts.append(('timing', a.id, b.id, f'windows {a0}-{a1} and {b0}-{b1} overlap nearby'))
    total_cost = sum(n.cost for n in NEEDS)
    if total_cost > budget:
        s = sorted(NEEDS, key=lambda n: -n.cost)
        conflicts.append(('budget', s[0].id, s[1].id, f'requests ${total_cost:.1f}M > budget ${budget:.1f}M'))
    trace += [f'{k} conflict {a}x{b}: {msg}' for k, a, b, msg in conflicts]

    # Equity review: protected groups checked against the access floor.
    flags = [(n.id, floor - n.base_access) for n in NEEDS if n.protected and n.base_access < floor]
    trace += [f'{nid} flagged: {gap * 100:.0f}pt below floor {floor}' for nid, gap in flags]

    # Orchestration: greedy, protected-first, worse access first within class.
    order = sorted(NEEDS, key=lambda n: (not n.protected, n.base_access))
    remaining = budget
    decisions = {}
    for n in order:
        if remaining >= n.cost:
            decisions[n.id] = ['retain', n.cost]
            remaining -= n.cost
        elif remaining >= n.cost * 0.55:
            decisions[n.id] = ['revise', round(remaining, 1)]
            remaining = 0
        else:
            decisions[n.id] = ['reject', 0.0]

    # Floor enforcement: a flagged protected need must not be rejected —
    # pull budget from the cheapest retained non-protected need.
    by_id = {n.id: n for n in NEEDS}
    for nid, _gap in flags:
        if decisions[nid][0] == 'reject':
            donors = [(i, d) for i, d in decisions.items()
                      if not by_id[i].protected and d[0] != 'reject']
            if donors:
                donor_id, donor = min(donors, key=lambda x: x[1][1])
                alloc = round(min(by_id[nid].cost, donor[1]), 1)
                decisions[nid] = ['revise', alloc]
                if donor[1] > alloc * 1.6:
                    decisions[donor_id] = ['revise', round(donor[1] - alloc, 1)]
                else:
                    decisions[donor_id] = ['reject', 0.0]
                trace.append(f'floor enforcement: {nid} upgraded by reallocating from {donor_id}')

    used = round(sum(d[1] for d in decisions.values()), 1)
    trace.append(f'resolved: ${used}M of ${budget}M allocated')

    # Design scale follows the actual allocation to shade / seating needs.
    shade_alloc = sum(decisions[n.id][1] * n.gain_shade for n in NEEDS)
    max_shade = sum(n.cost * n.gain_shade for n in NEEDS)
    seat_alloc = sum(decisions[n.id][1] * n.gain_seat for n in NEEDS)
    max_seat = sum(n.cost * n.gain_seat for n in NEEDS)
    tree_share = shade_alloc / max_shade if max_shade else 0.0
    bench_share = seat_alloc / max_seat if max_seat else 0.0
    heat_factor = 1 - 0.5 * tree_share  # heat field contracts with built canopy

    return {
        'conflicts': conflicts, 'flags': flags, 'decisions': decisions,
        'used': used, 'tree_share': tree_share, 'bench_share': bench_share,
        'tree_count': round(tree_share * N_DESIGN_POINTS),
        'bench_count': round(bench_share * N_BENCHES),
        'heat_factor': heat_factor, 'trace': trace,
    }


# --------------------------------------------------------------------------
# Agents — port of src/sim.ts (Ped + logistic route choice + exposure metrics).
# --------------------------------------------------------------------------

TICK_S = 0.5  # seconds of simulated time per Mesa step


class Ped(mesa.Agent):
    """A role-typed pedestrian walking real street geometry.

    Route choice is a binary-logit rule over shade gain, seating gain, and
    detour cost with role-specific weights — the same discrete-choice form
    (and coefficients) as the interface.
    """

    def __init__(self, unique_id, model, role, home_path, corridor):
        super().__init__(unique_id, model)
        self.role = role
        self.home_path = home_path
        self.path = home_path
        self.corridor = corridor          # eligible to adopt the greenway
        self.on_green = False
        self.d = model.random.random() * home_path.total
        self.dir = 1 if model.random.random() < 0.5 else -1
        self.speed = ROLE_SPEED[role] * (0.85 + model.random.random() * 0.3)
        self.pause_s = 0.0
        self.pos_ll = home_path.point_at(self.d)

    def maybe_switch_route(self):
        if not self.corridor or not self.model.design_live:
            self.path, self.on_green = self.home_path, False
            return
        w = UTILITY[self.role]
        u = (w['shade'] * self.model.pipeline['tree_share']
             + w['seat'] * self.model.pipeline['bench_share']
             - w['detour'] * 0.5)
        p_switch = 1.0 / (1.0 + math.exp(-6.0 * u))
        if self.model.random.random() < p_switch:
            self.path, self.on_green = GREEN_PATH, True
        else:
            self.path, self.on_green = self.home_path, False

    def step(self):
        if self.pause_s > 0:
            self.pause_s -= TICK_S
            return
        if self.model.random.random() < 0.04 * TICK_S:
            self.pause_s = 1.2 + self.model.random.random() * 2.0
            return
        self.d += self.speed * TICK_S * self.dir
        if self.d > self.path.total or self.d < 0:
            self.dir *= -1
            self.pause_s = 0.6 + self.model.random.random() * 1.8
            self.maybe_switch_route()
            self.d = max(0.0, min(self.d, self.path.total))
        self.pos_ll = self.path.point_at(self.d)


# --------------------------------------------------------------------------
# Model — pipeline + agent loop + DataCollector.
# --------------------------------------------------------------------------

def _exposure(model, protected: bool) -> float:
    b = model.exp_protected if protected else model.exp_general
    return b['hot'] / b['total'] if b['total'] else 0.0


class PolisModel(mesa.Model):
    """POLIS kernel: plan under a budget cap and an equity floor, then let
    role-typed agents respond on real geometry and measure who is exposed."""

    def __init__(self, budget=22.0, floor=0.75, design_live=True, seed=7):
        super().__init__()
        self.random = random.Random(seed)
        self.budget, self.floor = budget, floor
        self.design_live = design_live
        self.pipeline = compute_pipeline(budget, floor)

        self.schedule = mesa.time.RandomActivation(self)
        uid = 0
        for path_idx, roles in PED_MIX:
            for role in roles:
                corridor = path_idx in (0, 1)  # the two parallel streets
                self.schedule.add(Ped(uid, self, role, PED_GEO[path_idx], corridor))
                uid += 1

        self.exp_protected = {'hot': 0.0, 'total': 0.0}
        self.exp_general = {'hot': 0.0, 'total': 0.0}

        self.datacollector = mesa.DataCollector(model_reporters={
            'heat_exposure_protected': lambda m: _exposure(m, True),
            'heat_exposure_general': lambda m: _exposure(m, False),
            'adoption': lambda m: sum(a.on_green for a in m.schedule.agents) / len(m.schedule.agents),
            'budget_used': lambda m: m.pipeline['used'],
            'tree_count': lambda m: m.pipeline['tree_count'],
        })

    def in_heat(self, pos) -> bool:
        hf = self.pipeline['heat_factor']
        for z in HEAT_ZONES:
            dx = (pos[0] - z.center[0]) * M_PER_DEG_LON / (z.rx * hf)
            dy = (pos[1] - z.center[1]) * M_PER_DEG_LAT / (z.ry * hf)
            if dx * dx + dy * dy <= 1.0:
                return True
        return False

    def step(self):
        self.schedule.step()
        for a in self.schedule.agents:
            bucket = self.exp_protected if a.role in PROTECTED_ROLES else self.exp_general
            bucket['total'] += TICK_S
            if self.in_heat(a.pos_ll):
                bucket['hot'] += TICK_S
        self.datacollector.collect(self)


# --------------------------------------------------------------------------
# Entry point: one seeded run, then a budget x floor Monte Carlo sweep.
# --------------------------------------------------------------------------

def main():
    print('=== single seeded run (budget $22M, floor 0.75, seed 7) ===')
    model = PolisModel(budget=22.0, floor=0.75, seed=7)
    for d in model.pipeline['trace']:
        print('  trace |', d)
    for _ in range(1200):  # 10 minutes of simulated time
        model.step()
    print(model.datacollector.get_model_vars_dataframe().tail(3).round(3))

    print('\n=== budget x floor sweep, 5 seeds each (Monte Carlo) ===')
    results = mesa.batch_run(
        PolisModel,
        parameters={'budget': [14.0, 18.0, 22.0, 26.0, 30.0],
                    'floor': [0.60, 0.75, 0.90]},
        iterations=5, max_steps=1200,
        number_processes=1, data_collection_period=-1, display_progress=False,
    )
    df = pd.DataFrame(results)
    summary = (df.groupby(['budget', 'floor'])
                 [['heat_exposure_protected', 'heat_exposure_general', 'adoption', 'budget_used']]
                 .mean().round(3))
    print(summary)
    df.to_csv('sweep_results.csv', index=False)
    print('\nfull sweep written to sweep_results.csv')


if __name__ == '__main__':
    main()
