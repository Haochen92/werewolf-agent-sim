# AC2 current / before_note with the closing call in today's wording, n=25: generation only

**Question:** on AC2 (game 2f19d908, day-3 vote, player_5 the Investigator), how often does the vote go to
player_8 (the real Healer) when the frozen transcript's closing call no longer lists the accusers? In
`../deduction_ac2_2x2/` the prompt still carried the original game's call, "Before the vote: player_8 has
been accused by player_2, player_5 and player_4. player_8 gets a last word." Live games no longer say who
accused (`Agents/rules/closing.py`). The replay bench now rewrites the old call to today's wording
(`evaluation/src/replay/hallucination_bench.py` `_engine_wording`). This run samples the 2×2's
`current_before_note` arm again with that one line changed. It records the samples and counts the votes
only. It does not judge them.

**Runner:** `evaluation/experiments/deduction_ac2_closing_fixed.py`, a sibling of
`evaluation/experiments/deduction_ac2_2x2.py`. It renders the AC2 turn with the base runner's `_turn`
(`evaluation/experiments/deduction_placement_screen.py`: same case and the same settings), and checks it
against the 2×2's saved prompt. It then calls the 2×2 runner's `run` and `count` unchanged, with that
module's globals set to this folder, one arm (block "current", placement "before_note"), n=25 and a cap of
30 calls. As in the 2×2, every call sent the saved system and human texts, read back from `prompts/`.

```
poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --render-only
LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
  GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --run
poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --count
```

**Code:** HEAD `c0272210` plus an **uncommitted working tree**. Before and after the run, the sha256 of
`git diff HEAD -- Agents/ evaluation/src/replay/` was
`d02a5b6ed837ba392528e5480ee66e16cc1f5470aaf9316e46e3eb25f930c329`. It does not cover untracked files.
The runners are untracked: this one is `2f80861a413ebcd0…`; the 2×2 runner (`d497abacb409c990…`), the base
runner (`3acb7ccef7ead5b6…`) and the ablation wrapper (`6602c7d43a2bd0ce…`) are the same files as for the
2×2 run. The run took place on 2026-10-18. The prompt was rendered and checked (`--render-only`) shortly before 02:41:07 UTC and again at
the start of `--run`. The calls ran from 02:41:21 to 02:42:47 UTC, reruns included.

## The prompt: diff against the 2×2

Before any model call, the runner checked the following. `prompt_check.json` records each check.

- The rendered human message holds "Before the vote: player_8 gets a last word." once, and does not hold
  "has been accused by".
- The system message is byte-identical to `../deduction_ac2_2x2/prompts/system.txt` (12,306 characters,
  sha256 `016c791eaeff2a0c…`).
- The human message differs from `../deduction_ac2_2x2/prompts/AC2_current_before_note.txt` only in the
  closing line. It equals that file with the old line swapped for the new one.

```
--- deduction_ac2_2x2/prompts/AC2_current_before_note.txt
+++ rendered
@@ -43 +43 @@
-game_master: Before the vote: player_8 has been accused by player_2, player_5 and player_4. player_8 gets a last word.
+game_master: Before the vote: player_8 gets a last word.
```

The human message is 11,053 characters (the 2×2's was 11,115), sha256 `2526326ead304f43…`. The schema,
the action key and the legal vote targets come from the same `_turn` render as the 2×2's.

## Settings

These are the 2×2's settings, for its `current_before_note` arm.

| | |
|---|---|
| Model | `anthropic/claude-haiku-5-5`, `structured_mode` json_schema |
| Thinking | low (`GOOGLE_GENAI_THINKING_LEVEL=low`) |
| Temperature | 1.0, the `get_llm()` default |
| Memory | off (`turn_payload(memory="none")`) |
| `deduction_mode` | "full" |
| `deduction_placement` | "before_note" |
| Case | AC2: 2f19d908, day 3 vote, player_5 the Investigator. `haiku_effort_replay/vote_cases.jsonl` `9b827b695a61ece9` |
| n | 25 samples |
| Schedule | the 25 samples shuffled by `random.Random(20261018)`. The order is in `schedule.json`. |
| Concurrency | 3 worker threads, which take the jobs in schedule order |
| Requests | `GAME_LLM_ATTEMPTS=1`, timeout 180 s, cap 30 including reruns and SDK retries; Langfuse tracing off |

## Results: vote counts

These are counted by code (`--count`) from `vote_target`, on the latest valid row per sample. All 25
samples ended valid.

| player_8 | player_6 | Valid |
|---|---|---|
| 5 | 20 | 25 |

(The `--count` output's `first_half` / `second_half` fields come from the 2×2's 100-job schedule. Here
all 25 slots fall in its "first half".)

**Model calls:** 28, with 25 in the main pass and 3 reruns. The SDK made no retries.

**Invalid samples:** 3 in the main pass, each a malformed read (`reads.N.player` missing): samples 12
(position 2), 11 (position 11) and 22 (position 12). All three were valid in the first rerun round, and
those rerun rows are the ones counted.

**Total cost:** $0.0368. That covers 250,264 input tokens, of which 153,250 were cached and 18,390 were
cache writes, and 50,176 output tokens, of which 34,712 were reasoning. The cost includes the cache-write
premium.

## Files

- `prompts/system.txt`: the system message, byte-identical to the 2×2's.
- `prompts/AC2_current_before_note.txt`: the human message as sent.
- `prompt_check.json`: the checks above, the diff, and each prompt's sha256.
- `schedule.json`: the seed and the 25 shuffled (arm, sample) jobs. The index is `schedule_position`.
- `samples.jsonl`: one row per call, 28 rows, with the 2×2's fields (`case`, `case_id`, `arm`, `block`,
  `placement`, `sample`, `schedule_position`, `call_order`, `rerun`, `started_utc`, `finished_utc`,
  `valid`, `error`, `vote_target`, `updated_strategy`, `reads`, `usage`). The invalid rows are kept, and the
  reruns are marked `"rerun": true`. **For counting, use the latest valid row per sample.**
