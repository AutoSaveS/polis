# Baseline and POLIS standard operating procedures

Status: DRAFT - freeze with the preregistration archive.

## 1. Common controls

Every workflow receives the same scenario package: site boundary, source
layers, eight or ten substantive need records, constraint file, normalised
budget, output specification, and stopping limits. Need wording may be
reformatted for a workflow, but beneficiaries, spatial scope, priority,
satisfaction predicate, and conflicts may not change.

All workflows must return the same deliverables:

1. final geometry in the frozen coordinate reference system;
2. parameter table and bill of quantities;
3. disposition of every input need as retained, revised, or rejected;
4. regulatory and buildability checklist;
5. process log with active person-minutes, elapsed time, handoffs, checks,
   revisions, software, and compute use. These resource fields support
   descriptive appendix reporting only.

The frozen evaluator computes the five outcomes once after submission. They are
not returned to any workflow for revision or stopping. Operators cannot inspect
another workflow's output for the same scenario before submission.

## 2. Operators, training, and allocation

- Operators must have at least one year of relevant planning, GIS, landscape,
  architecture, or parametric-design experience.
- Each operator completes a two-hour workflow-specific training and one
  non-study practice task.
- Scenario-workflow order is counterbalanced with the frozen seeds.
- An operator may work in more than one workflow, but never on the same
  scenario in more than one workflow.
- Operator identity is logged and included only in sensitivity analyses.
- Help from the research team is limited to documented software or file-access
  faults. Substantive design advice is prohibited.

## 3. Timing rules

- Active time starts when the scenario package is opened.
- Breaks over two minutes pause active time but not elapsed time.
- Parallel work is summed as person-time and separately recorded as elapsed
  time.
- A formal revision cycle begins when a submitted candidate is reopened after
  a compliance, stakeholder, or indicator review.
- The common cap is 30 revision cycles, 120 elapsed minutes, eight professional
  person-hours, or 120 scenario compute-minutes, whichever occurs first.
- Resource states are logged at each formal evaluation; no resource-matched or
  quality-matched confirmatory comparison is performed.

## 4. Existing condition

Purpose: no-intervention reference, not an active planning workflow.

Procedure:

1. Load the frozen existing geometry and attributes.
2. Apply no new design elements and perform no conflict arbitration.
3. Evaluate the existing condition with the same frozen outcome code.
4. Resource use is not used as a confirmatory outcome.

Prohibited: geometric repair, requirement accommodation, or removal of an
existing constraint violation.

## 5. Conventional planning

Allowed tools: static site survey/map package, PDF regulatory documents,
spreadsheet, 2D CAD, email-style handoff template, and calculator.

Procedure:

1. Review the site package and tabular need list.
2. Manually annotate needs on the site plan.
3. Produce a 2D CAD proposal and parameter/bill-of-quantities table.
4. Conduct one manual stakeholder-need review.
5. Conduct one post-design regulatory and buildability review.
6. Revise under the manual review criteria until a stopping cap is reached or
   the operator records completion.
7. Export the common deliverables.

Prohibited: shared object graph, automated conflict detection, vulnerability
weighting, algorithmic arbitration, live parametric indicator feedback,
automated repair, or machine-readable evidence-to-parameter provenance.

## 6. Digitally enhanced planning

Allowed tools: all conventional tools plus GIS, environmental simulation, and
Rhino/Grasshopper. Tools remain separate and handoffs are manual.

Procedure:

1. Inspect site layers in GIS and manually transfer selected evidence to the
   design environment.
2. Encode the same substantive needs in a spreadsheet or drawing annotation.
3. Create design geometry in CAD/Rhino/Grasshopper.
4. Export geometry to each frozen simulation tool.
5. Manually compare simulation, GIS, need, budget, and regulatory outputs.
6. Revise under the available tool indicators until a stopping cap is reached
   or the operator records completion.
7. Export the common deliverables.

Prohibited: automatic cross-tool object identifiers, automatic spatial/resource
conflict detection, Equity Guardian intervention, orchestrated arbitration,
live location-specific multi-domain feedback, or continuous provenance.

## 7. Full POLIS

Allowed tools: frozen POLIS world model, four coordination agents,
Rhino/Grasshopper generators, frozen indicator functions, constraint
checker, and provenance recorder.

Procedure:

1. Validate source hashes, required fields, object links, and constraints.
2. Encode each frozen need as a demand record without changing its substantive
   predicate.
3. Run conflict detection and Equity Guardian checks after every demand event.
4. Record compromise, equity-prioritised, phased, retained, revised, and
   rejected decisions with source links.
5. Translate the resolved demand set into design parameters.
6. Generate the candidate design and compute only the six internal indicators.
7. Generate alternatives when a prespecified condition fails; do not adopt an
   alternative automatically.
8. Select from feasible alternatives using the frozen objective weights and
   departure penalty.
9. Stop only under the prespecified success rule or common cap.
10. Export the common deliverables and complete provenance trace.

Every logical agent uses OpenAI `gpt-5.6-terra` through `/v1/responses` with
`reasoning.effort=medium`, `reasoning.context=current_turn`, `store=false`, and
its frozen strict JSON Schema. No temperature, top-p, or provider seed is sent
or claimed. Hosted tools, web/file search, provider multi-agent beta, and
participant data are prohibited. The primary response is the first
schema-valid, non-refusal response. Regeneration for substantive quality is
prohibited. A schema-invalid response may be retried once with the same frozen
input and an automatically generated validation error; both raw responses and
request/response metadata are retained. Study seeds govern local construction,
allocation, and analysis but do not make hosted generation deterministic.

## 8. Ablations

Experiment 2 uses the full POLIS SOP except for the single prespecified removal.
No compensating functionality may be introduced.

- `A1`: remove the shared object/world-model coupling; pass layers through
  separate keyed files.
- `A2`: disable automated conflict detection; retain only conflicts explicitly
  supplied in the scenario package.
- `A3`: disable vulnerability weighting, adoption-Gini alerts, and equity
  intervention.
- `A4`: replace the four-role workflow with one general-purpose
  `gpt-5.6-terra` agent using the same frozen inputs, local tools, and output
  contracts; disable role separation, cross-agent handoffs, and orchestration.
- `A5`: disable location-specific indicator feedback during revision; compute
  outcomes only after final submission.

The model-sensitivity appendix reruns Full POLIS with `gpt-5.6-sol` on the same
12 Experiment 2 base scenarios. It is descriptive only, is not a seventh
Experiment 2 configuration, adds no hypothesis test, and cannot be used to
select or replace the registered primary model.

## 9. SOP fidelity audit

An auditor who did not operate the task checks tool use, timestamps, handoffs,
and prohibited functions before outcome labels are revealed. A material SOP
violation is recorded when it changes available evidence, automation, time, or
substantive requirements. A hosted-model output is not replaced after a
material SOP violation; the original run and reason remain in the audit log.
One same-seed rerun is permitted only for a deterministic local-tool execution
fault, and both records are retained.
