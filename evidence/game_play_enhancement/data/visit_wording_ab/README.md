# Visit-wording replay A/B (2026-10-21): generation

Question: does the physical "visit" metaphor ("came to", "went to", "at my door", "follow") cause the
definition arguments seen on day 2 of game 2b29bfe8 (DeepSeek V4.1 Flash), where ~15 lines went on
whether a Trailseer's "player_3 came to visit me" was watch or follow language?

**Generation only.** Judging is done afterwards on `blind.jsonl` by chat subagents (no bench judge,
no Claude API calls here).

## Arms

| arm | checkout | wording |
|---|---|---|
| A | worktree `../ww-visit-a` on tag `visit-wording-baseline` (= 1371b5e5) | current: visit / follow / came to / went to / at the door |
| B | worktree `../ww-visit-b`, detached at the same tag + uncommitted edits (`arm_b.diff`) | same rules, mechanical: "X targeted Y", "who targeted X", "targeted no one"; the Trailseer *tracks*; the Sentinel *watches*; door/approach metaphors deleted |

Arm B changes only words a model reads: the rules block (`game_rules.py`), the role cards, the night
record and will templates (`night_record.py`, with the will parser in `public_prose.py` taught the new
wording too), the claim ledger, the deduction engine's wording modules, the night-record verbs in
`prompt_formatters.py`, and the field descriptions of the discussion output's `claimed_night_actions`
(`lineup_output.py`). Engine identifiers (action `follow`, `visit`, result `no_visitors`, field names)
are unchanged. A shim in `prompt_formatters.py` (`retarget`) rewrites the stored outcome prose of the
replayed games ("Tonight player_3 visited player_4.") and the game master's read-out wills into the
new wording as they are rendered. Not rewritten: anything a player or the summariser wrote (the
transcript, earlier days' summaries, the seat's own strategy notes), so arm B's prompts still carry
the original game's "visit"/"follow" words wherever players used them. The summariser's own schema
(`schemas/output.py`) is unchanged; it does not run in this replay. In B, the rules goldens were
regenerated and `tests/engine/test_game_rules_render.py` + `tests/engine/test_night_whiff_disclosure.py`
pass.

## Run

- First run: model `deepseek/deepseek-flash` (DeepSeek V4.1 Flash), as in the source games (samples in `deepseek/`; the owner then ruled experiments run on Haiku, and asked for the finished DeepSeek run to be judged too); the catalogue row has
  no turn thinking or structured mode, so the game ran at the default `minimal` thinking and the
  provider's default structured mode. Both arms: `GOOGLE_GENAI_MODEL=deepseek/deepseek-flash
  GOOGLE_GENAI_THINKING_LEVEL=minimal`, `LLM_STRUCTURED_MODE` unset, memory none, n=5, workers 3.
- Command per arm, from its worktree, with the main repo's `.venv` python:
  `python -m evaluation.src.cli_runner.regen_replay.both.hallucination_bench --worker --dataset
  <abs>/cases.jsonl --out <abs>/samples_{A,B}.jsonl --n 5 --memory none --workers 3`
- Second run (the main one): `anthropic/claude-haiku-5-5`, `GOOGLE_GENAI_THINKING_LEVEL=low`, `LLM_STRUCTURED_MODE=json_schema`, n=5, same cases; `samples_{A,B}.jsonl` here. Haiku cost ≈ $0.21 (2.39M input, 1.79M of it cached; 260k output).

## Cases (`cases.jsonl`, 19)

Built by `evaluation/experiments/visit_wording_cases.py` (states read read-only from the games'
LangGraph checkpoints on the server's Postgres; seqs in the runner are the `events` table's).

- `report` (8): a seat's turn reporting its own watch/follow result: 2b29bfe8 seq 125 (player_4,
  Trailseer, opening) and 223 (player_3, Sentinel, its first watch report, mid-discussion);
  25003626 (Claude Haiku 5.5) seq 550, 556, 691, 802; 64e0f58b (DeepSeek V4.1 Flash) seq 127, 320.
- `react` (11): turns answering a sighting claim: 2b29bfe8 day 2 seq 144, 172, 181, 199, 239, 248,
  266; 25003626 seq 566, 572, 605, 708.
- Skipped: none (every turn had its checkpoint). Game 140610ad was searched and has no Sentinel or
  Trailseer in its lineup, so no report turns.

## Files

- `cases.jsonl`: the frozen turns (bench case format, no golden).
- `samples_A.jsonl`, `samples_B.jsonl`: the worker's samples (units, claim, usage).
- `blind.jsonl`: every valid sample's public line (or "(passed)"), shuffled, with an opaque id, case,
  slice and seat, no arm; `key.jsonl`: opaque id → arm, case, sample. Made by
  `poetry run python evaluation/experiments/visit_wording_cases.py blind`.
- `case_context.md`: per case, the true roles, every night record (who targeted whom, in arm A's
  wording), the claims on record, the last lines before the turn and the original line.
- `arm_b.diff`: arm B's edits against the tag.

## Judging (2026-10-21)

Blind, by eight chat subagents (four per model, ~47 lines each), against `judge_rubric.md` with
`case_context.md`: per line `mech` (states or relies on false visit/watch/follow mechanics), `chew` (main
point is rules or wording), `clear` (report slice: own result stated correctly and unambiguously).
Verdicts: `judged_*.jsonl` (Haiku), `deepseek/judged_*.jsonl`. Unblinded by the runner's `score`
command (joins `key.jsonl`); the sign test counts cases whose rate differs between the arms.

| model | arm | mech | chew | clear (report) | sign test vs A |
|---|---|---|---|---|---|
| DeepSeek V4.1 Flash | A visit | 23/91 (25%) | 7/91 (8%) | 23/39 (59%) | |
| DeepSeek V4.1 Flash | B target | 22/95 (23%) | 9/95 (9%) | 25/40 (62%) | mech 5–5, chew 0–2, clear 4–4 (all p ≥ 0.5) |
| Haiku 5.5 | A visit | 19/95 (20%) | 1/95 (1%) | 22/40 (55%) | |
| Haiku 5.5 | B target | 28/95 (29%) | 2/95 (2%) | 14/40 (35%) | mech 3 better–6 worse (p=0.51), clear 1–4 (p=0.38) |

**Result: the wording is not the cause.** Swapping "visit/follow" for "target/track" changed nothing on
DeepSeek and was, if anything, worse on Haiku (not significant at this n). The mechanics errors cluster
on one interaction in both models and both arms: in 2b29bfe8 the Sentinel (player_3) watched player_4
while the Trailseer (player_4) followed player_3, so the follow showed player_3 going to player_4 while
the watch on player_4 listed no one. Players (the Sentinel itself included) read the two results as
contradictory, or the Sentinel denied visiting at all, because watching is a visit and the watcher is
never listed in its own result. Cases b77857, cb1f34, 5b2f63, 83e5f3, 9c6a0a and 4e5ab6 hold most of
the `mech` lines. A smaller second group asks players who visited them, as if a visited player is told.
