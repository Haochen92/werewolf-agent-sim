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

## Step 5 — Two self-review passes (in order)

1. **Argument pass** — the guide's full checklist, including the type-specific items. Explicitly check: does any section list facts without interpretation (the fact-dump smell)? Did anything drift from the Step-3 brief's selection?
2. **Prose-legibility pass** — a separate read applying the guide's §Prose legibility rules mechanically: one main idea per sentence; unpack stacked modifiers; ≤ ~1 em-dash per paragraph; define shorthand before use; plain sentence over aphorism.

## Step 6 — Deliver

Present the draft plus a 5-line review note: type chosen, exemplar read, what was excluded and why, checklist items that needed a fix in pass 1, and any claim you could not verify against evidence (flag, don't smooth over).
