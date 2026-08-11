# Registration checklist

The draft may pass structural validation while remaining ineligible for freeze.
Every unchecked item below must be completed with real evidence, not by the
existence of an empty template.

## Scientific and technical freeze

- [ ] Authors approve every numerical threshold in `parameters.yaml`.
- [x] The 36-scenario frame and 12-scenario ablation subset are fixed.
- [x] The 60 analytical need profiles and 60 predicates are populated and
  explicitly distinguished from resident data.
- [x] OpenAI `gpt-5.6-terra`, Responses API settings, four role prompts, strict
  schemas, model-data boundaries, and artifact hashes are frozen.
- [x] A4 is frozen as a same-Terra single-agent baseline; `gpt-5.6-sol` is
  restricted to the same 12 scenarios as a descriptive appendix sensitivity
  check with no hypothesis test or model selection.
- [ ] Real operators, eligibility evidence, training, conflicts, and scenario
  assignments are recorded under coded IDs in `protocols/operator_roles.csv`.
- [x] A balanced 108-row plan assigns three different operator slots within each
  scenario and 12 assignments per workflow to each of three slots.
- [ ] At least three real qualified operators replace the planned slots and
  complete the training log and non-study practice assessment.
- [x] The public roster excludes names and contact details; the PI has restricted
  identity-linkage and verification-attestation templates.
- [ ] The PI has completed the restricted identity linkage, verified the
  supporting evidence, and signed the attestation; completed private records
  are not included in the public archive.
- [x] The deterministic Python structural smoke test passes on synthetic data.
- [x] R 4.3.3 and `analysis/confirmatory_analysis.R` are frozen as the registered
  confirmatory runtime and entry point.
- [ ] Before the first confirmatory run or real-result inspection, the R 4.3.3
  CR2, cumulative-link mixed, Bradley--Terry, and agreement models run
  successfully on synthetic data under an archived package lock/container.
- [ ] Before the first API run, the project/region, data-retention controls,
  refusal handling, and every strict schema pass a documented non-study
  preflight; no participant data are used.
- [x] The offline API request-contract and local refusal-handler preflight is
  scripted using synthetic inputs only.
- [ ] Four live Terra strict-schema checks pass and the verified API project,
  region, and retention-control record is archived without credentials.

## Regulations and sites

- [x] Every populated regulatory number is linked to a named official database,
  instrument, version, section, and official URL.
- [x] Every constraint has a frozen analytical screening rule, missing-trigger
  rule, and separate real-project applicability field. `SUZ-C10` remains
  reference-only because exact GB 55019 clauses were not extracted.
- [ ] Before any legal-compliance, permission, or construction-readiness claim,
  a competent authority or qualified local professional resolves every pending
  parcel classification, permission, exemption, area trigger, current-code, and
  real-project applicability field. This implementation gate does not convert
  unknown facts into study assumptions.
- [ ] Final site boundaries, coordinate systems, resident 1-km catchments, and
  online stimulus assets are versioned and hashed.

## Expert ethics and implementation

- [x] Approval metadata are recorded: application
  `11000110520260706104327`, approved 6 July 2026, for 8--12 experts.
- [ ] The approval record is confirmed to include the exact PIS, consent form,
  and expert rubric intended for use; approved copies and version confirmation
  are archived under `ethics/approved/`.
- [x] The currently available local PDFs, hashes, creation provenance, and the
  `NOT_CONFIRMED_BY_APPROVAL_RECORD` finding are documented in
  `ethics/expert_attachment_version_audit.md`.
- [ ] A non-study timing pilot confirms that 27 outputs and preference items fit
  the approved 30--60 minute session.
- [x] The timing-pilot SOP, complete-task definition, pass rule, and zero-row log
  are frozen without fabricating pilot observations.
- [ ] Exact approved bilingual item wording is imported without rewriting.

## Resident ethics and implementation

- [ ] A new resident ethics application or amendment is approved. The current
  expert approval does not cover residents.
- [ ] Approved resident PIS, consent form, recruitment materials, language
  versions, compensation, withdrawal, retention, and sharing rules are archived.
- [ ] Site-specific institutional permissions and cross-jurisdiction data-
  protection/transfer requirements are resolved.
- [x] Eligibility, per-city stopping, fixed order allocation, primary fidelity,
  four comprehension items, exclusions, and no-imputation rules are specified.
- [ ] Translation, interface accessibility, device compatibility, and session
  timing are piloted on non-study data and approved where required.
- [x] The resident data template contains zero participant rows.

## Deposit

- [x] `python3 validate_preregistration.py` passes.
- [ ] `python3 validate_preregistration.py --freeze-ready` passes.
- [ ] `generate_freeze_manifest.sh` is run after every file is final.
- [ ] A read-only archive is deposited before relevant outcome inspection.
- [ ] Registry URL, UTC timestamp, DOI, and archive SHA-256 are recorded outside
  the immutable archive.

Working status on 4 August 2026: the protocol structure has been updated to
three experiments and two case studies. Registration remains blocked by resident
ethics approval, approved-document version confirmation, real coded operator
assignment, expert timing evidence, and author/PI confirmation. Model selection,
prompts, and schemas are frozen; API and R live preflights remain execution
gates. Real-project regulatory applicability remains an
implementation/compliance-claim blocker, not a reason to fabricate study facts.
