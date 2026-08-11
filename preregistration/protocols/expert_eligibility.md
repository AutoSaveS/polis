# Expert eligibility, recruitment, consent, and allocation protocol

Status: DRAFT - must be checked against the final approved PIS, consent form,
and rating rubric before preregistration freeze.

## Approved scope

- Human participants: independent professional or academic experts only.
- Approved recruitment range: 8--12 reviewers.
- Prespecified confirmatory target: 12 reviewers.
- Approved collection period: 1 August--13 October 2026.
- Mode: fully online on Wenjuanxing, in English or Chinese.
- Compensation: none.
- Public or resident participants: none within this approval. The separately
  proposed resident case is not covered and cannot start before new approval.

## Inclusion criteria

A reviewer must satisfy all of the following:

1. At least three years of professional or research experience in urban or
   landscape planning, green-infrastructure design, or urban spatial analysis,
   or a relevant postgraduate qualification with practice experience.
2. Able to provide informed consent.
3. Able to complete the rating task in English or Chinese.

## Exclusion criteria

Exclude a person before allocation when the person is a POLIS development-team
member, a direct collaborator on this project, has a declared material conflict
of interest, cannot provide informed consent, or does not satisfy the inclusion
criteria. Duplicate participation is excluded. Eligibility or ratings are not
judged by whether the reviewer supports POLIS.

## Recruitment and consent

Potential reviewers are approached through targeted email invitations to
professional practices, university departments, relevant professional bodies,
and permitted snowball referrals. There is no public advertising, payment,
coercion, or authority relationship. The invitation includes the approved PIS
and a link to the online platform. The PIS is shown again on the landing page.
No professional-background item or rating is collected until the reviewer has
actively confirmed every approved online consent statement.

## Allocation and burden

With 12 recruited reviewers, the seeded allocation assigns nine scenarios to
each reviewer and three reviewers to each scenario. Each assigned scenario
contains three anonymised intervention outputs, giving 27 outputs per reviewer
and three ratings per scenario-workflow output. Output order is independently
randomised. Within each site, scenarios are ranked by SHA-256 of
`400001:site_index:scenario_id`; ranked scenario `j` (zero based) receives slots
`((3*j+k) mod 12)+1` for `k=0,1,2`. Workflow order within an assignment is the
SHA-256 rank of `400100:expert_slot:scenario_id:workflow`. A non-study timing
pilot must demonstrate that the complete task,
including five seven-point ratings per output and the approved forced-choice
preference items, can be completed within 30--60 minutes. If it cannot, data
collection pauses and the team seeks ethics guidance before changing the task.

## Withdrawal and missingness

Reviewers may pause and resume. There is no follow-up. Identifiable data and
linked ratings may be withdrawn until anonymisation and aggregation, expected
within approximately two weeks after submission. After that point the
anonymous record cannot be located for removal. A withdrawal needs no reason.
Missingness and exclusions follow the frozen preregistration and are reported
without replacing outcome-discordant reviewers.

## Approval-version gate

The ethics notice is dated 6 July 2026, while the supplied application lists
the PIS, consent form, and rating rubric as uploaded on 8 July 2026. Before
recruitment, the PI must document that the approved record incorporates those
exact versions. The approved files must be copied into the frozen package
without silently rewriting participant-facing text.
