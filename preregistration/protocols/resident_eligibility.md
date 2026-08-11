# Resident eligibility, recruitment, consent, and stopping protocol

Status: proposed for the new ethics application. No procedure in this file may
be used until the resident component has written approval.

## Scope

Case Study 2 is a fully online feasibility study in Suzhou, London, and Chicago.
It targets 15 analysable participants per city and permits at most 20 consented
participants per city. It does not estimate citywide preferences or compare
national populations.

## Inclusion criteria

A participant must satisfy all criteria before allocation:

1. age 18 years or older;
2. able to provide active informed consent;
3. able to complete an ethics-approved language version;
4. self-reports either usual residence within the displayed, frozen 1-km
   catchment of the relevant study-site boundary, or use of the site or its
   immediately adjoining public realm at least once per month during the
   previous six months; and
5. has not previously consented to this resident study.

The site connection is self-reported as a categorical route. Exact home or work
addresses, GPS coordinates, full postcodes/ZIP codes, and precise travel traces
are not collected.

## Exclusion criteria

Exclude before analysis for age under 18, no valid consent, no qualifying site
connection, inability to complete an approved language, confirmed duplicate,
membership of the POLIS development team, consent withdrawal, or a technical or
completion failure that leaves either mode without a fidelity rating. Do not
exclude based on criticism, low fidelity, failed comprehension, correction
count, task time, or any other outcome value.

## Recruitment and consent

Recruitment channels, advertisement text, contact routes, compensation, and any
identity verification must be exactly those approved by the relevant ethics and
local review. There is no recruitment through an authority relationship and no
claim that the study is an official municipal consultation. The resident PIS is
shown before consent. Screening begins only after active consent unless the
approved application explicitly authorises a minimal pre-consent eligibility
screen.

## Allocation and stopping

Eligible consented participants receive the next unused slot for their city in
`resident_randomisation.csv`. Slots are never skipped or reassigned because of
an outcome. Recruitment in a city stops at the first of 15 analysable records or
20 consented participants. A shortfall in one city is not filled from another.
Consent, exclusions, completions, and the stop reason are logged without storing
an exact address.

## Withdrawal

The withdrawal window, anonymisation point, contact method, deletion procedure,
and treatment of already anonymised data must match the final approved resident
PIS and consent form. Until those documents are approved, no retention or
withdrawal promise in a draft overrides institutional requirements.
