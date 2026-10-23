# Agent Information Boundaries — Build Journey

> **What this is.** The chronological record of how the harness came to guarantee that each agent's
> prompt holds only what its role may know: the checkers, the regression that proved where the
> boundary really lives, each private field added since, and the re-verification of 2026-10-14 that
> found the batch runner feeding half the checkers nothing. Later entries supersede earlier ones;
> where a rule changed, the change is shown in its place.
>
> **Companion docs.** The current contract, stated destination-first, is [`report.md`](report.md).
> The raw run logs of the regression are colocated: `leakwire_smoke.log` (pre-fix) and
> `leakfix_smoke.log` (post-fix), with their JSONL records in `batch_results/legacy/`.

---

## 1. The checkers are written (2026-05-09, `e290b2ff`)

The nine-seat game had four private things: the wolf roster, the wolf channel, the investigator's
results and the healer's target. Four checkers were written over the per-game `prompt_log` (every
agent call's prompt-input dict), one per field, each returning a list of `LEAK:` lines. They ran
from a notebook cell after a game and passed against the concurrent-era day fan-out, which built one
role-filtered payload per role.

They were named `test_*`, so pytest collected them and failed them for missing fixtures from the
day they were written. Renamed to `check_*` on 2026-06-06 (`f5d43a94`); the rename is why they are
not unit tests and must be driven by a runner.

## 2. The 109-flag regression (2026-06-03 to 06, `ef43342` / `8008623` / `e9d30ba`)

**Verdict.** The sequential-discussion rewrite shipped a superset payload that put the wolf roster,
the investigator's results and the vigilante's shot feedback into every speaker's prompt input. The
first wired run of the checkers flagged 109 violations. None reached a model: the templates only
interpolate their declared placeholders, and the private placeholders exist only in role-matched
templates. Role-gating the payload fixed it; the post-fix run flagged 0.

**Cause: a misread of where LangGraph filters.** The rewrite's `build_speaker_send` dispatched one
universal payload to every speaker, justified in its own docstring by "LangGraph ignores extra keys on
a Send payload." LangGraph's input-schema filtering is real but narrow: it applies to typed state
channels and to a compiled subgraph used as a node, which filters its input to its declared schema. It
does not apply to a `Send` into a plain node: the payload arrives verbatim, the node's `TypedDict`
annotation enforces nothing at runtime, and the prompt-input builder reads straight from that payload.
The claim was true of a boundary that was not on this path and false of the one that was. The
documented justification was the bug.

**Composition of the 109: flag events, not distinct inputs.** The superset handed each input
everything, so one input tripped several checks.
- 76 wolf-identity flags: the wolf-identity checker emits two lines per contaminated input (one for
  the `surviving_wolves` field, one for the names extracted from it), so 38 non-wolf inputs × 2.
- 33 `investigator_results` flags: 33 non-investigator inputs.
- 76 + 33 = 109.

**A third field outside the count, and on the vote path too.** `vigilante_results` was also leaking
but contributed 0 to the 109 because no checker covered it; found by inspection,
`check_vigilante_results_isolation` was added afterwards (`8008623`). It leaked through two builders:
the superset in `build_speaker_send` (discussion turns) and `fan_out_day`'s base payload (every
voter). So the contamination was not discussion-only.

**How it persisted.** The checkers were correct and present the whole time; they were not in the
execution path.
- May 9: checkers written against the concurrent-era fan-out. Passing.
- June 3 to 4: the sequential rewrite introduces `build_speaker_send` and the superset payload. The
  checks ran only in a notebook, so nothing fired.
- June 6: checks wired into `run_batch` (`e9d30ba`); the first live game flags the 109.

**Severity: nothing rendered, on either path.** An exhaustive grep confirmed the private placeholders
render only in role-matched templates: `{surviving_wolves}` in the wolf day-discuss, vote, night and
situation-summary templates; `{investigator_results}` in the investigator's; `{vigilante_results}` in
the vigilante's. The template layer dropped the contraband for every contaminated prompt, discussion
and vote alike. Two consequences: every game result to date is unaffected (wolf and serial-killer wins
are genuine dynamics), and even in the worst case the wolf-identity leak would have helped the
village, never the wolves.

**Fix (`ef43342`).** `build_speaker_send` attaches private fields role-gated (wolves get the roster,
the investigator its results, the vigilante its feedback, everyone else none), and `fan_out_day` no
longer puts `vigilante_results` in its base payload. The docstring was rewritten to state the invariant
and why a superset is unsafe.

**Verification.** A post-fix live game with all six checks active (`leakfix_smoke.log`): 0 flags,
`leak_check: {passed: true, leaks: []}`, batch exit 0; the test suite of the day, 27 passed. Both smoke
records carry the runtime fingerprint, so they are self-describing.

**Lessons.**
- A boundary that does not reject is not a boundary. State schemas and templates both tolerate surplus
  data silently; any invariant resting on a permissive layer is violated eventually, without an error.
- "Harmless extra keys" must be checked against every consumer. The superset rationale was right for
  the graph and wrong for the prompt pipeline reading the same dict.
- Checks that do not run on every execution decay into false confidence. Three days of "it passed last
  time someone ran it."
- Audit at the data layer, not the presentation layer. Checking prompt inputs flagged a violation the
  rendered prompts would have hidden. That asymmetry is the early warning.

## 3. The wolf channel rides into the day (2026-07-05, `2a8792c1`)

Originally the wolf day state carried no `wolf_channel`, so wolves could not cite their night
coordination by day. That was design scoping, not an isolation rule: the channel is the wolves' own
information, so giving it to a wolf is never a leak. The scoping existed for one untested worry, that a
wolf would out itself by parroting night chat in public ("as we planned last night").

From this date wolves carry the channel into their day discuss and vote turns, mirroring how the
investigator and vigilante got their private results by day; it also fixed the day lag on the whiff
note and the wolf day situation-summary slot that rendered empty. The self-leak worry is handled by a
confidentiality instruction in the wolf day prompts and was flagged for measurement on a later batch.
`check_wolf_channel_isolation` was re-scoped from "night only" to "a wolf's own prompts only": the
true invariant is by player, not by phase.

## 4. Two private things that are not fields (2026-07-02 to 07-17)

**Held lines (`f9f767d2`, 2026-07-02).** The novelty gate started holding a repeated sweep line back
as a pass marker that keeps the candidate text. The text was never said, so it must reach no other
player's prompt. `check_gated_candidate_isolation` scans every prompt input for every held candidate.

**Reads (`f3537bae`, 2026-07-15).** Each turn now produces the agent's honest role suspicions. A
wolf's read labels its packmate "wolf", so reads are private by construction: they live on the typed
turn result and never enter graph state. `check_reads_isolation` guards against a formatter or
template regression in two passes, structural (a rendered read object anywhere in a prompt input) and
prose (a long "why" text appearing in another player's prompt). The prose pass false-positived twice
and was narrowed each time, in place:
- 2026-07-09 (smoke): shared game vocabulary ("confirmed healer") lives in public discussion, store
  memories and the author's own note at once. Whys under 40 characters are skipped, and a why that
  also appears in the public text cannot be attributed to a leak.
- 2026-07-17 (`a010dc68`): a needle at the 40-character floor, "abstained during the serial killer
  lynch", matched inside the recipient's own strategy note and halted the v7 run. Recipient-authored
  prose is excluded from the prose pass: convergence on the same phrasing of a public event is not
  receipt.
- 2026-10-11 (`4a78bf7f`): a ten-seat pilot flagged the chanteuse's own chat line in the illusionist's
  prompt. The pack's chat is excluded the same way: only wolves write it and only wolves read it.

## 5. The ten-seat game (2026-10-03 to 10-14)

**One record per night actor replaces the result fields (`f1b3017b`, 2026-10-03).** The audit of
2026-10-03 found the healer had no record of its own protections and the vigilante learned only
immune shots. Night resolution now writes a `NightActionRecord` for every actor, and the pack's kill
under the actor "wolves". Each payload builder hands a player only its own records (`own_night_actions`:
the player's, plus the pack's for a wolf). `investigator_results` and `vigilante_results` became
nine-seat fields, kept so old logs still check. `check_night_record_isolation` (`9b729aac`,
2026-10-09) is their successor: a record's outcome text may appear only in its actor's prompts.

**One gate function for the day (`_private_fields`).** With twelve roles, the per-builder gating of
§2 became one function that every day builder calls: the pack's rosters and chat to a wolf, the own
night record to any night actor, uses left to a limited role, the speculator's pick and the fortune
teller's points to those roles. The night builders (`night_turn_payload` for a solo actor,
`_pack_payload` for a wolf) apply the same rule.

**The unit regression closes (`3bc222ee`, 2026-10-07).** The gap recorded on 2026-06-06 ("the only
thing enforcing the fix is the live check") closed with
`tests/engine/test_round_payload_leaks.py`: the standing checks run over the opening, closing and
sweep payloads, and each private field is asserted to reach its own role only. The same commit added
`check_held_lines_reach_only_their_author` (the current rule for held lines, after the author started
seeing its own held line) and `check_round_players_are_seat_ids` (the round's player list reaches the
spectator wire, so it must hold bare seat ids). Both run in unit tests only; a live game does not
retain the round lists.

**The shared-prefix layout (`d41b1c0c`, 2026-10-14).** Every prompt is now composed as rules, then
the public record (the cache boundary), then the board, the role card, the instructions, the private
results and the brief. Private placeholders live in the role cards. The layout changed nothing at the
payload boundary; a held line now reaches no prompt at all, since the transcript is the same bytes for
every seat (`tests/engine/test_shared_prefix_layout.py`).

## 6. Re-verification against the code (2026-10-14, at `0566de66`)

The report was re-read against the code before the portfolio write-up. The mechanism held; the
description had drifted (the nine-seat roles, the identifiers, "six checks" where there were eleven).
One finding changed the code.

**Problem: three checkers were fed nothing.** `run_leak_tests` had grown optional arguments for the
eliminated players (May), the held candidates (July) and the night records (October). The batch runner
and the two capture scripts passed only the prompt log, the roles and the reads. So on every live game
`check_night_record_isolation`, `check_gated_candidate_isolation` and
`check_eliminated_players_excluded` ran over empty inputs and returned nothing. The night-record check
is the ten-seat successor of the investigator and vigilante checks, so night-result isolation had no
live check at all since 2026-10-03; it was guaranteed by the builders and verified only in unit tests.
Exactly the §2 failure shape: a correct checker outside the execution path.

**Fix.** `leak_inputs(result)` in `tests/leak_test.py` lifts the three inputs out of the final game
state (the dead roster, the candidate text of every held marker, the night records); the batch runner
and both capture scripts call `run_leak_tests(prompt_log, roles, **leak_inputs(result))`. The
eliminated-player check was rewritten at the same time: it had read the elimination day out of the
game master's prose ("Player X has been voted out", "was killed by the wolves last night"), and the
ten-seat morning announcements no longer use the second form, so even when fed it would have missed
night deaths. It now takes the death records: a player lynched on day D gets no night turn that day
and nothing later; a player killed on night D gets nothing from day D+1.

**Tests (`tests/engine/test_night_payload_leaks.py`).** The two night builders are pinned the way the
day builders were on 2026-10-07: a solo payload carries no pack field and only its own record, a pack
payload carries the pack to a wolf and the pack record only, the standing checks pass over a ten-seat
night log and flag a planted record; `leak_inputs` lifts the three inputs and feeds nothing from an
empty result; the eliminated check passes a night victim's own night turn and flags its next day, and
flags a lynched player's night turn. 1064 engine and evaluation tests pass.

**The served game, the same day.** The gap "the served game runs no leak check" was closed in the
same session, delegated to a coding agent and reviewed. Two facts drove the design. The capture was
one process-global list: the batch runner clears it per game, but the server never did, so served
games' prompts interleaved across rooms and accumulated for the life of the process (a memory leak
nobody had noticed). And the server container has no writable game-data directory; everything
durable is in Postgres. So: the capture is a context variable set per game beside the game's model
handle (`TURN_CAPTURE` in `Agents/turn/eval.py`, defaulting to the old globals so the batch runner
is unchanged); at game end the session saves the prompts, the reads and the six state fields the
checks read as one gzip row (`prompt_captures`, migration 0013; a fixture game packs 139 KB into
9.5 KB); `leak-audit` (`server/housekeeping/leak_audit.py`) runs the nine checks over every unaudited
row and writes the verdict back. A game resumed after a restart is captured only from the restart and
marked partial. Nine tests; 1352 engine, server and evaluation tests pass. Not yet deployed: the
migration must be applied and the cron line installed.

**Still open after this entry** (the report's §5 carries the current list): the memory-retrieval
namespace is enforced by construction and still not asserted; the situation-summary call and the
human seat build a prompt input from the same payload but do not log it; no standing audit reads the
rendered prompt; a restarted served game is only partly captured.

---

**Sources.** `tests/leak_test.py` (the checkers and `leak_inputs`), `Agents/nodes/day/flow.py`
(`_private_fields`, the day builders), `Agents/nodes/night/solo.py` and `pack.py` (the night
builders), `Agents/prompts/prompt_inputs.py` (the superset formatter), `Agents/prompts/layout.py` (the
layout), `scripts/run_batch.py` (the live wiring); commits as cited per entry.
