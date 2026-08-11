# Fully online resident session SOP

Status: proposed for ethics review; prohibited from use before approval.

The entire resident session is fully online.

## 1. Pre-launch gate

Before opening recruitment, the PI documents: resident ethics approval or an
approved amendment; approved PIS, consent, recruitment, language versions, and
data plan; any required site/institutional permissions; frozen site boundaries
and 1-km catchments; accessibility and device testing; stimulus hashes; the
randomisation list; and a synthetic-data analysis test. Any material change
after approval is reviewed before use.

## 2. City stimulus package

Each city uses one version-controlled package with: site boundary and 1-km
eligibility catchment, neutral map, selected images or renderings, neutral site
description, analytical context, and the same interface layout. Asset filename,
language, hash, and approval status are recorded in the stimulus manifest before
freeze. Images must not reveal private individuals or imply implementation.

## 3. Session sequence

1. Show the approved resident PIS and collect active consent.
2. Apply the eligibility screen in `resident_eligibility.md`; collect no exact
   address or precise coordinates.
3. Assign the next unused city slot and its frozen mode order.
4. Present the common city stimulus package.
5. In the first mode, ask for one specific place-based green-infrastructure need.
6. Display the generated structured need record. Collect the 1--7 fidelity
   rating before correction, then allow confirmation or correction.
7. Repeat steps 5--6 in the second mode for the same intended need. The second
   response may refer back to the participant's intention but may not display
   the first mode's structured output before its fidelity rating is recorded.
8. Show the standardised provenance trace linking the participant-confirmed
   record to one design decision and collect four comprehension items.
9. Collect voice, fairness, trust, usability, burden, optional comment, and the
   approved debrief. State that no displayed design is promised for delivery.

## 4. Mode implementation

Text mode provides a neutral text box and no spatial pin, polygon, automated
spatial prompt, or POLIS structuring feedback before submission. POLIS spatial
mode provides the registered map interaction and structured prompts. Both modes
use the same site information, task goal, maximum response time if any, and
structured-record schema. Fidelity is always participant-confirmed and recorded
before correction.

## 5. Technical events

The platform logs mode start, submission, fidelity response, correction, and
completion timestamps. A disconnected session may resume at the last completed
page if the approved platform supports it. A mode is incomplete when no fidelity
rating is recorded. Do not reconstruct a missing primary rating from comments or
system logs. Platform faults and repeats are logged; duplicate substantive
responses are not silently merged.

## 6. Coding and quality control

A material correction changes meaning or implementation through addition,
deletion, spatial relocation, beneficiary change, priority change, or rejection.
Two bilingual coders independently classify correction type and qualitative
failure-mode codes using the frozen codebook. They are blinded to the other
mode's fidelity and to aggregate model results during coding. Disagreements are
adjudicated and all versions are retained.

## 7. Cross-city comparability

Task order, randomisation logic, variable definitions, response scales, and
interface layout are constant across cities. Only approved language and
site-specific stimuli vary. Translation uses forward translation, independent
review, reconciliation, and a version log. Results are feasibility evidence for
the three online site-connected samples, not representative consultation.
