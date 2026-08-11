# Experiment 1 run order

This order separates frozen inputs, design production, outcome evaluation, and
confirmatory analysis. Rhino 8/Grasshopper may run on a separate fixed
workstation. The local Python machine receives only the exported package and
its handoff record.

## 0. Freeze the common inputs

Run these commands from the project root:

```bash
.venv-polis39/bin/python preregistration/prepare_experiment1_scenario_packages.py
.venv-polis39/bin/python preregistration/prepare_experiment1_run_manifest.py
.venv-polis39/bin/python preregistration/validate_preregistration.py
```

Confirm 36 scenario packages, 144 run rows, three city GeoPackages, population
weights, scenario seeds, need predicates, the constraint register, and the
unitless resource caps. Do not edit a package after formal work begins.

## 1. Prepare the fixed workstations and operators

On the Rhino workstation, follow
`software/rhino_generators/RHINO_WORKSTATION_SOP.md` and use the frozen
`software/rhino_generators/generator_contract.json`. Complete
`software/rhino_workstation_assets.template.json` as
`software/rhino_workstation_assets.json` with the inventory script only after
the actual six `.gh`/`.ghx` definitions and master `.3dm` exist. Record
Rhino/Grasshopper/plugin versions and SHA-256 values for every source file.
The definitions must implement the six registered design domains: vegetation,
hardscape, hydrology, furniture, activity zones, and ecological features.

Operator records and 108 assignment rows are useful for reproducibility and
should be maintained, but they are not technical prerequisites for the dry run
or for building the software components. Existing-condition rows do not
require an operator.

## 2. Run one non-study dry run

Use a practice scenario outside the 36 registered scenarios. Export one design
GeoPackage and one Rhino handoff record. The export must contain exactly the
required evidence layers:

`accessible_network`, `green_entrances`, `required_destinations`,
`turning_spaces`, `usable_spaces`, `shade_footprints`, and `design_objects`.

Validate the handoff against
`software/rhino_export_contract.schema.json`, then run the evaluator with test
need and constraint CSVs. Fix export or CRS errors before formal work. Do not
use dry-run results as Experiment 1 data.

## 3. Produce the formal designs

For each row in `experiment1_run_manifest.csv`, use the frozen scenario package
and the workflow implementation. Existing is the computable no-intervention
baseline and receives the same five-outcome evaluation as every generated run.
Conventional and Digital use their baseline workflow implementations. POLIS
requires the Terra API workflow (if the study run invokes Terra), the six local
indicator functions, provenance logging, and the Rhino generators.

Operators must not inspect another workflow's design or outcome for the same
scenario before their own submission. Record active minutes, elapsed time,
revisions, software, handoffs, and stopping state in the process log.

## 4. Transfer and validate each output

For every run, transfer the GeoPackage, need-result CSV, constraint-result CSV,
process log, and Rhino export record to the analysis machine. The local runner
checks the frozen world-model hash, handoff hash, CRS, layer contract, and run
ID before calculating outcomes. Any missing geometry, height, applicability, or
provenance is recorded as `not_evaluable`; it is never imputed.

## 5. Lock outcomes and analyse

After all eligible run outputs are archived and outcome labels are locked,
run the five-outcome evaluator for each row and build the analysis dataset.
Compute the three generated-workflow-minus-Existing paired changes before the
prespecified between-workflow contrasts; report the outcome-specific evaluable
denominator whenever a baseline or generated score is `not_evaluable`.
Only then run the registered R 4.3.3 confirmatory models. R is not required for
Rhino production or Python spatial scoring, but a locked R 4.3.3 environment is
required before inspecting confirmatory results.

## 5A. POLIS local feedback and orchestration runner

The technical runner is `polis_workflow_runner.py`. Its deterministic local
feedback layer is `analysis/polis_feedback_functions.py`. Both operate on the
frozen scenario package and never infer missing spatial, population, cost, or
legal evidence.

Run an offline contract check with synthetic, non-study responses:

```text
PYTHONPATH=preregistration python3 -m unittest -v \
  preregistration.analysis.test_polis_feedback_and_workflow
```

Run one scenario with a fixture directory (no network request and no API key):

```text
PYTHONPATH=preregistration python3 preregistration/polis_workflow_runner.py \
  --scenario-package preregistration/experiment1_scenario_packages/SUZ-GE-B.json \
  --fixtures preregistration/software/fixtures/polis_offline \
  --output-dir <dated-output-directory>
```

These bundled fixtures validate control flow only. They deliberately return
unresolved substantive decisions and must never be copied into a formal result.
Each need is processed as a separate demand event; conflict detection, Equity
Guardian review, and orchestration are repeated after every event as required
by the frozen algorithm.

After a Rhino candidate and its local evaluation are available, pass a JSON
array through `--candidate-evaluations`. Every array item must validate against
`software/schemas/polis_candidate_evaluation.schema.json`, including the
candidate and evaluator SHA-256 values, six internal indicators, six formal
quality values, object-level floors, hard constraints, and resource counters.

For a live synthetic preflight, first run
`python3 preregistration/software/api_preflight.py --live`; only after that
passes may the runner be used with `OPENAI_API_KEY` for a formal nonparticipant
workflow call. The key is read from the process environment and is never
written to an output file or sent to the Rhino operator.

The runner records raw request/response metadata, schema-validation retries,
role outputs, prompt/schema/config hashes, local feedback, and the registered
stopping reason in `polis_workflow_output.json`. A candidate design must be
exported and evaluated by the local spatial evaluator before the two-consecutive
target rule can stop the run.

## Current completion state

Already available: world-model GeoPackages, 36 frozen scenario packages,
Python 3.9.7 environment, five-outcome evaluator, 144-row queue, cross-device
export schema, and six-generator source/simulation tests. Still required for
formal technical execution: actual Rhino source assets and inventory, a passed
cross-device dry run, a real GeoPackage exporter, the Existing-condition
builder, the six local feedback functions, the POLIS workflow runner (and live
Terra access only when POLIS calls the API), and then the 144 run-specific
output packages. These can be developed in parallel before the dry-run files
return.
