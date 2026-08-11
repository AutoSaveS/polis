# Preregistration: revised confirmatory evaluation of POLIS

Version 2.0.0-draft, 4 August 2026

Status: **NOT YET REGISTERED**. This is a complete candidate protocol, not a
claim that data have been collected or that the resident component has ethics
approval. It becomes a preregistration only after all freeze gates are satisfied
and the immutable package is deposited before the relevant outcomes are
inspected.

## 1. Research scope

POLIS links public evidence and frozen analytical stakeholder-need profiles to
conflict resolution, equity checks, parametric green-infrastructure design,
regulatory validation, and implementation review. The study has three
experiments and two case studies:

1. Experiment 1 compares four planning conditions on 36 fixed scenarios and
   five planning-observable outcomes.
2. Experiment 2 compares Full POLIS with five single-component ablations on 12
   fixed scenarios (72 runs).
3. Experiment 3 is a blinded online review by 8--12 approved professional or
   academic experts, with a target of 12.
4. Case Study 1 examines technical provenance, regulatory screening, controlled
   deviations, and counterfactual responses in Suzhou, London, and Chicago.
5. Case Study 2 proposes a fully online, within-participant feasibility study
   of text versus POLIS spatial need expression with residents or routine users
   connected to the three study areas.

The computational experiments use analytical profiles derived from study rules
and cited official records. They are not resident statements. Case Study 2 is
the only resident component and may begin only after a new ethics approval or
approved amendment and any required local permissions. The three bounded sites
are not representative samples of their cities or countries. The study does not
measure completed construction or physical or mental health outcomes.

The registered primary LLM is OpenAI `gpt-5.6-terra` through the Responses API.
It is used only in Experiments 1--2 and Case Study 1 with frozen analytical and
public-source inputs. It never receives expert or resident participant data.

## 2. Research questions and hypotheses

### 2.1 Experiment 1: planning outcomes

Question: under identical frozen inputs, does POLIS improve green-space access,
access equity, shade-based environmental comfort, stakeholder-need retention,
and regulatory/implementation feasibility relative to Digitally Enhanced
Planning?

For each outcome, the primary contrast is POLIS minus Digital. The five
contrasts form one Holm-controlled family at two-sided family-wise alpha 0.05.
POLIS versus Conventional, Digital versus Conventional, and POLIS versus
Existing are secondary contrasts and cannot rescue a failed primary family.

### 2.2 Experiment 2: component contribution

Question: does removing a prespecified POLIS component reduce complete target
attainment? For each of five components, Full POLIS is paired with the ablated
configuration on the same 12 scenarios. Complete target attainment is primary.
Continuous losses in the five Experiment 1 outcomes are secondary mechanism
evidence. A4 is a same-model single-agent baseline: one general-purpose
`gpt-5.6-terra` agent receives the same frozen inputs, local tools, and output
contracts but has no role separation, cross-agent handoffs, or orchestrator.

### 2.3 Experiment 3: professional validation

Question: do independent experts give POLIS outputs higher overall-integration
ratings than Digital outputs? Overall integration on a seven-point ordinal scale
is primary. Stakeholder responsiveness, spatial coherence, constructability,
and equity sensitivity are secondary. Forced-choice preferences, blinding
checks, and inter-rater agreement are supporting evidence.

### 2.4 Case Study 1: technical and regulatory validation

Question: do the registered provenance and regulatory mechanisms operate as
specified across the three bounded contexts? Trace completeness, deviation
sensitivity and specificity, review-trigger accuracy, and affected-need
recovery are descriptive; no city or population hypothesis is tested.

### 2.5 Case Study 2: online resident validation

Question: can eligible residents or routine users express and verify a
place-based need more faithfully through POLIS spatial interaction than through
a conventional text channel, and understand the link from the confirmed need
to a design decision?

Participant-confirmed fidelity is the primary resident outcome. The primary
estimand is the within-participant effect of mode. City and mode-by-city terms
describe transferability only; they are not country comparisons and will not be
interpreted as citywide or national population effects.

## 3. Experimental units and design

The computational unit is one scenario-workflow output; `scenario_id` is the
paired unit. Site, decision type, and variant are fixed blocking factors. The
complete frame is three sites by six decision types by two variants = 36
scenarios. Experiment 1 evaluates Existing, Conventional, Digital, and POLIS on
all 36 scenarios. Experiment 2 uses GE-B, AR-B, EA-B, and IP-B from each site,
crossed with Full POLIS and five ablations.

Experiment 1 is a no-field-survey computational comparison. Every workflow
receives the same frozen public-data world model, CRS, population weights,
need profiles, analytical constraint register, scenario budget, generator
library, random seed, and five-outcome evaluator. No workflow may add a site
visit, cadastral survey, resident elicitation, or measured height/width/slope
after the input freeze. Unresolved spatial dimensions are retained as
not_evaluable in the observed mode or represented by the registered central,
low, and high image/remote-sensing proxy variants in the sensitivity run.

The four conditions differ only in decision logic: Existing is a computational
no-intervention reference; Conventional is a fixed rule-order GIS/parametric
template with one-pass review; Digital is a deterministic standalone
GIS/simulation/parametric workflow without multi-agent arbitration; POLIS is
the provenance-aware multi-agent workflow with conflict detection, Equity
Guardian, local feedback, and orchestration. Thus the estimand is the
workflow-logic contrast under a common data boundary, not a field-survey
quality contrast.

The central analysis contains 36 computable Existing baseline evaluations and
108 generated outputs from Conventional, Digital, and POLIS. All five outcomes
are computed for every evaluable condition--scenario cell. Paired
Conventional-minus-Existing, Digital-minus-Existing, and POLIS-minus-Existing
changes are reported with 95% bootstrap confidence intervals. The primary
method contrast is POLIS minus Digital; secondary method contrasts are POLIS
minus Conventional and Digital minus Conventional. Existing is a fully
computable paired no-intervention baseline, but it is not an independently
generated fourth workflow. Central proxy inputs are primary; low/high reruns
are sensitivity analyses and are not additional experimental units.
Operational condition definitions and run controls are frozen in
`protocols/experiment1_no_field_comparison_SOP.md`.

Experiment 3 reuses the 108 intervention outputs from Conventional, Digital,
and POLIS. With 12 experts, each expert receives nine scenarios and 27 outputs;
each scenario-workflow output receives three independent ratings. The approved
range remains 8--12, so realised coverage and missingness will be reported when
fewer than 12 experts participate.

Case Study 2 uses a within-participant design. Each participant expresses the
same intended place-based need once in text mode and once in POLIS spatial mode.
Mode order comes from `protocols/resident_randomisation.csv`, which contains 20
preallocated consent slots per city, ten in each sequence. The target is 15
analysable participants per city (45 total), with no representative sampling
claim.

## 4. Scenario generation rules

### 4.1 Frozen source state

Source files, access dates, coordinate transformations, OSM identifiers,
world-model objects, site boundaries, constraints, need templates, prompts,
software/model identifiers, and evaluator code are frozen and hashed before
execution. No input may be edited in response to workflow performance. A later
change requires an amendment and is exploratory unless registered before the
affected outcomes are inspected.

### 4.2 Need records

Every base scenario contains exactly eight needs: two access/mobility, two
shade/comfort, one ecology, one activity/use, one maintenance/budget, and one
vulnerable-group-priority need. Exactly two are critical. Each stress scenario
inherits the eight and adds one conflicting critical need and one conflicting
noncritical high-priority need, giving ten needs and three critical needs.

Each record includes role, beneficiary, source, spatial scope, priority,
requested change, parametric implication, satisfaction predicate, and conflict
links. A critical need may be revised to a functionally equivalent predicate but
may not be rejected if the complete target is to pass. The 60 frozen analytical
records and their one-to-one predicates are in `inputs/need_profiles.csv` and
`inputs/need_predicates.csv`; none may be described as elicited resident data.

### 4.3 Conflicts, budget, and decision operations

Base scenarios contain exactly two frozen conflicts and budget multiplier 1.00.
Stress scenarios contain four conflicts and budget multiplier 0.80. At least one
conflict is spatial and one resource based.

- GE focuses on vegetation, shade, coverage, and compatible activity elements.
- AR focuses on connected accessible routes, entrances, rest, and destinations;
  the stress case activates a blocked edge.
- CU allocates limited area among circulation, activity, ecology, and shade.
- RR introduces revisions at cycle 5 (base) and cycles 5 and 10 (stress).
- EA distributes access and comfort across population units and encoded groups.
- IP activates all domains, outcomes, budget pressure, conflicts, and hard
  constraints.

## 5. Outcomes and fixed thresholds

All five computational outcomes are in [0,1], higher is better, and are computed
by frozen evaluator code independent of the operator.

### 5.1 Green-space access

`A_green` is the population-weighted proportion of eligible origins within a
1,000 m analysis catchment whose network distance to a connected entrance of a
qualifying usable green space is no more than 300 m. Target: `A_green >= 0.80`.

### 5.2 Access equity

Origin accessibility is `a_i = max(0, 1 - d_i/1000)` and is population
weighted. The finite-support-normalised weighted Gini definition in the
manuscript is used with epsilon `1e-9`. Target: `E_equity >= 0.80`.

### 5.3 Shade-based environmental comfort

Shade is evaluated on 21 June, 21 July, and 21 August at local solar times
10:00, 12:00, 14:00, and 16:00. Within-day weights are 0.20, 0.30, 0.30, and
0.20; dates are equally weighted. The effective-shade diagnostic floor is 0.50.
Target: `C_comfort >= 0.60`. This is a shade proxy, not measured thermal comfort.

### 5.4 Stakeholder-need retention

Continuous predicates pass within 2% unless stricter; point locations pass
within 5 m; polygons require intersection-over-union at least 0.80; categorical
predicates require exact match. Target: `P_ret >= 0.80` and critical-need
retention = 1.00.

### 5.5 Regulatory and implementation feasibility

`I_impl = H * S`, where `H` is one only when every evaluable hard constraint
passes and `S` is the pass proportion among evaluable non-hard predicates. Any
hard failure sets `I_impl` to zero. Target: `I_impl >= 0.95`. The nine Suzhou
instruments SUZ-C01--SUZ-C09
have been confirmed for inclusion as analytical screening rules, with their
official source, section, and conditional trigger retained in the registers.
For Experiment 1, the trigger state is read only from frozen scenario metadata
and the computational design output. A trigger shown false by that metadata is
excluded; a supported trigger is scored pass/fail; a missing or ambiguous
trigger remains `not_evaluable`. This analytical screening confirmation does
not assert that the selected parcel is legally classified, permitted, or
construction-ready. A row marked `reference_only_not_scored` is reported but
never assigned a legal threshold.

### 5.6 Common study constraints

Budget ratio is at most 1.00; cross-domain overlap is at most 0.01 m2; there are
zero disconnected accessible routes, unresolved critical conflicts, and missing
required POLIS provenance links. Common accessible-route minimum width is 1.50
m, maximum running slope is 0.05, maximum cross slope is 0.02, and circular
wheelchair turning diameter is at least 1.525 m. The 1.525 m rule supersedes the
1.50 m common value wherever circular turning is required. It is a conservative
common study rule based on the verified Chicago requirement, not a claim that
Suzhou or London law independently specifies 1.525 m.

Every jurisdiction-specific row must retain its official database, instrument,
version/effective date, section, URL, verbatim summary, applicability condition,
source-text status, frozen study-evaluator rule, real-project applicability
status, confirmation authority, and verification status in
`constraints/site_constraints.csv`. The register is a research screening tool,
not legal advice or a permit. The analytical rule may be frozen while parcel
classification, permission, exemption, area trigger, current-code status, and
competent-authority approval remain pending. Those real-project questions must
be resolved before any project-level compliance, permission, or construction-
readiness claim.

### 5.7 Resident outcomes and thresholds

After each mode, fidelity is rated from 1 (does not represent my intended need)
to 7 (fully represents my intended need). No dichotomous success threshold is
used for the primary analysis. A material correction is an addition, deletion,
spatial relocation, beneficiary change, priority change, or rejection that
changes meaning or implementation. Four comprehension items test identification
of the source need, recorded decision, affected design parameter, and review
trigger; the score is correct items divided by four. Voice, fairness, trust,
usability, and burden are separate seven-point items, not a post hoc composite.

## 6. Internal thresholds and implementation deviations

Internal feedback minimums are access 0.80, solar 0.60, shade/thermal proxy
0.60, green coverage 0.35, ecology 0.50, and budget performance 0.95. Critical
access objects require local access at least 0.70; vulnerable-use zones require
local shade/thermal proxy at least 0.50. Objective weights are 0.25, 0.10, 0.20,
0.15, 0.15, and 0.15 respectively, with parameter-departure penalty 0.10.

Equity review compares group retention rates rather than adopted counts. It uses
epsilon 0.05, inverse-access weight cap 5.0, retention-Gini alert 0.20, and a
mandatory recorded intervention or unresolved status above 0.25. Each encoded
group must retain at least 0.75 of its needs unless infeasibility is documented.

Implementation deviations use the greater of 0.10 m or 5% for continuous
dimensions, 5% for area/canopy, 2% for budget, and exact categorical matching.
Four positive cases per site are injected at 1.5 times tolerance; four null
cases use 0, 0.25, 0.50, and 0.75 times tolerance.

## 7. Baseline SOP and controlled execution

`baseline_SOPs.md` fixes common inputs, deliverables, allowed tools, prohibited
POLIS functions, operator eligibility, timing, and fidelity audits. Operator
roles must be filled with real personnel represented by codes such as `OP01` in
`protocols/operator_roles.csv` before freeze; the zero-row template does not
demonstrate staffing. Names and contact details are held only in the PI's
restricted identity-linkage table and are not deposited in the public archive.
The coded roster must still contain real evidence of experience, training,
practice-task completion, assignment, conflicts, and PI verification.

The frozen assignment plan uses three operator slots for the 108 active
workflow assignments (36 scenarios times Conventional, Digital, and POLIS).
Within every scenario the three workflows use three different slots; across the
full frame each slot receives 12 assignments per workflow. Before execution,
`OP_SLOT01`--`OP_SLOT03` must be mapped to at least three real, independently
qualified coded operators. Planned slots are not evidence that operators exist.

The master seed is 20260804. Experiment, expert, case, resident-order,
bootstrap, and permutation seeds are in `seeds.csv`. Runtime timestamps are not
used. `PYTHONHASHSEED` is fixed and OR-Tools uses one search worker. Study seeds
govern scenario construction, allocation, deterministic local tools, bootstrap,
and permutation; they do not make hosted LLM generation deterministic.

All four POLIS logical agents use OpenAI `gpt-5.6-terra` through
`/v1/responses`, with `reasoning.effort=medium`,
`reasoning.context=current_turn`, `store=false`, and one frozen strict JSON
Schema per role. No temperature, top-p, or provider seed is sent or claimed.
Hosted tools, web search, file search, and OpenAI's provider multi-agent beta are
disabled; the four roles are coordinated by the frozen POLIS workflow. The
first schema-valid, non-refusal response is primary. Selective regeneration for
quality is prohibited. One retry is allowed only after schema validation fails,
using the identical frozen input plus the validation error. Raw requests,
responses, refusal/validation states, retry links, returned model identifiers,
usage metadata, and hashes are retained. Prompts, schemas, request settings, and
their SHA-256 hashes are under `software/`.

As a descriptive robustness check, Full POLIS is rerun with `gpt-5.6-sol` on
the same 12 Experiment 2 base scenarios. This is not a fourth experiment or a
seventh Experiment 2 configuration. It has no hypothesis test and cannot be
used to select or replace the registered primary model. The appendix reports
schema-valid response rate, five-outcome direction concordance, constraint-
failure-category agreement, and provenance completeness.

Expert allocation uses seed 400001. Within each site, scenarios are ranked by
SHA-256 of `400001:site_index:scenario_id`; zero-based ranked scenario `j` is
assigned expert slots `((3*j+k) mod 12)+1` for `k=0,1,2`. Thus every scenario
has three slots, every expert slot has three scenarios per site and nine total.
Within each expert-scenario assignment, Conventional, Digital, and POLIS are
ranked by SHA-256 of `400100:expert_slot:scenario_id:workflow`. Resident order
uses fixed city seeds 800001--800003 and a SHA-256 ranking of the 20 slots; the
frozen realised sequences are stored in the randomisation CSV. Allocation is by
consent slot, before any outcome is known.

## 8. Stopping rules

### 8.1 Computational runs

A run first reaches target when every quality condition passes in two
consecutive formal evaluations; the first passing state is recorded. A run
stops at the earliest of target confirmation, 30 revision cycles, 120 elapsed
minutes, eight professional person-hours, or 120 scenario compute-minutes.
There is no interim futility stopping. A capped run is retained as target not
reached. No scheduled run is added or removed because of observed performance.

### 8.2 Expert review

Recruitment follows the approved 8--12 range and stops at 12 consented eligible
experts or the approved collection end, whichever occurs first. No additional
expert is recruited in response to rating direction. Timing-pilot failure pauses
recruitment and requires ethics guidance before task modification.

### 8.3 Resident case

For each city separately, recruitment stops at 15 analysable participants or 20
consented participants, whichever occurs first. Across-city recruitment does not
replace a shortfall in another city. The cap is independent of outcomes. No
resident may be screened, consented, or enrolled before resident ethics approval
and required local permissions are in force.

## 9. Statistical models

### 9.1 Experiment 1

For each outcome:

`outcome ~ workflow + site + decision_type + variant`

OLS is fitted with scenario-clustered CR2 standard errors. The five
POLIS-minus-Digital contrasts are Holm adjusted. Raw paired differences and
10,000 stratified bootstrap intervals (seed 600001) are reported. Boundary
values remain 0 or 1; no transformation, winsorisation, or outcome-driven model
switch is allowed. Fractional-logit GEE is a prespecified sensitivity model.

### 9.2 Experiment 2

Full versus each ablation target attainment is tested with exact paired McNemar
tests, Holm adjusted across five components. Continuous outcomes use
`outcome ~ configuration + site + decision_type` with scenario-clustered CR2
standard errors; Full-minus-ablation contrasts are Holm adjusted within each
outcome.

### 9.3 Experiment 3

The primary cumulative-link mixed model is:

`overall_integration ~ workflow + (1 | expert_id) + (1 | scenario_id)`

with seven ordered categories and logit link. POLIS versus Digital is primary;
POLIS versus Conventional is secondary. The same model is used for four
secondary dimensions with Holm adjustment. Forced-choice preferences use a
Bradley-Terry model with scenario-clustered bootstrap intervals. Fleiss kappa is
computed only for outputs with exactly three completed ratings; ordinal
Krippendorff alpha with 10,000 bootstrap samples is sensitivity evidence.

### 9.4 Case Study 1

Trace completeness, sensitivity, specificity, trigger accuracy, and recovery
are reported per site and pooled as counts, proportions, and exact
Clopper-Pearson 95% intervals. No hypothesis test or ranking of cities is used.

### 9.5 Case Study 2

The primary cumulative-link mixed model is:

`fidelity ~ mode * city + order + (1 | participant_id)`

with seven ordered categories and logit link. The mode coefficient is the
primary estimate. City and interaction terms are descriptive. The model is fit
once to all eligible paired records. No missing fidelity is imputed. Model
convergence, threshold ordering, random-effect variance, and proportional-odds
diagnostics are reported; diagnostic failure does not license an unregistered
replacement primary model. City-stratified paired distributions and paired
median differences are sensitivity summaries.

Correction counts, task time, four-item comprehension, voice, fairness, trust,
usability, and burden are secondary descriptive outcomes with uncertainty
intervals. Comprehension item nonresponse remains missing rather than incorrect.
Free text is coded by two bilingual coders using a frozen codebook; disagreements
are adjudicated without access to fidelity or mode-effect results.

Resource measures collected with Experiment 1 are reported only in the
manuscript appendix as descriptive reproducibility information. They are not a
fourth experiment, have no efficiency hypothesis, and support no quality-matched
or resource-matched causal claim.

## 10. Exclusion, failure, and missing-data rules

### 10.1 Computational runs

- A scenario is invalid only if a required frozen input is absent, corrupt,
  hash-mismatched, or cannot be transformed to the frozen coordinate system. It
  is excluded from all workflows and not replaced.
- A software, API, renderer, or schema failure may be rerun once with identical
  input and seed. A persistent failure is target not reached, not an exclusion.
- A material SOP violation may be rerun once after blinded audit. Both runs and
  the reason remain logged.
- Poor quality, an extreme value, high resource use, target failure, or conflict
  with the hypothesis is never an exclusion ground. No outlier is removed.

### 10.2 Experts

Experts are excluded only for failed eligibility, material conflict, duplicate
participation, consent withdrawal, or failure to rate any output. Item-level
missingness is not imputed. A scenario remains in the expert model with at least
two completed ratings. If over 10% of primary ratings are missing or a scenario
has fewer than two ratings, the complete-case model is labelled sensitivity and
coverage is reported; outcome-discordant experts are not replaced.

### 10.3 Residents

Eligibility requires age 18 or older, informed consent, an approved study
language, and self-reported connection defined as residence within the displayed
frozen 1-km catchment or use of the site/immediately adjoining public realm at
least monthly during the previous six months. Exact address is never requested.

A participant is excluded from the primary paired analysis only for consent
withdrawal, failed eligibility, confirmed duplicate, or technical
failure/non-completion leaving either mode without fidelity. A completed low
rating, many corrections, failed comprehension, long task time, or criticism of
POLIS is never an exclusion ground. Available secondary responses are retained
only where consent and the approved missing-data rules permit. Exclusion counts
and reasons are reported by city and sequence.

## 11. Human-participant procedures and data governance

The expert component was approved on 6 July 2026 under application
`11000110520260706104327`, for 8--12 independent professional or academic
experts only. The exact approved PIS, consent form, and rubric must be verified
against the approval record before recruitment; generated or later-edited files
must not be represented as approved attachments. The current evidence and file
hashes are recorded in `ethics/expert_attachment_version_audit.md`; its finding
is `NOT_CONFIRMED_BY_APPROVAL_RECORD` and does not satisfy the approval gate.

The resident component is **not covered** by that approval. Its protocol,
information sheet, consent form, language versions, recruitment route,
cross-jurisdiction transfer, retention, withdrawal, and repository-sharing
rules must be approved before use. Until then, `resident_ethics.status` remains
`PENDING_NEW_APPLICATION`, recruitment and data collection are prohibited, and
the human-need data template must contain no participant rows.

Expert data follow `protocols/participant_data_SOP.md`; resident data follow
`protocols/resident_data_SOP.md` after approval. Direct identifiers and linkage
files are stored separately with restricted access. Raw, pseudonymised, or free-
text participant data are not uploaded to generative-AI services. No expert
rating, expert free text, resident need statement, resident free text, direct
identifier, or participant linkage record is transmitted to OpenAI. Case Study
2 uses the approved online interface and deterministic local transformation
rules rather than the registered LLM. Public sharing
is limited to data that are fully anonymised, disclosure reviewed, consented for
sharing, and permitted by the applicable approval and data-protection rules.

## 12. Blinding, integrity, and reporting

Expert outputs omit workflow names and branded traces and use common scale,
viewpoint, resolution, annotation density, and colour rules. Blinding beliefs
are collected after ratings and never determine exclusion. Resident mode cannot
be blinded; order is counterbalanced and modelled.

Outcome labels remain hidden from operators and SOP auditors until logs are
sealed. Analysis code is first run on synthetic data. All scheduled runs,
persistent failures, caps, exclusions, withdrawals, missing items, and amendments
are reported. All five computational outcomes and the resident primary outcome
are reported regardless of significance. No composite wellbeing score is added.
Exploratory analyses are labelled and cannot change confirmatory conclusions.

## 13. Registration and freeze gate

Structural validation and registration readiness are separate. A structurally
valid draft may still be blocked from freeze. Before registration, every
readiness flag in `parameters.yaml` must be true, all required files must exist,
the operator roster must contain real qualified coded assignments, the frozen
study-level constraint rules must be complete, approved expert attachments must be verified,
resident ethics/permissions/translations must be approved, the R 4.3.3 analysis
specification must be frozen, and the model manifest must be frozen.

The registered confirmatory runtime is R 4.3.3. A drafting machine need not have
R installed. Before the first confirmatory run and before inspecting any real
outcome or participant result, the team must archive the exact package lock or
container digest and pass the CR2, cumulative-link mixed, Bradley--Terry, and
agreement analyses on synthetic data. Failure of this execution preflight
requires a dated preregistration amendment before real-result analysis.

Real-project legal applicability is tracked separately under
`implementation_readiness`. It does not block preregistration of this analytical
study, but while false it prohibits claims of legal compliance, permission, or
construction readiness for any case-study site.

Run `python3 validate_preregistration.py` for structural validation and
`python3 validate_preregistration.py --freeze-ready` for the stricter gate.
After all gates pass, generate a SHA-256 manifest and deposit an immutable
archive before inspecting the affected outcomes. Later changes are appended to
an external copy of `amendments.csv`; the registered archive is never replaced.
