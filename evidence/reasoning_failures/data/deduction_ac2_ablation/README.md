# AC2 seat-block ablation, n=10 per variant: generation only

**Question:** which sentences in player_8's entry of the AC2 seat block go with the day-3 vote on player_8
(the real Healer, the original failure)? In `../deduction_placement_n10/`, AC2 with `deduction_placement`
"before_note" voted player_8 in 8 of 10 samples. An earlier run of a shorter block got 0 of 6. This folder
removes sentences from that prompt and samples each variant. It records the samples and counts the votes
only. It does not judge them.

**Runner:** `evaluation/experiments/deduction_ac2_ablation.py`, a wrapper around
`evaluation/experiments/deduction_placement_screen.py`. It reuses that runner's AC2 case, `_turn`, chain
(legal-target schema, structured output), cost accounting and SDK-retry counter, all unchanged. The arm is
"before_note". The wrapper renders the human message, removes the variant's strings from the rendered
text, and sends the system message unchanged.

```
poetry run python evaluation/experiments/deduction_ac2_ablation.py --render-only
LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
  GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_ablation.py --n 10
# then the same command with --rerun-invalid (the cap of 45 requests counts the first pass)
```

**Code:** HEAD `30a7048f` plus an **uncommitted working tree**. Before the run, the sha256 of
`git diff HEAD -- Agents/ evaluation/src/replay/` was
`b8fbc4fc67fb1f8baba2182ec13edb5699983deb5486658d43140b1f394627c1`, the same as for the n10 run. It does
not cover untracked files. The base runner is untracked, and its sha256 is `3acb7ccef7ead5b6…`, the same as
for the n10 run. The wrapper is untracked, and its sha256 is `6602c7d43a2bd0ce…`. The run took place on
2026-10-18. The main pass ran from 02:10:37 to 02:16:41 UTC, and the rerun pass ended at 02:18:11.

**A concurrent edit to the tree.** Another session edited files in `Agents/` from 02:15:22 UTC on:
`schemas/game_events.py`, `rules/night_record.py`, `deduction/records.py`, `schemas/deduction.py`,
`deduction/self_knowledge.py`, and `deduction/comparisons/` (`record.py`, `wording.py`, `status.py`,
`own_visits.py`, `__init__.py`). After the run, the diff sha256 was
`c91060db1ebe797661ab9e9c7cda1af7d7b93d0b4898c6b7b761e86ea5b3ebde`.
- The main pass's process imported its code before the first edit, so its 40 rows ran on the `b8fbc4fc…`
  tree.
- The rerun pass started after some of those edits, so its 5 rows (`"rerun": true`) ran on a tree that was
  partly edited. Before any rerun call, the rerun pass re-rendered AC2 and checked that the human message
  was byte-identical to the n10 file. The system message was not compared.

## Settings

These are the n10 run's settings, restricted to one case and one arm.

| | |
|---|---|
| Model | `anthropic/claude-haiku-5-5`, `structured_mode` json_schema |
| Thinking | low (`GOOGLE_GENAI_THINKING_LEVEL=low`) |
| Temperature | 1.0, the `get_llm()` default |
| Memory | off (`turn_payload(memory="none")`) |
| `deduction_mode` | "full" |
| `deduction_placement` | "before_note" |
| Case | AC2: 2f19d908, day 3 vote, player_5 the Investigator. `haiku_effort_replay/vote_cases.jsonl` `9b827b695a61ece9` |
| n | 10 samples per variant, four variants |
| Requests | `GAME_LLM_ATTEMPTS=1`, timeout 180 s, cap 45; Langfuse tracing off |

## Variants: the removed strings, verbatim

Each string is removed from the rendered human message. Before any model call, the runner checked that
each string occurred exactly once and that the variant's length fell by exactly the sum of the removed
lengths. Both checks are recorded in `prompt_check.json`. A `diff` against V0 shows that only the lines
listed below change. The strings are copied from `../deduction_placement_n10/prompts/AC2_before_note.txt`.
The live render was byte-identical to that file, and V0 is that file.

- **V0, current:** nothing is removed.
- **V1, no E1:** removes
  `" player_2 says player_8 came to you on night 2, and player_8 says it protected you that night. These agree; the sighting does not show which action player_8 took."`
  (162 characters, with the leading space).
- **V2, no will visit:** removes
  `" player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on player_1, so that visit was her block on player_8."`
  (161 characters, with the leading space).
- **V3, no both:** removes both strings above and the whole line
  `"- No one else claims the Investigator, the Sentinel, the Sigilist or the Healer. player_6 and player_10 have made no role claim.\n"`
  (129 characters, with its newline). That is 452 characters in all.

After V1 and V2, the player_8 line keeps "- player_8 can be the Serial Killer only if player_2's watch is false." and
the remaining sentence. After V3, it is that first sentence alone.

| Variant | Human message characters |
|---|---|
| V0 | 11,115 |
| V1 | 10,953 |
| V2 | 10,954 |
| V3 | 10,663 |

## Results: vote counts

These are counted by code from `vote_target`, on the latest valid row per (variant, sample).

| Variant | player_8 | player_6 | player_10 | Valid samples |
|---|---|---|---|---|
| V0 | 1 | 8 | 1 | 10 |
| V1 | 5 | 5 | 0 | 10 |
| V2 | 5 | 5 | 0 | 10 |
| V3 | 1 | 7 | 0 | 8 (samples 3 and 7 still invalid) |

**Model calls:** 45, the cap. There were 40 first-pass calls and 5 reruns, and the SDK made no retries.

**Invalid samples:** 7 in the first pass, all of them a malformed read (`reads.N.player` missing). They
were V0 samples 1, 4, 7 and 8, and V3 samples 2, 3 and 7. The rerun pass reached V0 1, 4, 7 and 8 and V3
2, and all five came back valid. The cap was then reached, so V3 samples 3 and 7 were not rerun.

**Calls and cost per variant**, with reruns included:

| Variant | Calls | Cost |
|---|---|---|
| V0 | 14 | $0.0198 |
| V1 | 10 | $0.0122 |
| V2 | 10 | $0.0123 |
| V3 | 11 | $0.0137 |

**Total cost:** $0.0580. The first pass cost $0.0510 and the reruns $0.0070. That covers 400,467 input
tokens, of which 270,688 were cached and 6,152 were cache writes, and 84,415 output tokens, of which 60,045
were reasoning. The cost includes the cache-write premium.

## Files

- `prompts/AC2_<variant>.txt`: the rendered human messages as sent.
- `prompt_check.json`: the removal checks.
- `samples.jsonl`: one row per call, 45 rows, with these fields:
  - `case`, `case_id`, `variant`, `arm`, `sample`, `valid`, `error`, `rerun`;
  - `vote_target`, `updated_strategy`, `reads`;
  - `usage`: `input`, `cached`, `cache_written`, `output`, `reasoning`, `seconds`, `cost_usd`.

  The invalid rows are kept. The replacements come at the end of the file, marked `"rerun": true`. **For
  counting, use the latest valid row per (variant, sample).**
