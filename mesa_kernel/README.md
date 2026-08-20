# POLIS Mesa kernel

A faithful port of the POLIS simulation kernel — the planning pipeline
(`src/pipeline.ts`) and the agent simulation (`src/sim.ts`) — to
[Mesa](https://mesa.readthedocs.io/), the standard Python agent-based
modelling framework.

The TypeScript front end remains the agency-facing interface. This kernel is
the science-facing implementation: headless, seeded, batch-runnable, and
instrumented with Mesa's `DataCollector`, so Monte Carlo sweeps and
sensitivity analysis run in the Python ecosystem (pandas / SALib) without
touching the browser.

## Correspondence

| Mesa kernel | TypeScript interface |
|---|---|
| `compute_pipeline()` (pure function) | `src/pipeline.ts` `computePipeline()` |
| `Ped(mesa.Agent)` + logistic route choice | `src/sim.ts` `Ped` + `maybeSwitchRoute()` |
| `PolisModel.step()` + exposure buckets | `src/sim.ts` `tickSim()` + `Metrics.tick()` |
| `mesa.DataCollector` | per-frame live metrics |
| `mesa.batch_run()` grid | slider recomputation, swept as a grid |

Same frozen scenario data, same utility coefficients, same allocation rules.
On the Chicago corridor case at budget $22M and floor 0.75, the kernel
reproduces the interface's decision trace exactly — R1/R2 flagged at
29pt/37pt below the floor, $20.2M of $22M allocated.

## Run

```bash
pip install mesa pandas
python3 polis_mesa.py
```

Prints one seeded run (decision trace + collected metrics), then a
budget × floor Monte Carlo sweep (5 seeds per cell) and writes
`sweep_results.csv`.

All analytical records are frozen, illustrative demonstrator values —
not resident observations or completed study results.
