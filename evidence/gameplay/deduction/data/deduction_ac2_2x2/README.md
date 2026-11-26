# AC2 2×2, interleaved, n=25 per arm: generation only

**Question:** on AC2 (game 2f19d908, day-3 vote, player_5 the Investigator), how often does the vote go to
player_8 (the real Healer) under each of four prompts: the seat block as it stands or trimmed of player_8's
two added sentences, crossed with `deduction_placement` "before_note" or "after_note"? In
`../deduction_placement_n10/` the before_note prompt voted player_8 in 8 of 10 samples, and the same
byte-identical prompt got 1 of 10 in `../deduction_ac2_ablation/` (V0). This run therefore samples all four
arms in one shuffled schedule, so that any drift over time hits every arm alike. It records the samples and
counts the votes only. It does not judge them.

**Runner:** `evaluation/experiments/deduction_ac2_2x2.py`, a sibling of
`evaluation/experiments/deduction_ac2_ablation.py`. It reuses the base runner
`evaluation/experiments/deduction_placement_screen.py` (the AC2 case, `_turn`, the legal-target schema,
cost accounting and SDK-retry counter) and the ablation's removed strings (`E1`, `WILL`) and `_ablate`,
all unchanged. The four prompts were rendered once at the start, checked, and saved to `prompts/`. Every
call then sent the saved system and human texts, read back from those files, rather than re-rendering.

```
poetry run python evaluation/experiments/deduction_ac2_2x2.py --render-only
LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
  GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_2x2.py --run
poetry run python evaluation/experiments/deduction_ac2_2x2.py --count
```

`--run` makes the main pass and then reruns the invalid samples in the same process, inside the cap.

**Code:** HEAD `30a7048f` plus an **uncommitted working tree**. Before and after the run, the sha256 of
`git diff HEAD -- Agents/ evaluation/src/replay/` was
`c91060db1ebe797661ab9e9c7cda1af7d7b93d0b4898c6b7b761e86ea5b3ebde`, the ablation's post-run value. It does
not cover untracked files. The three runners are untracked: this one is `d497abacb409c990…`, the base runner
is `3acb7ccef7ead5b6…` and the ablation wrapper is `6602c7d43a2bd0ce…`, the same as for the ablation run.
The run took place on 2026-10-18. The prompts were rendered at 02:23:46 UTC, and the render was repeated
at the start of `--run` and gave the same sha256s. The main pass ran from 02:24:05 to 02:29:02 UTC, and the
rerun pass ended at 02:29:30.

**The prompts.** The live render of both placements was byte-identical to
`../deduction_placement_n10/prompts/AC2_<placement>.txt`, and `current_before_note` is byte-identical to
the ablation's `AC2_V0.txt`. The system message is the same in both placements: 12,306 characters, sha256
`016c791eaeff2a0c…`. It is saved as `prompts/system.txt`. The schema, the action key and the legal vote
targets are also the same in both placements. The targets are player_2, player_4, player_6, player_8,
player_10 and abstain.

## Settings

These are the ablation's settings, with placement added as a factor.

| | |
|---|---|
| Model | `anthropic/claude-haiku-5-5`, `structured_mode` json_schema |
| Thinking | low (`GOOGLE_GENAI_THINKING_LEVEL=low`) |
| Temperature | 1.0, the `get_llm()` default |
| Memory | off (`turn_payload(memory="none")`) |
| `deduction_mode` | "full" |
| `deduction_placement` | "before_note" or "after_note" (a factor) |
| Case | AC2: 2f19d908, day 3 vote, player_5 the Investigator. `haiku_effort_replay/vote_cases.jsonl` `9b827b695a61ece9` |
| n | 25 samples per arm, four arms, 100 samples |
| Schedule | the 100 (arm, sample) jobs shuffled by `random.Random(20261018)`. The order is in `schedule.json`. |
| Concurrency | 3 worker threads, which take the jobs in schedule order |
| Requests | `GAME_LLM_ATTEMPTS=1`, timeout 180 s, cap 115 including reruns and SDK retries; Langfuse tracing off |

## Arms: the removed strings, verbatim

| Arm | Block | Placement | Human message characters |
|---|---|---|---|
| `current_before_note` | current | before_note | 11,115 |
| `current_after_note` | current | after_note | 11,115 |
| `trimmed_before_note` | trimmed | before_note | 10,792 |
| `trimmed_after_note` | trimmed | after_note | 10,792 |

The **trimmed** block removes these two strings from the rendered human message. They are the ablation's
V1 and V2 strings, which is the ablation's V3 without the claims line.

- `" player_2 says player_8 came to you on night 2, and player_8 says it protected you that night. These agree; the sighting does not show which action player_8 took."`
  (162 characters, with the leading space)
- `" player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on player_1, so that visit was her block on player_8."`
  (161 characters, with the leading space)

The player_8 line then reads "- player_8 can be the Serial Killer only if player_2's watch is false." alone.
The line "- No one else claims the Investigator, the Sentinel, the Sigilist or the Healer. player_6 and player_10
have made no role claim." stays.

Before any model call, the runner checked the following, and `prompt_check.json` records each check:

- In both placements, each string occurred exactly once in the human message and once inside the seat
  block. After removal, neither string occurred.
- Each trimmed arm is shorter by exactly 323 characters, the sum of the two removals.
- Within each block, before_note and after_note have the same seat block, which occurs once. With the
  block taken out, the rest of the two prompts is the same word sequence, and the two prompts have the
  same multiset of characters.
- The block sits before "Adaptive Strategic thinking:" in before_note and after it in after_note.

A `diff` between `current_before_note` and `trimmed_before_note` changes only the player_8 line.

## Results: vote counts

These are counted by code (`--count`) from `vote_target`, on the latest valid row per (arm, sample). All
100 samples ended valid.

| Arm | player_8 | player_6 | player_10 | player_4 | Valid |
|---|---|---|---|---|---|
| current_before_note | 9 | 14 | 2 | 0 | 25 |
| current_after_note | 9 | 13 | 1 | 2 | 25 |
| trimmed_before_note | 10 | 13 | 2 | 0 | 25 |
| trimmed_after_note | 5 | 15 | 4 | 1 | 25 |

**By half of the schedule.** The halves are schedule positions 0–49 and 50–99. A rerun is counted in its
original slot. All five counted reruns have slots in the second half, and they ran after position 99.

| Arm | Slots in first half | First half: votes | Second half: votes |
|---|---|---|---|
| current_before_note | 9 | player_8 3, player_6 6 | player_8 6, player_6 8, player_10 2 |
| current_after_note | 12 | player_8 3, player_6 8, player_4 1 | player_8 6, player_6 5, player_4 1, player_10 1 |
| trimmed_before_note | 15 | player_8 5, player_6 8, player_10 2 | player_8 5, player_6 5 |
| trimmed_after_note | 14 | player_8 3, player_6 8, player_10 2, player_4 1 | player_8 2, player_6 7, player_10 2 |

Pooled over the four arms, player_8 got 14 of 50 votes in the first half and 19 of 50 in the second.

**Model calls:** 107, with 100 in the main pass and 7 reruns. The SDK made no retries.

**Invalid samples:** 5 in the main pass:

- 4 were a malformed read (`reads.N.player` missing): trimmed_after_note 8 (position 56) and 15 (69),
  current_before_note 23 (86), and trimmed_before_note 8 (96).
- 1 was invalid JSON: trimmed_before_note 14 (95).

In the first rerun round, three came back valid: current_before_note 23, and trimmed_before_note 8 and 14.
trimmed_after_note 8 and 15 failed again with a malformed read. Both were valid in the second rerun round.

**Calls and cost per arm**, with reruns included:

| Arm | Calls | Cost |
|---|---|---|
| current_before_note | 26 | $0.0334 |
| current_after_note | 25 | $0.0327 |
| trimmed_before_note | 27 | $0.0331 |
| trimmed_after_note | 29 | $0.0354 |

**Total cost:** $0.1346. The main pass cost $0.1258 and the reruns $0.0088. That covers 952,840 input
tokens, of which 639,808 were cached and 18,456 were cache writes, and 192,901 output tokens, of which
135,326 were reasoning. The cost includes the cache-write premium.

## Files

- `prompts/system.txt`: the system message, the same for all four arms.
- `prompts/AC2_<arm>.txt`: the four human messages as sent.
- `prompt_check.json`: the removal and placement checks, with each prompt's sha256.
- `schedule.json`: the seed and the 100 shuffled (arm, sample) jobs. The index is `schedule_position`.
- `samples.jsonl`: one row per call, 107 rows, with these fields:
  - `case`, `case_id`, `arm`, `block`, `placement`, `sample`;
  - `schedule_position`; `call_order`, the order in which calls were dispatched, which includes reruns;
  - `rerun`, `started_utc`, `finished_utc`, `valid`, `error`;
  - `vote_target`, `updated_strategy`, `reads`;
  - `usage`: `input`, `cached`, `cache_written`, `output`, `reasoning`, `seconds`, `cost_usd`.

  The invalid rows are kept. The reruns come at the end, marked `"rerun": true`. **For counting, use the
  latest valid row per (arm, sample).**
