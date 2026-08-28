# Case Study 2 interface — amendment changelog

Date: 2026-08-25
Scope: `preregistration/case2_interface/` (index.html, app.js, styles.css) and
`preregistration/ingest_case2_exports.py`.
Trigger: local test report `case2_local_test_report.md` (issues 1–6, P0 set).

**Frozen materials untouched.** No file under `preregistration/case2_kit/`
(randomization.csv, stimuli/{SUZ,LON,CHI}/, the four data-entry templates) and
no protocol document was modified. The ingest script was minimally extended
(change 2 below) because the export schema changed; the extension writes an
*additional* file and leaves the four frozen template layouts unchanged.

Export schema version: `case2-v1` → `case2-v2`.

---

## 1. Fidelity rating enforced before correction (report issue 1)

- SOP clauses: `resident_online_SOP.md` §3 step 6 ("Collect the 1–7 fidelity
  rating before correction, then allow confirmation or correction"), §4
  ("Fidelity is always participant-confirmed and recorded before correction"),
  §5 ("A mode is incomplete when no fidelity rating is recorded").
  Instrument items: RES-F01, RES-CF1.
- Before: rating, confirm/correct dropdown and correction textarea shared one
  page with a single submit and a single merged timestamp `t`; a correction
  could be typed before rating.
- After: the record check is two sequential screens.
  - Step A (`record_fidelity`): structured record + RES-F01 1–7 rating only.
    Submission requires a rating; it stamps `t_fidelity` and event
    `{mode}_fidelity`, and the rating is locked (no back navigation; step B
    states the locked value).
  - Step B (`record_confirm`): confirm / correct / reject plus the RES-CF2
    verbatim. It is unreachable until step A is submitted, so a correction
    cannot precede the rating by construction. Submission stamps `t_confirm`
    and event `{mode}_confirm`.
- Files: index.html (`record_fidelity` / `record_confirm` sections), app.js
  (`showRecordFidelity`, `btn_fidelity_next`, `showRecordConfirm`,
  `btn_record_next`).

## 2. Per-event timestamps and export schema case2-v2 (report issue 2)

- SOP clause: §5 "The platform logs mode start, submission, fidelity response,
  correction, and completion timestamps."
- Export now carries a named ISO-8601 event map `events`:
  `consent_given`, `screener_completed`, `{text|spatial}_start`,
  `{text|spatial}_submit`, `{text|spatial}_fidelity`, `{text|spatial}_confirm`
  (the confirm/correct/reject action, i.e. the SOP "correction" event),
  `comprehension_start`, `comprehension_complete`, `experience_complete`,
  `session_complete`. Each response block also carries `t_mode_start`,
  `t_submit`, `t_fidelity`, `t_confirm` (legacy `t` kept = `t_confirm`).
  First occurrence wins, so resumed sessions keep original event times.
- `ingest_case2_exports.py` extension (documented in its docstring): the four
  frozen templates have no columns for per-event times, so events are written
  to an additional `case2_kit/events_log.csv`
  (participant_code, event, timestamp_utc), deduplicated on
  (participant_code, event) across re-runs. v1 exports without `events` still
  ingest unchanged; all previous column mappings are untouched.
- Files: app.js (`ev()`, `S.events`, `exportJSON`), ingest_case2_exports.py.

## 3. Disconnect / resume and post-completion cleanup (report issue 3)

- SOP clause: §5 "A disconnected session may resume at the last completed page
  if the approved platform supports it." Data minimisation per
  `resident_data_SOP.md`.
- Before: every step autosaved to localStorage but nothing ever read it back;
  a reload returned to the consent page and the slot was lost.
- After: on load, an incomplete autosaved session for a listed code raises a
  resume banner (code shown; "Resume where I left off" / "Discard and start
  over"). Resume restores state (answers, mode order, stage, pending record,
  event times), reloads the city package, and re-enters the last completed
  step via `resumeAt()`. Completed steps' answers are intact; the step in
  progress restarts empty, consistent with "resume at the last completed
  page". localStorage is wiped after completion + export (`wipe()` at finish)
  and on ineligible exits, so no study data remains on the device.
- Files: app.js (`save`, `wipe`, `offerResume`, `resumeAt`), index.html
  (`resume_banner`), styles.css (`.banner`).

## 4. Screener aligned with the frozen eligibility instrument (report issue 4)

- SOP clauses: §3 step 2 (apply `resident_eligibility.md`; no exact address or
  precise coordinates collected) and §2 (1-km eligibility catchment part of
  the city stimulus package). Instrument items RES-S01 (18+), RES-S02
  (site connection), RES-S03 (duplicate screen); eligibility criteria 4–5 and
  the duplicate exclusion in `resident_eligibility.md`.
- Before: five ad-hoc connection options (including non-qualifying "work
  nearby"), no "neither" route, no duplicate question; `eligible` and
  `duplicate_check_passed` exported as empty strings; no catchment shown.
- After:
  - RES-S02 uses exactly the frozen categories `resident_within_1km`,
    `routine_user_monthly_6m`, `neither`. Choosing `neither` ends the session
    on a graceful ineligible page and retains no data.
  - RES-S03 duplicate question added ("Have you previously consented…");
    answering yes ends the session as ineligible, no data retained.
  - Eligible sessions export `eligible=1`, `duplicate_check_passed=1`,
    `connection_type=<frozen category>`, filling the previously empty
    screener-template columns.
  - The 1-km catchment is displayed on the consent page once a listed code is
    entered: a labelled canvas drawn directly from the frozen `site.geojson`
    (1-km circle around the site centroid + dashed site boundary). No CDN or
    network dependency, so it also serves as the static fallback.
- Files: index.html (consent/ineligible sections, `catchment_wrap`), app.js
  (`btn_consent`, `drawCatchment`), styles.css (`canvas.catchment`).

## 5. Reject option in the record check (report issue 5)

- Instrument items: RES-CF1 (`confirm|correct|reject`), RES-CF2 (conditional
  verbatim, "Code only when correct or reject is selected"); SOP §6 counts
  rejection among material-correction types.
- Before: only confirm/corrected existed; rejecting a record was impossible.
- After: step B offers Confirm / It needs correction / Reject this record.
  Export writes `substantive_response` ∈ {confirm, correct, reject} per the
  codebook (alongside the template-compatible `confirmed_or_corrected`
  value). Because RES-CF2 is *conditional-required* — collected whenever
  correct **or** reject is selected — the verbatim box uses the frozen RES-CF2
  prompt ("Please state the correction needed.") and is required for both
  correct and reject; it is not shown for confirm. (An earlier draft of this
  amendment made the reject reason optional; that did not match RES-CF2's
  conditionality and was corrected on 2026-08-25.)
- Files: index.html (`rec_confirm`, `rec_corrbox`), app.js
  (`rec_confirm.onchange`, `btn_record_next`).

## 6. PIS and debrief embedded in the interface (report issue 6)

- SOP clauses: §3 step 1 ("Show the approved resident PIS and collect active
  consent"), §3 step 9 (approved debrief; "State that no displayed design is
  promised for delivery"), §1 pre-launch gate (approved PIS/consent wording
  required before use). `resident_eligibility.md`: "The resident PIS is shown
  before consent."
- Before: only an "I have read the PIS" checkbox; completion page had no
  debrief and the no-commitment statement was not restated at the end.
- After: a scrollable PIS region sits above the consent checkboxes, and the
  completion page shows a debrief box that restates: "no design shown in this
  study is a commitment to build, and nothing you saw is promised for
  delivery." Because no ethics-approved wording exists yet, the interface
  deliberately ships placeholders instead of invented consent text. **All
  placeholders must be replaced with approved wording before launch:**
  - `[[PENDING APPROVED PIS TEXT - REPLACE BEFORE LAUNCH]]` plus the six
    section stubs `[[PENDING APPROVED PIS: PURPOSE / PROCEDURE / VOLUNTARY +
    UNPAID / DATA HANDLING / WITHDRAWAL / CONTACTS]]` (consent page);
  - `[[PENDING APPROVED DEBRIEF TEXT - REPLACE BEFORE LAUNCH]]` (completion
    page);
  - `[[PENDING APPROVED INELIGIBILITY WORDING - REPLACE BEFORE LAUNCH]]`
    (ineligible page).
- Files: index.html (`pis_box`, `debrief_box`, ineligible section), styles.css
  (`.pis-box`).

---

## Known limitations deliberately out of scope for this amendment

Tracked in the test report, pending author decisions: approved-wording
alignment of all instrument prompts and translations (issue 7; the RES-CF2
prompt was aligned here because change 5 touched it), comprehension option
shuffling and key positions (issue 8), self-hosting of maplibre/basemap
(issue 9), server-side data return (issue 10), completion code carrying the
comprehension score (issue 11), ingest dtype warnings (issue 12), duplicate
randomisation lists (issue 13).

## Verification

Re-verified end-to-end with Playwright/Chromium on 2026-08-25 against a local
server: SUZ text-first happy path (two-step record check, case2-v2 export,
ingest round-trip into /tmp template copies including events_log.csv);
correction-before-rating structurally blocked; `neither` and duplicate=yes
end ineligible with no retained data; mid-session reload resumes correctly at
two different steps; LON spatial-first (including reject with required
RES-CF2 verbatim); invalid code rejected; no console errors.

---

# Amendment 2026-08-27 → 2026-08-28 (case2-v3, pre-data pipeline batch)

Dates: code batch executed 2026-08-27 (evening); closeout, documentation and
full verification completed 2026-08-28.
Scope: `case2_interface/app.js`, `build_case2_kit.py`, the four
`case2_kit` data-entry templates (layout only, still zero data), three new
`case2_kit` files, `ingest_case2_exports.py`,
`analysis/confirmatory_analysis.R`, `analysis/case2_analysis.py`,
`protocols/` (one new companion notice, one SOP section), and the external
E2E suite (`case2_verify_e2e.cjs`, polis workspace).
Trigger: 2026-08-27 pipeline review — an audit of the whole
export → ingest → analysis chain against the manuscript's Table 12 and
`app:resident_case_metrics` commitments, run while the templates were still
empty (the only painless window for schema fixes). Review points and the
ten-item fix list are archived at
`.submission/case2_pipeline_review_20260827.md` (polis workspace).

Export schema version: `case2-v2` → `case2-v3`.

**Frozen-materials discipline.** `case2_kit/randomization.csv` (seed
`POLIS-CASE2-RANDOMISATION-v1`, 60 slots) and the three stimulus packages are
byte-untouched. The four data-entry templates were regenerated with
additional *empty* columns while containing zero participant data; this
layout change is exactly what this amendment records. No manuscript `.tex`
file was modified. `protocols/resident_randomisation.csv` is untouched
(see change 10).

## Changes, file by file

1. **`case2_interface/app.js`** — the screener export now carries
   `not_team_member` (0/1, from the pre-existing `c_notteam` checkbox that
   was previously UI-only and never exported, so the team-membership
   exclusion was not auditable in data); export `schema` bumped to
   `case2-v3`. (Review must-fix 1.)
2. **`build_case2_kit.py`** — template writers gain the new columns:
   screener `not_team_member` + the three eligibility columns; responses
   `correction_text` + the three eligibility columns (see 3–4).
3. **`case2_kit/screener_template.csv`** (regenerated, empty) — new columns
   `not_team_member`, `withdrawal_status`, `exclusion_reason`,
   `primary_analysis_eligible`. (Review must-fix 1 + should-fix 6.)
4. **`case2_kit/responses_template.csv`** (regenerated, empty) — new columns
   `correction_text` (verbatim RES-CF2), `withdrawal_status`,
   `exclusion_reason`, `primary_analysis_eligible`. `correction_types` is
   now **reserved for the manual dual-coder codes** and is never written by
   ingest (the v2-era ingest wrongly filled it with the verbatim text).
   (Review must-fix 2 + should-fix 6.)
5. **`case2_kit/correction_coding_codebook.csv`** (new) — frozen
   material-correction codebook from the manuscript appendix
   (`app:resident_case_metrics`): six material classes
   ADD / DEL / REL / BEN / PRI / REJ (material=1) plus NMC non-material
   clarification (material=0), with EN/ZH definitions and examples.
   (Review must-fix 2.)
6. **`case2_kit/correction_coding_sheet.csv`** (new, header-only) —
   dual-coder sheet: `coder1_id/codes`, `coder2_id/codes`,
   `adjudicated_codes`, `adjudicator_id`, `adjudication_note` per
   corrected/rejected record. (Review must-fix 2.)
7. **`case2_kit/allocation_log.csv`** (new) — slot allocation-completion log
   (`slot`, `participant_code`, `allocated_at`, `status`
   allocated/completed/withdrawn/no_show, `completed_at`), 60 empty rows.
   (Review should-fix 5.)
8. **`ingest_case2_exports.py`** — (a) phase-1 validator: every export is
   validated **before anything is written** (all-or-nothing per batch);
   unknown `participant_code` aborts loudly instead of being silently
   dropped; city/mode_order must agree with the frozen slot; value-domain
   checks on screener, responses, comprehension, experience and events;
   `case2-v1`/`v2` remain ingestable with an explicit legacy warning
   (their missing `not_team_member` / `correction_text` stay empty).
   (b) the RES-CF2 verbatim is written to `correction_text`;
   `correction_types` is never touched by ingest. (c) every merge updates
   the matching `allocation_log.csv` slot to `completed` + timestamp; a
   manually recorded `withdrawn` status is warned about and never
   overwritten. (Review must-fixes 1–2, should-fix 5, fix 7.)
9. **`analysis/confirmatory_analysis.R`** — `fit_resident` gained a runnable
   data entry point (`Rscript confirmatory_analysis.R resident <csv> <out>
   [tag]`): column mapping from the frozen template names, sum-to-zero city
   contrasts so `modespatial` is the mode main effect averaged over cities,
   outputs `{tag}case2_clmm_resident.json` (log-odds, Wald 95% CI, p,
   convergence diagnostics: optimizer code, max |gradient|, Hessian
   positive-definiteness and condition number, logLik, AIC) plus
   coefficients CSV and full summary. Previously the protocol formula
   existed but was wired to no data — the manuscript-promised CLMM primary
   could not actually run. (Review must-fix 3.)
10. **`analysis/case2_analysis.py`** — (a) eligibility filter now reads
    `not_team_member`, `withdrawal_status`, `exclusion_reason`,
    `primary_analysis_eligible` on top of the frozen exclusions;
    (b) material corrections are counted from the dual-coder sheet's final
    codes against the codebook's material classes, with the
    interface-counted `material_corrections_n` only as a clearly labelled
    "uncoded (fallback)"; (c) the CLMM (via R, change 9) is the primary
    mode effect; the paired-difference bootstrap + Wilcoxon are demoted to
    descriptive/secondary; (d) new RES-P01..P05 item-level distribution
    output (`{tag}case2_experience_item_distributions.csv`, counts 1–7 ×
    Pooled/SUZ/LON/CHI); (e) analysis outputs renamed **table14 →
    table12** (filenames and JSON keys; one historical code comment
    documents the rename); (f) `--smoke` builds a clearly-labelled
    synthetic kit in /tmp and runs the whole pipeline including the real R
    CLMM, never writing into the kit. (Review must-fixes 2–3, should-fix 6,
    fixes 8–9.)
11. **`protocols/resident_randomisation.SUPERSEDED.md`** (new, 2026-08-28) —
    companion notice declaring `case2_kit/randomization.csv` (identical to
    the interface's `data/randomization.json`) the authoritative list and
    the older, structurally different `resident_randomisation.csv`
    (SUZ-R001…, SPATIAL_THEN_TEXT…) superseded and audit-only. The CSV
    itself is deliberately byte-untouched because its SHA-256 is pinned in
    `freeze_manifest.preview.sha256` and `validate_preregistration.py`
    parses it header-first (a first-line comment would break both).
    (Review should-fix 4.)
12. **`protocols/resident_data_SOP.md`** — new section "Return workflow and
    duplicate reconciliation" (回收流程与去重核对, items 10–11): manual JSON
    return remains the approved channel for this batch (server-side capture
    stays out of scope), receipt logging in `allocation_log.csv`,
    ingest-only merging, and the duplicate-adjudication rules
    (one export per code, first complete session wins, quarantine before
    ingest, RES-S03 cross-check, count reconciliation after every batch).
    Also removed a stray duplicated sentence after item 7 left by an
    earlier edit. (Review note on manual return.)
13. **E2E suite `case2_verify_e2e.cjs`** (polis workspace, outside the
    preregistration tree) — assertions updated for v3 (2026-08-28 00:54):
    export schema `case2-v3`, screener `not_team_member=1`, correction
    verbatim in `correction_text`, 14 named per-event ISO timestamps,
    fidelity-before-confirm event ordering. (Review fix 10.)

## Takeover record (as it actually happened)

This batch was completed across four agent sessions ("takeovers"):

- **2026-08-27 evening (session 1)** — pipeline review, then the code batch:
  app.js (22:36), templates + codebook + sheet + allocation_log (22:38),
  ingest validator (22:43), analysis + R wiring (22:54). Stalled before the
  closeout items.
- **2026-08-27 night – 2026-08-28 morning (sessions 2–3)** — E2E assertions
  updated (00:54); `build_case2_kit.py` last touched 2026-08-28 11:00
  (content consistent, judged the stalled predecessor's final write). No
  closeout documentation produced; both sessions stalled.
- **2026-08-28 (session 4, this closeout)** — anti-collision mtime
  snapshots (no concurrent writes detected at any check), items 1/4/8/9 of
  the closeout list (supersession notice, this changelog entry, SOP
  section, review archive), verification of the template columns and the
  table12 rename, and the full test pass below. Step-by-step log:
  `case2_kit/FIX_PROGRESS.md`.

## Verification (2026-08-28, all on /tmp copies or the isolated mirror)

- **Ingest validator, 18/18**: good v3 export fills all four templates
  (correction_types left empty for coders), updates allocation_log,
  writes/dedups 14 events, re-runs idempotently; six bad classes (unknown
  code; fidelity 9 + city mismatch; unknown schema; corrected without
  verbatim; missing events; off-list category) each abort exit-1 with zero
  writes; a mixed good+bad batch writes nothing (all-or-nothing); v2 legacy
  export ingests with a warning; a manual `withdrawn` slot is never
  overwritten.
- **Full-chain smoke, 16/16** (mirror sandbox): built-in `--smoke` CLMM
  converged (+3.037 log-odds [1.992, 4.083], p=1.2e-08, max|grad|=4.4e-06);
  synthetic 48-export chain (exports → validator → ingest → manual
  withdrawal annotations → analysis) CLMM converged (+3.729 [2.475, 4.983],
  p=5.6e-09, cond(H)=214), exclusions 48 eligible − 3 withdrawn = 45
  analysable (15 per city), `case2_table12.csv` with Pooled/SUZ/LON/CHI
  rows, item distributions 5 items × 4 scopes, corrections status "coded";
  the real kit stayed zero-data throughout.
- **E2E, 53/53 green** (Playwright/Chromium headless against a local
  server): v3 export schema and fields, two-step record check, resume at
  two reload points, reject with required RES-CF2, ineligible routes retain
  no data, no console errors, no failed requests.

---

# Amendment 2026-08-28 (v3.1 — approved wording + zh-CN for the Suzhou arm)

Trigger: author confirmation of 2026-08-28 12:26 — (1) the draft texts
shipped with the interface are the approved wording; (2) the Suzhou arm
requires a Chinese (zh-CN) localisation.
Scope: `case2_interface/index.html`, `case2_interface/app.js`,
`case2_interface/i18n.js` (new), `case2_kit/README.md` (language-version
note), `protocols/resident_instrument_zh.csv` (new, generated review
table), and the external E2E suite (`case2_verify_e2e.cjs`, polis
workspace). Export schema **unchanged: `case2-v3`** — this amendment is
display-layer only.

**Frozen-materials discipline.** `case2_kit/randomization.csv` (60
slots), the three stimulus packages (including `data/*/trace.json` and
`description.txt`), the four zero-data templates,
`protocols/resident_instrument.csv` and every SOP are byte-untouched.
No exported field name, value coding (`confirm|correct|reject`,
`connection_type`, category values, event names, `q1_source…q4_trigger`
0/1) or schema string changed.

## 1. Approved wording replaces the launch placeholders (index.html)

All nine `[[PENDING APPROVED …]]` markers introduced by the 2026-08-25
amendment (change 6) are resolved:

- **PIS, six section stubs** (pure placeholders — wording drawn from the
  frozen protocol sources, per the author's instruction):
  *Purpose* from `POLIS_preregistration.md` §2.5 and
  `resident_online_SOP.md` §7 (feasibility evidence, not a citywide or
  official consultation); *Procedure* from SOP §3 (session sequence,
  30–60 min); *Voluntary + unpaid* from `resident_eligibility.md`
  (voluntary, unpaid, no authority relationship, no commitment to build);
  *Data handling* from `resident_data_SOP.md` items 1–5, 8 and 10
  (minimum fields, no exact address/coordinates, separate linkage file,
  manual file return, no generative-AI upload, anonymised publication
  only); *Withdrawal* from `resident_eligibility.md` (withdrawal section)
  + data SOP item 6, stated accurately against the implemented
  resume/autosave behaviour; *Contacts* per `resident_eligibility.md`
  (approved contact routes travel with the invitation, so the PIS refers
  to the invitation's study-team and independent ethics contacts).
- **PIS headline placeholder** replaced by the information-sheet
  introduction sentence.
- **Ineligibility page**: marker removed; the adjacent draft ("Based on
  your answers … No study data about you has been stored.") promoted to
  approved wording unchanged.
- **Debrief**: marker removed; the adjacent no-commitment draft promoted
  unchanged, and the debrief headline (a pure placeholder) filled from
  SOP §3.9 + preregistration §2.5 (what the session tested; ratings and
  corrections are the outcome; no right or wrong answers).

## 2. zh-CN localisation for the Suzhou arm (display layer only)

- **`i18n.js` (new)** — single string table: every UI string as
  `{id, en, zh}` (id = row key of the review table), plus display-layer
  zh renderings of the frozen SUZ stimulus texts (site description, the
  seven trace-chain records with identifiers/parameters/hashes kept
  verbatim, and the four comprehension questions with their options).
  `langForCode()` maps the participant-code prefix to the language
  (SUZ → zh, LON/CHI → en); `apply()` renders `[data-i18n]` nodes;
  `t()` serves runtime strings (alerts, progress labels, record card,
  locked-rating notice).
- **`index.html`** — `data-i18n` hooks on every visible string; text
  wrapped in spans so checkbox/select/`#resume_code`/`#done_code`
  elements are never re-created by a language switch.
- **`app.js`** — language switches live on the consent page as the
  participant code is typed, is re-asserted at consent and on resume
  (banner in the session language), and the frozen SUZ stimulus texts
  are swapped at display time only (`I18N.stimText`; frozen files
  untouched, English fallback everywhere else). **Data-layer guard:**
  the category `<option>`s previously had no `value` attribute, so the
  exported `need_category` equalled the visible label — translating
  labels would have leaked Chinese into the data. They now carry
  explicit canonical `value` attributes; labels are display-only.
- **`protocols/resident_instrument_zh.csv` (new)** — 155-row review
  table (item_id, en, zh) generated from `i18n.js` (single source; en
  for the stimulus rows taken from the frozen files). zh is a faithful
  translation of the approved English; it goes live for the Suzhou arm
  once the PI confirms the table (note added to `case2_kit/README.md`).
  The 1–7 fidelity anchors are point-matched
  ("1 = not at all · 7 = fully" ↔ "1 = 完全没有捕捉 · 7 = 完全捕捉");
  RES-P01–P05 are literal translations of the approved display wording.
- **Known divergence (unchanged by this amendment):** the frozen
  `protocols/resident_instrument.csv` carries older prompt variants
  (e.g. RES-P01 "I felt able to express what mattered to me in this
  task.") than the author-approved interface wording ("Through this
  process, my voice was heard."). The instrument file is frozen and was
  not edited; reconciling it is an author/ethics-file decision.

## 3. E2E suite extension (`case2_verify_e2e.cjs`, polis workspace)

Placeholder-presence assertions flipped to approved-wording assertions;
T1 is now the SUZ zh-CN flow (Chinese rendering of PIS/screener/anchors/
buttons/trace/experience/debrief, live prefix language switch, exports
asserted canonical — including a no-CJK sweep over all coded fields);
T2 asserts the approved zh ineligibility page and the flip back to
English for a CHI code; T3 asserts the resume banner in the session
language; T4 asserts approved English for LON; new T5 runs a full CHI
text-first flow, so all three cities have full-flow coverage.

## Verification (2026-08-28)

- **E2E 77/77 green** (Playwright/Chromium headless, local :8933; SUZ zh
  full flow, LON spatial-first with reject, CHI text-first, screeners,
  two-reload resume; no console errors, no failed network requests).
- **Ingest round-trip on /tmp mirror**: the four E2E exports (two from
  zh sessions) validate and merge 4/4 into template copies; spot check
  confirms canonical values only (`rest & seating`, `corrected`,
  `resident_within_1km`, `not_team_member=1`) and no CJK characters in
  any coded field. The real kit stayed zero-data (mirror only).
- Anti-collision mtime snapshots: no concurrent writes at start or
  close (log: `case2_kit/FIX_PROGRESS.md`).

**Launch gate closed.** Author confirmed resident_instrument_zh.csv and
authorised distribution for all three cities, 2026-08-28 12:59.
(Distribution guide: `case2_kit/LAUNCH_GUIDE_zh.md`.)
