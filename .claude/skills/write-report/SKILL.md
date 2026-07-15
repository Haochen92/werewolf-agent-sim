---
name: write-report
description: Write or revise an experiment report or evidence doc following the project style guide
---

Write or revise an evidence document for: $ARGUMENTS

## Step 0 — Pick the document type FIRST

Read `evidence/experiment_report_style_guide.md` §Document Types and decide which of the five shapes fits — experiment report · build-journey log (`experiment_log.md`) · decision/design record · negative/non-feasibility finding · reference/how-it-works doc. The type determines the skeleton, the discipline rules, AND which exemplar you must read. Do not default to the experiment-report skeleton.

## Step 1 — Read the guide's discipline section for that type

The full guide always; then re-read the type's discipline block ("Discipline for reference docs" / "Discipline for journey logs" / the per-type skeletons). These are the rules that erode first under a fill-in-the-blanks pass.

## Step 2 — Read the matching exemplar IN FULL (mandatory, not optional)

Writers imitate the prose they see more reliably than the prose they are told to write (the guide says this itself). Exemplars:
- Reference doc → `evidence/agent_boundaries/report.md`
- Build-journey log → `evidence/sequential_discussion/experiment_log.md`
- Experiment report (single-experiment reference pairing) → `evidence/sequential_discussion/report.md`
- Decision record → `evidence/refactor/eval_architecture_convention.md` (tension → principle → rejected alternatives → decision + named tradeoff), with `evidence/refactor/provenance_lineage_rationale.md` as a second design-rationale example.
- Negative finding → the guide's skeleton (§Document Types) — no single canonical file; imitate the reference-doc exemplar's honesty devices.

## Step 3 — Author the judgment layer BEFORE drafting

If the invoker supplied an outline/argument brief, follow it exactly. If not, produce one and get it confirmed before drafting. The brief must state:
- The one-paragraph argument (what the reader should believe after reading, and on what evidence).
- Selection: which results/artifacts carry each claim — and what is deliberately EXCLUDED (with a one-line why). Altitude drift and fact-dumping are selection failures, not prose failures; they are decided here.
- The reader: busy interviewer/auditor by default.

## Step 4 — Draft, under these accuracy rules

- Verdicts, statuses, and numbers are LIFTED from the cited evidence, never re-derived. State N with every result; separate direction from magnitude at small N.
- Stamp provenance (SHA / runtime_fingerprint / config) per the guide's Artifacts rules.
- Cite code by stable handles: console-entry names (`pyproject [project.scripts]`) or package paths discoverable from a package README; deep `file:line` anchors only when load-bearing (see the guide's Pointer discipline). In evidence folders, frozen scripts carry a FROZEN RECORD stamp — never present one as maintained code.
- Retracted or superseded claims: cite the correction, never the original headline.

### Claim-calibration rules (added 2026-07-06, from the owner's markup of the effectiveness report; extended 2026-07-07, metrics-report round)

- **Scope every verdict to what was tested.** Name the store version, epoch, faction, N, and instrument
  the claim rests on. A null result reads "no detected effect at this power," never "X doesn't help."
  A universal-sounding conclusion from one scoped experiment is a defect even when directionally right.
- **Mechanistic explanations are hypotheses, not findings.** "This fits because town plays an inference
  game" gets a "one plausible reading:" label. If later evidence — even tentative or from an invalidated
  run — points the other way, the verdict sentence must acknowledge it, not just a footnote.
- **Design claims come as controlled/uncontrolled pairs.** State what the design pins AND what it leaves
  live ("pairing pins the board setup; LLM sampling noise remains and is what the paired test averages
  over"). No triumphal labels — "confound-killer," "cancels the noise," "kills X" are banned; describe
  the mechanism and let the reader conclude.
- **Instrument primer before results.** Any ruler a table leans on (win rate, a proxy basket) gets a
  short primer before first use: what it measures, why it was chosen over the obvious alternative, and
  how it was validated. Never make the reader accept a proxy on faith mid-table.
- **Coined terms are claims.** A house term's NAME must not promise a mechanism the code doesn't
  implement — "de-luck" for rate-over-opportunity reads as guess-luck removal, which the metric does not
  do. At first use, define the term by its mechanism and bound it with an explicit "what it does NOT
  remove." If one coined word names several different mechanisms across the doc family (normalization,
  baseline-differencing, luck-vs-skill reassignment), the reader-facing doc names each mechanism
  distinctly and demotes the coined word to a historical house label.
- **Error-inclusion policy.** The report body includes only mistakes that changed the method or set a
  standing rule (e.g. the epoch-baseline rule). Clerical/agent slips and their retractions live in the
  experiment_log; the never-re-cite rule for retracted numbers still binds the report silently.
- **Quarantine the forensics.** Discarded baselines, drift windows, rejected readings, and other
  investigation narrative go in ONE clearly-bounded "Confounds and rejected readings" section (or stay
  in the log with a pointer). The report body must never read chronologically — if a section narrates
  "we did X, then found Y, then re-ran Z," it belongs in the experiment_log.

### Self-containment rules (added 2026-07-06, from the situation-dimensions log markup)

Assume the reader never clicks a link. Links are receipts for verification, not vehicles for
comprehension — every "the full story is in X" that carries understanding (not just provenance) is
functionally a deletion for a busy reader.

- **Show the cure at the disease's concreteness.** When a problem is illustrated with a concrete
  example ("'after a mislynch' matched every mislynch ever stored"), the fix must be shown on the SAME
  example — a before → after pair — not described abstractly ("name the distinctive conditions").
  Test: after the sentence, could the reader sketch the fixed output themselves?
- **One inline example per load-bearing artifact.** Any artifact the doc reasons about repeatedly (a
  composed embed string, a golden case with its labels, an audit row of filled-value-vs-truth) must
  appear inline as actual text at least once — LIFTED from the real record, never invented. If no real
  instance can be found, flag it; an invented example must be explicitly marked illustrative.
- **The curation contract is "self-contained at one example per claim."** "This doc curates, does not
  restate" is a valid contract for an internal hub, not for a reader-facing doc. Pulling one
  representative instance inline per pointed-at source (~15–20 lines total) converts required reading
  into optional receipts.
- **No conversation residue.** Never address "the user," reference chat framing, or cite house rules by
  bare name ("the no-laundering rule") without a one-clause definition. The reader is a stranger with
  no chat history; residue also reveals the doc was written *for* the owner rather than *by* the project.
- **Journey logs: reference-content quarantine.** The log keeps decisions, corrections, and reversals
  (the journey); steady-state mechanics ("how it works today") live in the report — a log section that
  restates the design spec is bloat even when accurate.
- **Acid test before delivering:** a reader with no repo access and no ability to click must be able to
  explain back (a) what the system does, (b) what the core artifact looks like as actual text, and
  (c) which results are trusted vs unknown. A doc that passes only (c) tells the reader exactly how
  much to trust things they cannot picture.

### Explanation-completeness rules (added 2026-07-06, from the exemplar comparison — the owner's
### hand-revised `evidence/sequential_discussion/experiment_log.md` vs the situation-dimensions log)

The exemplar doesn't just narrate the journey; it TEACHES the system while narrating. Imitate these
moves specifically:

- **System model first.** Before the journey starts, place the component in the pipeline in plain words:
  who writes it, who reads it, when, and the central design problem in one paragraph. The WHY of the
  component's existence is the frame every later section silently assumes — state it, don't assume it.
- **The dialectic chain is the unit of explanation.** For every design decision: the problem → the
  obvious/naive fix → why it fails (argued, not asserted) → the chosen fix → the trade-off explicitly
  accepted. Jumping from problem to chosen fix reads as arbitrary even when it isn't.
- **Every mechanism gets its job AND its reason at point of use.** "It exists because X; without it, Y
  happens" (exemplar: "a loop that only answers demands never originates anything... it needs a
  volunteer signal or it's dead on arrival"). A mechanism whose absence-consequence isn't stated is
  a mechanism the reader will not remember.
- **Anticipate the reader's objection and answer it inline.** The exemplar writes headings like "Why a
  tiered score, and not a flat blend or a plain decision tree." If a natural objection has an answer,
  face it; if the reader's question is "so is more similarity good or bad here?", the sentence must
  settle it.
- **Define categories by what membership licenses.** A tier/status/label is explained by what the reader
  may DO with a member ("diagnostic = may explain a verdict, never carry one"), not only by the
  attributes that earned membership ("conditioned on the environment, coupled to a basket proxy"). If
  the reader cannot act on the category after reading its definition, the category is undefined.
  *(added 2026-07-07, metrics-report round)*
- **Cross-experiment references: explain or cut.** A screen/probe/study from another workstream gets
  1–2 sentences of what-it-is and what-question-it-answers BEFORE its findings are used (the exemplar's
  "*Catches:*" convention). If that explanation isn't worth the space, cut the name-drop — an
  unexplained proper noun is worse than no reference.
- **Length calibration: under-explanation is the enemy, not length.** The exemplar is the repo's
  LONGEST log and its fastest read. Never compress by deleting reasoning; compress by deleting
  redundancy. A no-context reader should follow at conversational pace without ever stopping to ask
  "wait, why?"
- **No meta-commentary about the document itself.** Reading contracts, curation notes, and doc-
  discipline remarks are process residue addressed to maintainers; replace with a compact orientation
  blockquote (what this is · companion docs · guiding principle), like the exemplar's header.

## Step 5 — Two self-review passes (in order)

1. **Argument pass** — the guide's full checklist, including the type-specific items. Explicitly check: does any section list facts without interpretation (the fact-dump smell)? Did anything drift from the Step-3 brief's selection? Then scan every verdict sentence for scope: does its strength exceed what the cited store/epoch/N/instrument can carry (the Claim-calibration rules above)?
2. **Prose-legibility pass** — a separate read applying the guide's §Prose legibility rules mechanically: one main idea per sentence; unpack stacked modifiers; ≤ ~1 em-dash per paragraph; define shorthand before use; plain sentence over aphorism.

## Step 6 — Deliver

Present the draft plus a 5-line review note: type chosen, exemplar read, what was excluded and why, checklist items that needed a fix in pass 1, and any claim you could not verify against evidence (flag, don't smooth over).
