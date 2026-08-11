# Experiment 1 no-field-survey computational comparison SOP

## Scope

Experiment 1 compares workflow logic under a common frozen data boundary. It
does not compare field-survey quality and does not require a site visit,
topographic/cadastral survey, or resident data collection.

## Shared inputs

Every Existing, Conventional, Digital, and POLIS evaluation must use the same:

- city world-model GeoPackage and analysis CRS;
- GHSL population origins and weights;
- public GIS/OSM layers and registered imagery/remote-sensing proxies;
- scenario need profiles, constraint register, and resource cap;
- six-domain geometry generator contract;
- scenario seed and software/model freeze;
- seven-layer design export contract and five-outcome evaluator.

No workflow may add or correct a spatial input after seeing its own or another
workflow's outcome. A later correction requires a dated amendment and rerun of
all affected conditions.

## Conditions

1. **Existing**: no intervention. Construct the seven evaluator layers from the
   frozen world model and calculate all five outcomes. This is a
   scenario-specific computable baseline, not an independently generated
   planning workflow.
2. **Conventional**: apply the frozen domain rules in their registered order,
   generate one feasible template, and run one post-generation review. No LLM,
   multi-agent arbitration, equity guardian, or iterative indicator feedback is
   permitted.
3. **Digital**: run the deterministic standalone GIS/simulation/parametric
   optimiser with the scenario seed. Indicator calculations are available, but
   there is no multi-agent arbitration, provenance-aware conflict resolution,
   or Equity Guardian.
4. **POLIS**: run the frozen provenance-aware multi-agent workflow, including
   conflict detection, Equity Guardian, local indicator feedback, and
   orchestration, before exporting through the same generator contract.

## Proxy variants

The central image/remote-sensing proxy is the primary computational input.
Low and high variants must be rerun for every condition using the same workflow
settings. These are sensitivity analyses and are not additional experimental
units. Proxy values remain labelled not_measured and cannot support engineering
or survey claims.

## Regulatory screening

SUZ-C01 through SUZ-C09 are confirmed for inclusion as Experiment 1 analytical
screening rules. Confirmation covers the official rule text, source, section,
and inclusion in the research screen. It does not confirm real-project land
classification, legal applicability, permission, or compliance.

For each scenario-rule pair:

- score pass/fail only when the frozen scenario metadata activates the trigger
  and the design output supplies the required predicate value;
- exclude a trigger only when frozen metadata explicitly shows it is false;
- record not_evaluable when the trigger or predicate evidence is absent;
- never infer a trigger from imagery or from a missing field.

## Analysis

The experimental units are the 36 scenarios. Under the central input setting,
all five outcomes are evaluated for 36 Existing baselines and 108 generated
outputs, yielding 144 condition-level evaluations. Report paired
Conventional-minus-Existing, Digital-minus-Existing, and POLIS-minus-Existing
changes. The primary method contrast is POLIS minus Digital; secondary method
contrasts are POLIS minus Conventional and Digital minus Conventional.
Confidence intervals use the registered scenario-level paired bootstrap. If
either member of a pair is `not_evaluable`, omit that scenario only for that
outcome and contrast and report the evaluable denominator. Low/high proxy
results are sensitivity analyses, not additional experimental units.

## Stopping and exclusions

Use the registered retry, schema-failure, and exclusion rules. Stop a workflow
only at its registered stopping condition. A failed run remains in the process
log and may be excluded only under a prespecified technical exclusion code; it
may not be replaced because its outcome is poor.
