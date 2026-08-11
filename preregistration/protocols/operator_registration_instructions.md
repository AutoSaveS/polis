# Operator registration instructions

## Public preregistration record

Use `operator_roles.csv` for the public/frozen record. Each real operator is
represented by a stable code such as `OP01`; do not enter names, email addresses,
telephone numbers, signatures, or other direct identifiers in this file.

For each coded operator, record only verified facts:

- authorised workflow(s);
- years and basis of relevant planning, GIS, landscape, or parametric-design
  experience (minimum one year under the frozen SOP);
- completion time for the two-hour workflow-specific training;
- non-study practice-task ID and pass result;
- scenario-assignment file;
- conflict-check completion; and
- PI verifier and verification date.

Student-researcher or author status alone does not establish operator
eligibility. A person is not entered as qualified until every required check is
supported by a real record.

## Restricted identity record

Create a controlled copy of `operator_identity_linkage.template.csv` outside the
public preregistration archive. This restricted PI-held file must contain the
real name and institutional contact corresponding to each operator code. Access
is limited to authorised study-management personnel under the approved data-
management arrangements.

The PI completes `operator_verification_attestation.template.md` after checking
the underlying evidence. The public roster, restricted linkage table, training
records, practice output, assignment record, conflict declaration, and PI
attestation must all refer to the same stable operator code.

## Freeze rule

Set `readiness.operator_roster_complete` and
`readiness.operator_identity_and_evidence_verified_by_pi` to `true` only after
the public coded roster contains all planned assignments and the PI has verified
the restricted supporting records. Never populate either file with assumed
names, experience, training dates, pass results, or signatures.
