# Cross-project synthesis

Lessons that recur across subsystems: the same engineering judgment made in several places, each
time for its own reason. One file per lesson. Each file collects the instances with their evidence,
says what the instances have in common and where they differ, and drafts the paragraph the write-up's
engineering-lessons section will use.

The rule for the write-up (2026-10-13): each decision is explained in its own segment, where its
concrete problem and result live; the synthesis is one short paragraph that links back to those
segments. It never replaces them, and it never flattens different interventions into one slogan.

## Lessons

| Lesson | Instances | Status |
|---|---|---|
| [Separating generation from checking](separating_generation_from_checking.md) | extraction de-halo · tell detection · discussion echo gate | Written 2026-10-13 |
| [Deterministic where reliable](deterministic_where_reliable.md) | scheduler · night record and dead roster · claim ledger · night-1 lot · situation dimensions · echo gate · credit · eliminated-player check | Written 2026-10-14 |

## Candidates to extract

Pointers only, not yet checked against their sources. Verify each instance before writing it up.

- **Where a rule could be code, it became code.** Deterministic where reliable, the model only where
  a rule was not: the discussion scheduler's firing rules, the vote-endpoint credit, the night record
  and the dead roster (built from records, not parsed from the game master's prose), the addressing
  discharge, the deterministic situation dimensions overriding the model's, the eliminated-player
  check. Sources: `gameplay/discussion/experiment_log.md` (the guiding principle), `credit/`,
  `extraction/situation_dimensions/`, `agent_boundaries/experiment_log.md` §6; the closing bullet of
  `separating_generation_from_checking.md`. Written 2026-10-14 (above).
- **Grade the decision, not the result.** The de-lucked metrics, the credit grading rule (luck-dependent
  results graded on the choice), the extraction verdict halo. Sources: `metrics/`,
  `memory_system/v8/decisions.md` §12–13, `extraction/observation_quality/outcome_halo_case_study.md`.
- **Check that the experiment that ran is the one you meant.** The v7 config slip (memory on for every
  faction) and the arm guard added after it; the paired-board join that merged five arms' games by
  game id. Sources: `memory_system/v7/report.md`, `extraction/tell_extraction/experiment_log.md`.
  Also a decision that never reached the running system: the retrieval cap of 5 made as fetch width
  with a keep of 3 after it (`retrieval/capacity_limits/report.md` addendum), the leak checkers fed
  nothing on live games (`agent_boundaries/experiment_log.md`), the Gemini thresholds left on the old
  embedder's scale for three months (`dedup/embedding_prefilter/experiment_log.md` addendum).
- **Reshape the task before buying a bigger model.** Tell mining split so Flash-Lite could do what had
  needed 2.5 Pro; Flash-Lite's all-required schemas. Source: `extraction/tell_extraction/experiment_log.md` (version at `2382b34c`) §6–7.
- **Cost quotes against the bill.** The tell run billed 6× its quote (thinking billed as output); later
  quotes corrected the same way. Source: `extraction/tell_extraction/experiment_log.md` (2026-07-13).
- **Models favour the first, lowest or example-named option.** Seat-choice bias in prompts; the fix was
  an engine-drawn lot. Source: the prompt work around the night-1 lot.
- **Every claim carries its epoch.** A retracted static-memory result, a cross-epoch confound, and the
  finding that every memory game ran without reasoning tokens. Sources: `memory_system/v7/report.md`,
  `memory_system/`.
- **A value that cannot be computed reads as missing, never as zero.** *Owner's own note for handling
  missing data (2026-10-22); not a lesson for the write-up.* Three instances: v7's "+0.41 town lift",
  a raw rate with the no-memory baseline pinned to 0, retracted as halo (`memory_system/v7/report.md`); July
  credit's missing memory-off comparison taken as 0, so the abstain lesson sat at 0.00 (the smaller of
  the two gaps: −0.16 against the real baseline; `credit/report.md` §6); and the 21 metrics that read 0
  on every ten-seat game, set to None before they were ported (`memory_system/v8/decisions.md` §2). The
  ten-seat code now leaves such values unscored (`credit/report.md` §3).

## Adding a lesson

A lesson file has: the lesson in one paragraph; a table of the instances and which kind of
intervention each was; one section per instance (the problem, the check, the evidence, what it did
not fix, whether it is live, sources with line numbers); what the instances show together, including
where they differ; and where it goes in the write-up, with a draft paragraph.
