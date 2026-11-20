# Deduction block placement screen (OQ21): generation only

**Question:** does the seat's deduction block ("== Worked out for you ==") work better placed before or
after the seat's carried-forward strategy note? This is catalogue OQ21 in
`evidence/gameplay/deduction/deduction_catalogue.md`. These are the generated samples only. They are
judged blind, separately, and this folder does not score them.

**Runner:** `evaluation/experiments/deduction_placement_screen.py`. It reuses the replay bench's
`turn_payload` / `turn_template` and `generate`'s chain setup (legal-target schema, structured output on
`get_llm()`). It does not use the bench's judging.

**Code:** HEAD `2256b59e` plus an **uncommitted working tree**. Deduction slices 8–10 and the
placement setting are uncommitted, and other sessions were editing `Agents/` at the time. The sha256 of
`git diff HEAD -- Agents/ evaluation/src/replay/` is `0f7ee37b68e54b7c…`. It does not cover
untracked files, and `Agents/deduction/` holds 38 of them. The run took place on 2026-10-17.

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
| n | 3 samples per case per arm, so 24 samples |
| Requests | `GAME_LLM_ATTEMPTS=1`, timeout 180 s, no SDK retries |

**Model calls:** 25. That is 24 samples plus 1 rerun: AC2 before_note sample 2 first returned a
malformed read (`reads.3.player` missing), so it failed validation.

**Cost:** $0.0308 as recorded (236,953 input tokens, of which 129,085 were cached, and 37,444 output
tokens, of which 23,626 were reasoning). The recorded cost leaves out the cache-write premium, because
the runner read the wrong usage key; that is fixed now. The premium adds at most $0.0027, so the total
is at most $0.034.

## Cases

The four acceptance cases are on their frozen states.

| Case | Turn | Frozen case |
|---|---|---|
| AC1 | 2f19d908, day 2, player_8 the Healer, the discussion turn after player_7's admission | `deduction_injection/cases.jsonl` `9b3219e5dc1eb831` |
| AC2 | 2f19d908, day 3 vote, player_5 the Investigator | `haiku_effort_replay/vote_cases.jsonl` `9b827b695a61ece9` |
| AC3 | 403f4dbc, day 3, player_4 the Investigator, the visit-direction turn | `haiku_effort_replay/turn_cases.jsonl` `c52500274ffeccf0` |
| AC4 | 403f4dbc, day 5 vote, player_2 the Vigilante | `haiku_effort_replay/vote_cases.jsonl` `5b11c9fd2f6b9b0e` |

**Hand-filled claims (AC1, AC3).** AC1's and AC3's claims were made that same day, and no frozen day
summary carries them. The speaker field `claimed_night_actions` was therefore filled by hand on the
frozen messages, from their own words. These are exactly the entries in
`tests/engine/deduction/test_joins.py` (`_ac1_case`, `_ac3_case`), and the runner checks that they are
equal at render time.

- AC1: (2,3) player_5 investigated player_9 on night 1, suspicious. (2,10) and (2,12) player_3 followed
  player_7 on night 1 and saw player_8. (2,15) player_7 visited player_8 on night 1.
- AC3: (3,3) player_4 investigated player_6 on night 2, suspicious. (3,7) player_9 watched player_6 on
  night 2 and saw player_4 and player_8. (3,9) player_6 took no action on night 2.

Without these entries the block lacks the lines under test: AC1 line 2 and AC3 line 2.

## Prompt verification (before any model call)

The prompts are in `prompts/<case>_<arm>.txt` (the human message), and the check is in
`prompt_check.json`.

- **The arms differ only in where the seat block sits.** For every case:
  - the system message is identical between the arms;
  - the seat block is byte-identical between the arms;
  - with the block cut out, the two human messages are the same apart from one blank line next to the
    block.
- **Where the block goes.** In arm A it sits directly above "Adaptive Strategic thinking:", the
  carried-forward note. In arm B it sits right after the note's closing line ("This is private and will
  not be shared with other players."), just before "Silence rule:" (discussion) or the vote
  instructions. Each human message has the same length in both arms.
- **Block size** (lines including the heading and the preamble / characters):

| Case | Lines | Characters |
|---|---|---|
| AC1 | 5 | 654 |
| AC2 | 7 | 1,018 |
| AC3 | 7 | 1,217 |
| AC4 | 7 | 1,010 |

**Key lines, checked verbatim in the rendered prompt:**

| Case | Line | Where it is |
|---|---|---|
| AC1 | line 2 (F2) | seat block |
| AC2 | line 2 (F1) | seat block |
| AC2 | lines 4–5 in their vote form ("player_8 can be the Serial Killer only if player_2's watch is false.") | seat block |
| AC2 | line 6 (F4) | seat block |
| AC3 | line 1 (A22, "…player_6 is a wolf") | the private night record, not the seat block |
| AC3 | line 2 (F1) | seat block |
| AC4 | lines 1, 2 and 4 | seat block |

AC3 line 1 is a level-1 line. By design those sit beside the seat's own night record ("Night 2 (last
night): you checked player_6. … player_6 is a wolf."), so this line is in **the same place in both
arms**. AC1 line 1, the roleblock line, also stays in the night record in both arms.

## Files

- `prompts/<case>_<arm>.txt`: the rendered human messages.
- `prompt_check.json`: the verification above.
- `samples.jsonl`: one row per call, with these fields:
  - `case`, `case_id`, `arm`, `sample`, `phase`, `speaker`, `role`, `valid`, `error`;
  - `pass_turn`, `message`, `claim`, `claimed_night_actions`, `vote_target`, `updated_strategy`,
    `reads`;
  - `usage` (tokens, `cost_usd`).

  The invalid AC2 before_note sample 2 row is kept. Its replacement follows it, marked
  `"rerun": true`. **For judging, use the valid rows** (24, three per case and arm).

## Pre-registered measures (copied verbatim; not scored here)

- AC1 (healer): did it speak; does its message or note state the roleblock's consequence (the Chanteuse came to it on night 1) and treat player_7 as possibly/likely the Chanteuse under player_3's report, without asserting player_7 is the Chanteuse as certain; does its read of player_7 say chanteuse.
- AC2 (investigator vote): vote target (the failure was voting player_8); is player_6 or player_10 the target; does the note use the watch/role-claims conditionals.
- AC3 (investigator): does it state player_6 is a wolf from its own check; does it avoid saying player_6's statement and the watch conflict.
- AC4 (vigilante vote): vote target among player_3 / player_9 / player_10; does it avoid dismissing player_9 as "unverified" despite the will confirming part of the report.
