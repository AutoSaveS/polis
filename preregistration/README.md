# POLIS preregistration package

Status: DRAFT - NOT YET REGISTERED

This package implements the revised three-experiment, two-case-study design. It
contains no resident observations and does not claim resident ethics approval.

`STAGE1_REGISTRATION_SCOPE.md` defines the bounded first-stage protocol archive.
Run `python3 validate_preregistration.py --stage1-ready`, then
`./generate_stage1_manifest.sh`, before creating the immutable ZIP for an
external registry. A locally generated archive is not registered until the
registry returns a timestamped identifier or URL recorded in an external
receipt.

## Core files

- `POLIS_preregistration.md`: research questions, design, thresholds, stopping,
  models, exclusions, ethics gates, and reporting commitments.
- `parameters.yaml`: machine-readable settings and readiness flags.
- `scenarios.csv`: complete 36-scenario frame and Experiment 2 subset.
- `baseline_SOPs.md`: Existing, Conventional, Digital, Full POLIS, and ablation
  procedures.
- `seeds.csv`: deterministic seeds for Experiments 1--3 and both case studies.
- `inputs/need_profiles.csv` and `inputs/need_predicates.csv`: 60 analytical
  profiles and predicates, not resident statements.
- `constraints/site_constraints.csv`: official-source regulatory and policy
  screening register with separate verification and project applicability.
- `constraints/real_project_confirmation_log.template.csv`: the 34 unresolved
  project-level questions, responsible authority/professional, and evidence
  fields. Pending entries must not be guessed or generated.
- `constraints/design_parameter_tolerances.csv`: matching and deviation rules.

## Human-participant protocols

- `protocols/expert_eligibility.md`, `expert_rating_instrument.csv`, and
  `participant_data_SOP.md`: approved-scope expert procedures. Exact item wording
  remains gated on verification of the approved attachments.
- `protocols/resident_eligibility.md`, `resident_online_SOP.md`,
  `resident_data_SOP.md`, `resident_instrument.csv`, and
  `resident_randomisation.csv`: proposed resident procedures for the new ethics
  application. They are not authorised for use yet.
- `inputs/human_need_profile_collection_template.csv`: zero-row resident raw-data
  schema with one row per participant-mode. `inputs/resident_session_collection_template.csv`
  is the separate zero-row participant-session table for eligibility,
  comprehension, and procedural-experience measures. Both remain empty until
  approval and actual collection.
- `protocols/operator_roles.csv`: zero-row public roster schema. It must be
  populated with real, verified coded assignments such as `OP01` before freeze;
  names and contact details do not belong in the public roster.
- `protocols/operator_identity_linkage.template.csv` and
  `operator_verification_attestation.template.md`: restricted PI-held templates
  linking operator codes to real identities and documenting evidence checks.
  Completed copies must not be included in a public preregistration archive.
- `protocols/operator_registration_instructions.md`: public/private separation
  and evidence requirements for completing the real operator roster.
- `protocols/operator_assignment_plan.csv`: 108 balanced assignments across
  three planned slots; slots must be replaced by at least three verified coded
  operators before freeze.
- `protocols/operator_training_log.template.csv` and
  `operator_practice_task_rubric.md`: real training and qualification evidence.
- `protocols/author_threshold_inventory.csv` and
  `author_threshold_review.template.md`: complete numerical-setting inventory
  and the unsigned author/PI approval record.
- `protocols/expert_timing_pilot_SOP.md` and its zero-row log template: the
  required real non-study 30--60 minute feasibility pilot.

## Software and analysis status

- `software/model_manifest.yaml` freezes OpenAI `gpt-5.6-terra`, the Responses
  API, medium reasoning, four logical-agent roles, and the participant-data/tool
  restrictions. `software/prompts/`, `software/schemas/`, and
  `prompt_schema_manifest.csv` contain the hashed strict-output contracts. API
  access, regional data controls, and live refusal/schema preflight remain
  execution checks rather than invented evidence. A4 uses the same Terra model
  as one general-purpose agent, while `gpt-5.6-sol` is limited to a descriptive
  12-scenario appendix sensitivity check and is not an additional experiment or
  confirmatory ablation configuration.
- `software/api_preflight.py` performs an offline request-contract and refusal-
  handler check by default. With an approved project and `OPENAI_API_KEY`, run
  `python3 software/api_preflight.py --live` to send four benign synthetic
  schema checks. The script never reads participant files and never logs the
  API key. The actual project region and retention controls must be verified in
  `software/api_project_data_controls_record.md` from the supplied template.
- `analysis/synthetic_smoke_test.py` passes deterministic structural tests for
  scenario expansion, the Experiment 1 design matrix, Experiment 2 pairing, and
  resident allocation. It does not replace testing the registered R 4.3.3 CR2,
  ordinal mixed, Bradley--Terry, or agreement models.
- `analysis/confirmatory_analysis.R` is the registered R 4.3.3 analysis entry
  point. R need not be installed on the drafting machine; an exact package lock
  and successful synthetic-model preflight are mandatory before the first
  confirmatory run or inspection of real outcomes.
- `prepare_experiment1_run_manifest.py` creates the 144-row Experiment 1 queue
  and binds every row to its scenario seed and frozen city GeoPackage hash. It
  leaves all outcomes and deliverable paths blank. Existing-condition rows do
  not require an operator; the other 108 rows remain blocked until their coded
  operator assignments are PI-verified.
- `prepare_experiment1_scenario_packages.py` materialises 36 hash-bound JSON
  packages from the frozen scenario, need, predicate, source, constraint, and
  resource registers. These contain no expert or resident data and are the
  common controlled input for the manual workflows and the future POLIS API
  execution engine.
- `experiment1_run_readiness.py` is the technical Experiment 1 execution gate.
  It excludes preregistration receipts, author/PI threshold signatures,
  operator qualification, R/`renv`, and expert/resident ethics documents. It
  reports operator and API-governance records separately as nonblocking
  operational status. A nonzero exit means that a real technical component or
  the cross-device dry-run handoff is still missing.
- `analysis/experiment1_evaluator.py` computes all five frozen outcomes from a
  world model, a seven-layer design GeoPackage, and row-level need/constraint
  evidence. `experiment1_runner.py` binds one evaluation to the frozen run
  queue and verifies the world-model and cross-device Rhino export hashes.
- Rhino 8/Grasshopper runs on the fixed design workstation, not necessarily on
  this analysis computer. Every handoff must validate against
  `software/rhino_export_contract.schema.json`; the template is
  `software/rhino_export_record.template.json`. Before the first study run,
  record the fixed workstation, Rhino/Grasshopper and plug-in versions, and
  source-file hashes using `software/rhino_workstation_assets.template.json`.
  The six-domain source package, field contract, fixed-workstation SOP, and
  truthful asset-inventory command are in `software/rhino_generators/`.

## Ethics status

The expert component was approved on 6 July 2026 under application
`11000110520260706104327` for 8--12 independent experts. That approval does not
cover residents. The exact expert attachments still require documented version
confirmation. Resident recruitment, consent, screening, and data collection are
prohibited until the separate resident approval and required local permissions
are in force.

## Validation and registration

Run `python3 validate_preregistration.py` to check structure and internal
consistency. Run `python3 validate_preregistration.py --freeze-ready` to require
all approval, personnel, legal-applicability, software, analysis, and manifest
gates. Structural success is not registration readiness.

Before attempting Experiment 1, run
`.venv-polis39/bin/python preregistration/prepare_experiment1_run_manifest.py`
and then `.venv-polis39/bin/python preregistration/experiment1_run_readiness.py`.
Do not start a formal run unless the second command reports
`READY_FOR_FORMAL_EXPERIMENT_1_EXECUTION`.

`generate_preview_manifest.sh` may be used while blockers remain. Its output is
explicitly a draft integrity check and does not satisfy the final freeze gate.
Run `generate_freeze_manifest.sh` only after every readiness requirement is
actually complete.

After the strict gate passes, generate the hash manifest, archive the exact
directory, deposit it on a timestamped registry before outcome inspection, and
record the registry URL, DOI, timestamp, and archive SHA-256 outside the
immutable archive. Later changes belong in an external append-only amendments
record.

The site-constraint register is a research screening register, not legal advice
or a construction permit. Its frozen study rule determines how a constraint is
screened under recorded scenario inputs. Real-project applicability remains a
separate authority-confirmation field and cannot support a construction,
permission, or legal-compliance claim while pending.
