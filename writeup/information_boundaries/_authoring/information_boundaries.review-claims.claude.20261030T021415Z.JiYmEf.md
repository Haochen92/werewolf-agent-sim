<!-- claims review of writeup/information_boundaries/information_boundaries.md by claude (opus), 2026-10-30T02:14Z -->

I've checked every consequential claim on the page. None of them misstates the incident or overclaims a deployment. Seven claims need narrowing; the first two matter most, because each slightly contradicts something the page or the record says elsewhere.

## 1. Findings

- **Claim:** "Every model call's prompt variables are recorded before the call." (*Checking what was actually sent*). The figure's audit arrow is labelled "recorded for every call".
  **Source checked:** `Agents/turn/eval.py::log_prompt`; report §3 ("`run_agent`, which every LLM seat decision goes through"); report §5 ("Two call sites build a prompt input without logging it"); `Agents/turn/round_filter.py` (the opening filter is "One cheap call", via `get_llm_judge`).
  **Verdict:** overstated
  **Why:** Recording happens only on the player-turn path (`run_agent`). The situation-summary query, the opening filter and the echo gate are all model calls that are never recorded. The page's own coverage section admits two unrecorded call kinds, so this sentence contradicts it.
  **Suggested scope:** "Every player turn's prompt variables are recorded before the call", with the figure label changed to match.

- **Claim:** "Unit tests … plant a violation and require the check to catch it, so a check that never fires cannot pass for one that found nothing." (*Checking what was actually sent*)
  **Source checked:** deterministic_audits report row 2 and case 1; agent_boundaries report §5 "Closed" (three checkers fed nothing on live games until 2026-10-14); `tests/engine/test_night_payload_leaks.py`.
  **Verdict:** unsupported inference
  **Why:** A planted-leak unit test shows the check can fire when it is given input. It does not show the batch runner gives it input. That gap is exactly what happened: three correct, unit-tested checks ran on empty inputs in live games until 2026-10-14. The `leak_inputs` tests now cover how those inputs are pulled from a finished game, but the "so…" conclusion is stronger than that.
  **Suggested scope:** "…so each check is shown to fire on a known violation", and drop the "cannot pass for one that found nothing" consequence.

- **Claim:** "Serving another role's lessons would not reveal a current opponent's role, since lessons come from past games; it would break the retrieval rule and give a seat guidance written for a different role." (*What the checks cover*)
  **Source checked:** report §5 "Memory retrieval is enforced by construction, not verified". The sources comment cites only that section.
  **Verdict:** unclear (needs the owner)
  **Why:** The report calls this the top gap and says a wrong-role refactor "would leak another role's memory silently". It never assesses whether that would reveal current roles. The page adds a reassuring argument the record doesn't make. It is plausible (lessons are written offline after past games and contain no seat ids), but it plays down a gap the record ranks first.
  **Suggested scope:** Either the owner confirms the argument and the page keeps it as reasoning ("lessons describe past games, so…"), or the page says what the report says: another role's lessons would reach the seat silently.

- **Claim:** "It shows that the deductions do not depend on hidden information" (*Holding computed advice to the same boundary*)
  **Source checked:** `tests/engine/deduction/test_candidates.py::test_hidden_roles_the_seat_cannot_see_do_not_change_its_items` (one fixed case, one swap). Sibling tests: `test_*_hidden_roles_and_planted_state_change_nothing` and `test_random_games_do_not_change_with_planted_state` in comparisons, conditionals, joins, explanations, evil_seat and covers. Deduction report §4 ("do not establish that every legal interaction has been checked").
  **Verdict:** overstated
  **Why:** The page describes one swap test and then draws a general conclusion. Even the full suite only checks the constructed cases plus the hidden fields planted into random games' payloads. The general guarantee comes from the `SeatView` construction, which the page already states; the tests check it on the cases they cover.
  **Suggested scope:** "It checks, on the tested cases, that the deductions do not change when only hidden information does."

- **Claim:** "the final rendered prompt is not checked every game; it was searched by hand when the break above was found." (*What the checks cover*)
  **Source checked:** experiment_log §2 "Severity" ("An exhaustive grep confirmed the private placeholders render only in role-matched templates"); report §5 ("The §4 grep confirmed non-rendering once; the layout tests check that a held line reaches no rendered prompt").
  **Verdict:** wrong mechanism
  **Why:** What was searched was the templates, for placeholder names, not the rendered prompts. And "by hand" isn't recorded; it was a grep. Also, unit layout tests do check rendered prompts for held lines, so "not checked" is true per game but not across the board.
  **Suggested scope:** "…it is not checked every game; when the break above was found, the templates were searched to confirm none would render the leaked fields."

- **Claim:** "The second formats the payload into the prompt's variables and passes on every field it is given." (*Building the boundary into the input*)
  **Source checked:** `Agents/prompts/prompt_inputs.py::build_agent_prompt_input` (returns a fixed set of keys filled from `payload.get(field, default)`); report §2 layer 3 ("emits every standard key … forwarding whatever the payload contains").
  **Verdict:** wrong mechanism (minor)
  **Why:** The formatter emits one fixed set of variables, the same for every role, and fills each from the payload if it is there. It doesn't forward arbitrary fields. The point the page needs, that it never narrows by role, still holds.
  **Suggested scope:** "The second fills the same full set of prompt variables for every role from whatever the payload holds, never narrowing by role."

- **Claim:** "An assertion that the role asking matches the store served would check it; it is designed, not built." (*What the checks cover*)
  **Source checked:** report §5 ("The fix is an assertion in the retrieval path…").
  **Verdict:** wrong status (minor)
  **Why:** The record proposes the fix in one sentence. It has no design beyond that.
  **Suggested scope:** "…it is proposed, not built."

## 2. Checked and supported

- Public-on-purpose items (the transcript, the dead with revealed roles, the role counts) so that no player has to infer them: report §1 "Public by design".
- Wolves' rosters and night chat reach wolves only: report §1 table; `check_wolf_channel_isolation`.
- Night records, and uses left for their own role only: report §1 table. (A pack kill record goes to every wolf; that is the faction tier and fine at Level 1.)
- Reads and held lines reach no prompt. Reads never enter graph state: experiment_log §4; the `check_reads_isolation` docstring. Held lines reach no prompt, not even their author's: `round_filter.py` module docstring and `nodes/day/actors.py:83`. (The older `check_held_lines_reach_only_their_author` docstring is stale; current code matches the page.)
- Dead players receive nothing further: `check_eliminated_players_excluded`.
- Selection at payload construction is the only enforcement; templates filter only by accident: report §2 layers 2 and 4.
- Several day and night builders apply the same rule: report §1 "Where it is enforced" (`_private_fields`, `solo.py`, `pack.py`).
- Checks run after each successful batch-runner game, and one leak makes the batch exit non-zero: report §3 "Where the checks run".
- Unit tests use the real builders and include planted-leak cases: deterministic_audits row 2; `test_round_payload_leaks.py`, `test_night_payload_leaks.py`, `test_player_reads.py`, `test_wolf_channel_day_visibility.py`.
- Site games save the same inputs: report §3. The live database was upgraded with migration 0013 on 2026-10-15 according to the project memory, so this present-tense claim holds. "Is built to run" for the nightly job follows the owner's ruling and avoids stating the job's install status.
- The incident: the rewrite sent every speaker the same full payload; the docstring justified it by a framework behaviour; the first wired run flagged the wolves' names and the Investigator's results; nothing rendered and no result was affected; the fix gated the payload per role; the next run flagged none. Sources: report §4; experiment_log §2. Leaving out the vigilante field and the vote path is a simplification the brief records, not a misstatement.
- "Found a real break once": consistent with the record. The other events were false alarms or checks receiving no input, not leaks.
- The deduction engine reads only a `SeatView` built from the seat's payload: `Agents/deduction/seat_view.py` docstring; report §1.
- A reworded secret would pass the checks: deterministic_audits case 1 "How far to trust it".
- Memory namespaces are keyed on the requesting role, and nothing asserts it: report §5.
- Ownership: the deduction engine is described as a design, not as the author's code. No test authorship, CI or cron status appears on the page. No Handle-with-care item has reached the page copy.

## 3. Not checked

- "Chapter 1 set the rule…" and the cross-references to chapters 3, 4 and 8: I didn't open the other chapters to confirm they cover what this page says they do.
- Whether all eleven checks have a planted-leak unit test. I confirmed planted tests for the wolf channel, night record, held line, dead player, round players and reads checks, plus the site audit's planted leak. I didn't confirm one specifically for `check_wolf_identity_isolation` or `check_gated_candidate_isolation`. The page only claims planted tests in general, which deterministic_audits row 2 supports.
- Whether the post-fix run in June had a check for the vigilante field active. The record says "all six checks active"; I didn't open the logs. The page doesn't depend on it.
- The brief's open question about where the figure's audit branch attaches: it is drawn from the prompt variables, which matches report §3. Only the owner's sign-off is pending.
