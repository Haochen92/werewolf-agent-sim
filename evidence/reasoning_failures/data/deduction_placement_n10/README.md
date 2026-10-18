# Deduction block placement screen (OQ21), n=10: generation only

**Question:** does the seat's deduction block ("== Worked out for you ==") work better placed before or
after the seat's carried-forward strategy note? This is catalogue OQ21 in
`evidence/reasoning_failures/deduction_catalogue.md`. This folder reruns the first screen
(`../deduction_placement/`, n=3) at n=10. These are the generated samples only. They are judged blind,
separately, and this folder does not score them.

**Runner:** `evaluation/experiments/deduction_placement_screen.py`, the first run's runner. Two options
were added for this run: `--out` (output folder) and `--max-calls` (request cap; it defaults to 30). Its
cases, arms, settings and hand-filled claims are unchanged.

```
LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
  GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_placement_screen.py \
  --n 10 --max-calls 90 --out evidence/reasoning_failures/data/deduction_placement_n10
# then the same command with --rerun-invalid
```

**Code:** HEAD `30a7048f` plus an **uncommitted working tree**. Since the first run, the tree has gained
deduction slices 11–12 and a reworded roleblock line. The sha256 of
`git diff HEAD -- Agents/ evaluation/src/replay/` is
`b8fbc4fc67fb1f8baba2182ec13edb5699983deb5486658d43140b1f394627c1`. It was the same before and after the
run. It does not cover untracked files: `Agents/` and `evaluation/src/replay/` hold 52 of them, 50 of
those in `Agents/deduction/`. The runner itself is untracked, and its sha256 is `3acb7ccef7ead5b6…`. The
run took place on 2026-10-18, from 01:54 to 02:04 UTC.

## Settings

| | |
|---|---|
| Model | `anthropic/claude-haiku-5-5`, `structured_mode` json_schema (its catalogue row) |
| Thinking | low (`GOOGLE_GENAI_THINKING_LEVEL=low`) |
| Temperature | 1.0, the `get_llm()` default |
| Memory | off (`turn_payload(memory="none")`) |
| `deduction_mode` | "full" |
| Arm A | `deduction_placement` = "before_note" |
| Arm B | `deduction_placement` = "after_note" |
| n | 10 samples per case per arm, so 80 samples |
| Requests | `GAME_LLM_ATTEMPTS=1`, timeout 180 s, no SDK retries; Langfuse tracing off |

**Model calls:** 82, under a cap of 90. That is 80 samples plus 2 reruns. AC2 before_note sample 8 first
returned a malformed read (`reads.4.player` missing), and AC2 after_note sample 4 did too
(`reads.3.player` missing). Both failed validation. The SDK made no retries.

**Cost:** $0.0938 (784,880 input tokens, of which 456,173 were cached and 14,611 were cache writes, and
112,067 output tokens, of which 66,029 were reasoning). The main pass cost $0.0915 and the two reruns
$0.0024. This time the recorded cost includes the cache-write premium.

## Cases

These are the same four acceptance cases, on their frozen states, as in the first run.

| Case | Turn | Frozen case |
|---|---|---|
| AC1 | 2f19d908, day 2, player_8 the Healer, the discussion turn after player_7's admission | `deduction_injection/cases.jsonl` `9b3219e5dc1eb831` |
| AC2 | 2f19d908, day 3 vote, player_5 the Investigator | `haiku_effort_replay/vote_cases.jsonl` `9b827b695a61ece9` |
| AC3 | 403f4dbc, day 3, player_4 the Investigator, the visit-direction turn | `haiku_effort_replay/turn_cases.jsonl` `c52500274ffeccf0` |
| AC4 | 403f4dbc, day 5 vote, player_2 the Vigilante | `haiku_effort_replay/vote_cases.jsonl` `5b11c9fd2f6b9b0e` |

**Hand-filled claims (AC1, AC3).** They are the same as in the first run. They equal
`tests/engine/deduction/test_joins.py` (`_ac1_case`, `_ac3_case`), and the runner checked this at render
time.

- AC1: (2,3) player_5 investigated player_9 on night 1, suspicious. (2,10) and (2,12) player_3 followed
  player_7 on night 1 and saw player_8. (2,15) player_7 visited player_8 on night 1.
- AC3: (3,3) player_4 investigated player_6 on night 2, suspicious. (3,7) player_9 watched player_6 on
  night 2 and saw player_4 and player_8. (3,9) player_6 took no action on night 2.

## Prompt verification (before any model call)

The prompts are in `prompts/<case>_<arm>.txt` (the human message), and the check is in
`prompt_check.json`. Both were re-rendered from the current tree.

- **The arms differ only in where the seat block sits.** For every case:
  - the system message is identical between the arms;
  - the seat block is byte-identical between the arms;
  - with the block cut out, the two human messages are the same apart from one blank line next to the
    block.
- **Where the block goes.** In arm A it sits directly above "Adaptive Strategic thinking:", the
  carried-forward note. In arm B it sits right after the note's closing line ("This is private and will
  not be shared with other players."). From there it runs to just before "Silence rule:" in AC1 and AC3,
  and to just before "Cast your vote." in AC2 and AC4. Each human message has the same length in both
  arms.

| Case | Block lines (A / B) | Block lines | Block characters | Human message characters |
|---|---|---|---|---|
| AC1 | 98–103 / 108–113 | 6 | 710 | 9,682 |
| AC2 | 81–88 / 90–98 | 8 | 1,470 | 11,115 |
| AC3 | 104–112 / 114–122 | 9 | 1,426 | 10,990 |
| AC4 | 106–114 / 115–124 | 9 | 1,215 | 10,395 |

**Changes from the first run's prompts.** The arm A prompts were compared with the first run's.

- AC1: the block gains "No one else claims the Investigator or the Trailseer." In the night record, the
  roleblock line now reads "You were roleblocked: your protection of player_5 did not happen. …". It
  used to read "your action was not carried out".
- AC2: the block gains "No one else claims the Investigator, the Sentinel, the Sigilist or the Healer.
  player_6 and player_10 have made no role claim." The line "player_8 can be the Serial Killer only if
  player_2's watch is false." now goes on to the evidence: player_2's sighting, player_8's protect claim,
  and player_3's will showing the Chanteuse's block on player_8 on night 1. In the night record, the
  roleblock line now reads "your check on player_3 did not happen".
- AC3: the block gains "No one else claims the Investigator or the Sentinel." and "player_6 says it
  visited no one on night 2. That is about where player_6 went. player_9's watch is about who came to
  player_6. The two do not conflict." Nothing outside the block changed.
- AC4: the block gains "No one else claims the Sentinel. player_3 and player_10 have made no role claim."
  and "player_9 says no one came to player_3 on night 4. That is about who came to player_3, not about
  whether player_3 acted." Nothing outside the block changed.

**Key lines, checked verbatim in the rendered prompt:** they are the same strings as in the first run.

| Case | Line | Where it is |
|---|---|---|
| AC1 | line 2 (F2) | seat block |
| AC2 | line 2 (F1) | seat block |
| AC2 | lines 4–5 in their vote form ("player_8 can be the Serial Killer only if player_2's watch is false.") | seat block (now the start of a longer line) |
| AC2 | line 6 (F4) | seat block |
| AC3 | line 1 (A22, "…player_6 is a wolf") | the private night record, not the seat block |
| AC3 | line 2 (F1) | seat block |
| AC4 | lines 1, 2 and 4 | seat block |

AC3 line 1 and AC1's roleblock line stay in the night record, which is in the same place in both arms.

## Files

- `prompts/<case>_<arm>.txt`: the rendered human messages.
- `prompt_check.json`: the verification above.
- `samples.jsonl`: one row per call, 82 rows, with these fields:
  - `case`, `case_id`, `arm`, `sample`, `phase`, `speaker`, `role`, `valid`, `error`, `rerun`;
  - `pass_turn`, `message`, `claim`, `claimed_night_actions`, `vote_target`, `updated_strategy`,
    `reads`;
  - `usage`: `input`, `cached`, `cache_written`, `output`, `reasoning`, `seconds`, `cost_usd`.

  The two invalid rows are kept. Their replacements come at the end of the file, marked `"rerun": true`.
  **For judging, use the latest valid row per (case, arm, sample)**: 80 rows, ten per case and arm.

## Pre-registered measures (copied verbatim; not scored here)

- AC1 (healer): did it speak; does its message or note state the roleblock's consequence (the Chanteuse came to it on night 1) and treat player_7 as possibly/likely the Chanteuse under player_3's report, without asserting player_7 is the Chanteuse as certain; does its read of player_7 say chanteuse.
- AC2 (investigator vote): vote target (the failure was voting player_8); is player_6 or player_10 the target; does the note use the watch/role-claims conditionals.
- AC3 (investigator): does it state player_6 is a wolf from its own check; does it avoid saying player_6's statement and the watch conflict.
- AC4 (vigilante vote): vote target among player_3 / player_9 / player_10; does it avoid dismissing player_9 as "unverified" despite the will confirming part of the report.
