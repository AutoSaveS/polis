#!/usr/bin/env python3
"""Deterministic structural smoke test; it creates no study observations."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SEED = 700001
OUT = ROOT / "analysis" / "synthetic_smoke_test_result.json"


def load_scenarios() -> list[dict[str, str]]:
    with (ROOT / "scenarios.csv").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def design_matrix(rows: list[dict[str, object]]) -> np.ndarray:
    workflows = ["EXISTING", "CONVENTIONAL", "DIGITAL", "POLIS"]
    sites = ["Suzhou", "London", "Chicago"]
    decisions = ["GE", "AR", "CU", "RR", "EA", "IP"]
    return np.asarray(
        [
            [
                1.0,
                *[float(r["workflow"] == w) for w in workflows[:-1]],
                *[float(r["site"] == s) for s in sites[:-1]],
                *[float(r["decision_type"] == d) for d in decisions[:-1]],
                float(r["variant"] == "S"),
            ]
            for r in rows
        ]
    )


def main() -> int:
    scenarios = load_scenarios()
    rng = np.random.default_rng(SEED)
    workflows = ["EXISTING", "CONVENTIONAL", "DIGITAL", "POLIS"]
    outcomes = ["A_green", "E_equity", "C_comfort", "P_ret", "I_impl"]
    exp1_rows: list[dict[str, object]] = []
    workflow_effect = {"EXISTING": 0.00, "CONVENTIONAL": 0.05, "DIGITAL": 0.10, "POLIS": 0.18}
    for scenario in scenarios:
        for workflow in workflows:
            for index, outcome in enumerate(outcomes):
                exp1_rows.append(
                    {
                        **scenario,
                        "workflow": workflow,
                        outcome: float(np.clip(0.55 + workflow_effect[workflow] + index * 0.01 + rng.normal(0, 0.005), 0, 1)),
                    }
                )
    assert len(exp1_rows) == 36 * 4 * 5
    matrix = design_matrix(exp1_rows[::5])
    assert np.linalg.matrix_rank(matrix) == matrix.shape[1]
    y = np.asarray([float(row["A_green"]) for row in exp1_rows[::5]])
    beta = np.linalg.lstsq(matrix, y, rcond=None)[0]
    assert -beta[3] > 0, "POLIS-minus-DIGITAL should be positive in the deterministic smoke fixture"

    exp2_scenarios = [row for row in scenarios if row["exp2_included"] == "yes"]
    configurations = ["FULL", "A1", "A2", "A3", "A4", "A5"]
    exp2_rows = []
    for scenario in exp2_scenarios:
        for config in configurations:
            exp2_rows.append({"scenario_id": scenario["scenario_id"], "configuration": config, "A_green": 0.80 - (0.0 if config == "FULL" else 0.05)})
    assert len(exp2_rows) == 12 * 6
    full = {r["scenario_id"]: r["A_green"] for r in exp2_rows if r["configuration"] == "FULL"}
    for config in configurations[1:]:
        ablated = {r["scenario_id"]: r["A_green"] for r in exp2_rows if r["configuration"] == config}
        assert all(full[k] - ablated[k] >= 0 for k in full)

    with (ROOT / "protocols" / "resident_randomisation.csv").open(newline="", encoding="utf-8") as stream:
        allocation = list(csv.DictReader(stream))
    assert len(allocation) == 60
    for city in ("SUZ", "LON", "CHI"):
        orders = [row["mode_order"] for row in allocation if row["city"] == city]
        assert orders.count("TEXT_THEN_SPATIAL") == orders.count("SPATIAL_THEN_TEXT") == 10

    digest = hashlib.sha256(json.dumps({"exp1": len(exp1_rows), "exp2": len(exp2_rows), "allocation": len(allocation), "beta": beta.round(12).tolist()}, sort_keys=True).encode()).hexdigest()
    result = {
        "status": "PASSED_STRUCTURAL_SMOKE_ONLY",
        "seed": SEED,
        "exp1_rows": len(exp1_rows),
        "exp2_rows": len(exp2_rows),
        "resident_allocation_rows": len(allocation),
        "tests": ["scenario expansion", "full-rank Experiment 1 design", "paired Experiment 2 contrasts", "balanced resident randomisation"],
        "not_tested": ["R 4.3 CR2 inference", "cumulative-link mixed models", "Bradley-Terry model", "Fleiss kappa", "participant data"],
        "result_sha256": digest,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
