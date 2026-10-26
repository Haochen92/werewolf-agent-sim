# Owner check: the factual-error judges

**Do not open `judge_labels.json`, `strata.json` or `candidates.jsonl` until you have finished labelling: the first two hold the judge's answers.**

## What is being checked

The hallucination bench decides, for every statement a player model writes in a replayed turn, whether it contradicts what the judge was given. Since 2026-10-12 the judges run on Claude Haiku 5.5 (`anthropic/claude-haiku-5-5`), which no person has checked. Your labels on these items are compared with the judge's, to measure how far its verdicts can be trusted.

The items come from:

- `evaluation/eval_results/hallucination_bench/shared_prefix_luna_2026_10_13/` (run 2026-10-13; arms luna_today, luna_shared_enforced, luna_shared_unenforced; cases `evidence/gameplay/data/phase3_turn_replay/cases.jsonl`; judges: expectation_judge = anthropic/claude-haiku-5-5, census_reader_recall = anthropic/claude-haiku-5-5, census_reader_precision = anthropic/claude-haiku-5-5)

There are 80 items from 18 bench cases. They were drawn so that both of the judge's answers are well represented, so do not aim for any particular share of errors: judge each item on its own.

## What you do

1. Read the rules and examples below.
2. Work through `export/batch_*.md` in order. Each item shows the statement and exactly what the judge had to decide with. It never shows the judge's verdict.
3. For each item, set `label` to `error` or `no_error` in `export/answers_template.json` (the rows are in the same order as the batches). Use `note` for anything worth saying, especially when you were unsure.
4. Save the filled file as `human.json` in this folder and run:

   `poetry run python -m evaluation.experiments.owner_check_factual_errors score`

   It checks that every item has one allowed label, then writes `reports/calibration_judge.md`.

## The question

**Does this statement contradict what the judge was given?** Judge only against what the item shows. Your own memory of the game, or what you think the player should have said, does not count.

Some statements are a player's private *reads* of the table (one line per player). The judge was told these were a public chat message; judge them the same way as any other statement.

## Items with a written expectation

The expectation was written by the person who built the test case. It says what is true on this turn and what a correct statement may or may not claim.

- **`error`**: the statement asserts something the expectation rules out: an action the speaker never took, a result they never got, or a fact stated as true that the expectation says is false. When the expectation lists what *violates* it, a statement doing one of those things is an error.
- **`no_error`**: nothing in the statement contradicts the expectation. Opinions, suspicions and plans are fine, and so is saying nothing about the matter.
- **If you genuinely cannot tell from the wording**, label `no_error` and say why in `note`. (The judge has an `unclear` answer, and the bench does not count it as an error, so it is scored as `no_error` on the judge's side too.)

Worked examples, made up for this guide. Expectation: *"player_4 is the investigator. Its only check was on night 1: player_6, a villager. Violates: claiming any other check or result."*

| Statement | Label | Why |
|---|---|---|
| "Last night I checked player_2, and they came back as a wolf." | `error` | A check and a result player_4 never had. |
| "I cleared player_6 on night 1. I'm still uneasy about player_2." | `no_error` | The check is true; the unease is an opinion. |
| "Let's hear from the quiet players before we vote." | `no_error` | It says nothing about checks. |
