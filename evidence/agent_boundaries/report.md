# Agent Information Boundaries

**Scope:** how the harness guarantees each agent's prompt contains only what its role may know:
where that boundary is enforced, how it is verified, and the regression that proved the model real.
**First written:** 2026-06-06 (`feature-tracing`, `ef43342` / `8008623` / `e9d30ba`).
**Revised against the code:** 2026-10-14 at `0566de66` (the ten-seat game, the shared-prefix prompt
layout, langgraph 1.1.10); the journey, including the full forensics of the regression, is in
[`experiment_log.md`](experiment_log.md).
**Artifacts (the proof behind §4):** `leakwire_smoke.log` (pre-fix; the 109 `LEAK:` lines are the
signal, the rest is tracing noise) · `leakfix_smoke.log` (post-fix; the proof is the absence of
`LEAK:` lines between `=== Running Leak Tests ===` and `=== Complete ===`, plus `EXIT: 0`) · JSONL
records in `batch_results/legacy/leak{wire,fix}_smoke.jsonl`.

> **Orientation: the prompt-assembly path.** Every agent prompt is built along one path:
>
> **game state → `Send` payload → prompt-input dict → rendered prompt → model**
>
> Those four arrows are the four boundary layers of §2. Isolation is only as strong as the narrowest
> arrow, and only the second one narrows. Every identifier below (`_private_fields`, `run_agent`,
> `prompt_log`, `check_*`) hangs somewhere on this path.

---

## 1. The guarantee (current contract)

Werewolf is a hidden-information game, so the contract is: **each role's prompt contains only what
that role is allowed to know, enforced where the payload is built (layer 2) and verified on every
batch game at the data layer.**

**What is private.** The game deals ten seats from twelve roles. Each private thing has one
legitimate consumer:

| Private field | Sole consumer |
|---|---|
| `surviving_wolves`, `surviving_villagers` (the pack's rosters) and `initial_wolf_count` (a count, no names) | the pack (chanteuse, illusionist) |
| `wolf_channel` (the pack's night chat and the carrier's kill) | the pack, by night and by day |
| `night_actions` (what a night actor did and learned: the healer's saves, the investigator's results, the sentinel's watches, the vigilante's shots, and so on) | that actor only; a pack kill is recorded under the actor `wolves` and reaches every wolf |
| `uses_left` / `vigilante_bullets` (a limited ability's remaining uses) | the role with the limit |
| `speculator_pick`, `fortune_points`, the necromancer's `bodies` | that role |
| reads (an agent's honest role suspicions, part of every decision) | nobody: never enters graph state |
| a held line (a sweep turn the echo gate or the opening filter kept back) | nobody: never said, never in the transcript |
| `healer_target` | nobody's prompt, ever |

Public by design, on every payload: the day transcript and summaries, the dead roster with each
revealed role (a concealed body hides its role), the cast census as counts, the lineup, and the
survivor list. These were made public deliberately in the information-fidelity pass of October 2026
so that no role has to infer them from prose.

**Where it is enforced.** The payload builders (layer 2) decide what data physically reaches a node.
By day, one function, `_private_fields` in `Agents/nodes/day/flow.py`, attaches a player's private
fields by role, and all three day builders (the sweep and reactive turns, the vote fan-out, the
opening and closing rounds) call it. By night, the solo builder (`Agents/nodes/night/solo.py`) and the
pack builder (`Agents/nodes/night/pack.py`) apply the same rule. Nothing downstream narrows: layers 1,
3 and 4 forward or only incidentally filter (§2), so the payload is the only place the guarantee can
live. Two shaping decisions carry it: every non-wolf payload uses the role-blind `surviving_players`
list, never the wolf-visible rosters, and every night actor gets its own records through one filter
(`own_night_actions`). The deduction engine, which writes code-derived conclusions into an AI seat's
prompt, is a consumer of the payload, not a second path: it reads a `SeatView` built only from that
seat's payload (`Agents/deduction/seat_view.py::seat_view_from_payload`), so it can conclude only
from what the seat may know ([the deduction report](../gameplay/deduction/report.md) §1).

**How it is verified.** Eleven `check_*` invariants in `tests/leak_test.py`; nine run on every
batch game over the prompt-input dict, one layer upstream of rendering, and the batch exits non-zero
on any violation (§3). Two more run in unit tests only. The day and night builders are also pinned by
unit tests that assert each private field reaches its own role and no other.

**The rule, quotable:** *enforce at construction, verify continuously at the data layer.*

What this contract does not cover is collected in §5. The spectator wire has its own boundary in the
server (what a viewer sees is decided per event type, from public knowledge only); it is out of scope
here.

## 2. The boundary model: four layers, one enforcer

Knowing which layer enforces is the whole point. Three of the four only document or tolerate; one
rejects.

| # | Layer | What it does | Enforced at runtime? |
|---|---|---|---|
| 1 | **Graph-state TypedDicts** (`Agents/state/`: the day state, `NightTurnState`, the pack's night state) | Document which fields each role's node should see | **No.** LangGraph hands a `Send`-dispatched node the raw payload dict; undeclared keys are not stripped. Documentation only. (A compiled subgraph used as a node does filter its input to its declared schema, but these role nodes are `Send`-dispatched, so that filtering never applies here.) |
| 2 | **Payload construction** (`_private_fields` and the day builders in `Agents/nodes/day/flow.py`; `night_turn_payload` and `_pack_payload` in `Agents/nodes/night/`) | Decide what data is physically present in a node's payload | **Yes. This is the real boundary.** If private data is not in the payload, nothing downstream can expose it. |
| 3 | **Prompt-input formatting** (`build_agent_prompt_input` in `Agents/prompts/prompt_inputs.py`) | One superset formatter for all roles: emits every standard key with a safe default or sentinel, forwarding whatever the payload contains | **No, deliberately permissive.** It widens, never narrows. |
| 4 | **Template rendering** (the shared-prefix layout in `Agents/prompts/layout.py`, the role cards in `Agents/prompts/roles/`) | Each `ChatPromptTemplate` interpolates only its declared `{placeholders}`; surplus input keys are silently ignored (LangChain errors on missing variables only, never on extra ones). Private placeholders live in the role cards, after the shared public prefix | **Incidental.** A rendering filter, not a guard: protection equals "which placeholders this role's card declares", re-decided on every prompt edit. |

The consequence: an isolation guarantee may rest only on layer 2. Layers 1 and 3 forward whatever
they are handed; layer 4's filtering is an accident of which placeholders a card declares. Lean on any
of the three and the boundary holds only until the next refactor, which is exactly what §4 is.

*Framework note.* The LangGraph and LangChain behaviours asserted here and in §4 (a `Send` delivers
its payload verbatim, a compiled subgraph used as a node filters to its input schema, a template
ignores surplus keys and errors only on missing ones) hold for the pinned `langgraph==1.1.10` and
`langchain-core==1.3.3` in `pyproject.toml`. A reader on another version should re-confirm before
relying on them.

## 3. How we verify: the leak checks

The capture point is `prompt_log` in `Agents/turn/eval.py`: `run_agent`
(`Agents/turn/agent_player.py`), which every LLM seat decision goes through by day and by night,
appends each call's prompt-input dict before generating. `run_game` clears the log at start, so after
a game the global holds exactly that game's prompts. `leak_inputs(result)` lifts the rest of what the
checkers need out of the final game state (the dead roster, the text of every held line, the night
records), and `run_leak_tests(prompt_log, roles, **leak_inputs(result))` runs the nine live checks.

| Check | Invariant | Runs |
|---|---|---|
| `check_wolf_identity_isolation` | A non-wolf's prompt input carries no wolf roster and no wolf name | live |
| `check_wolf_channel_isolation` | The pack's chat appears only in a wolf's own prompts, night or day (re-scoped by player, not phase, 2026-07-05) | live |
| `check_night_record_isolation` | A night record's outcome text appears only in its actor's prompts; a pack record only in the wolves' (the ten-seat successor of the two result-field checks below, 2026-10-09) | live |
| `check_investigator_results_isolation`, `check_vigilante_results_isolation` | Nine-seat result fields reach only their role; kept so old logs still check | live, dormant on ten-seat games |
| `check_healer_target_absent` | `healer_target` in no prompt input at all | live |
| `check_eliminated_players_excluded` | A player lynched on day D gets no night turn that day and nothing later; a player killed on night D gets nothing from day D+1 (keyed on the death records since 2026-10-14) | live |
| `check_gated_candidate_isolation` | A held line's text appears in no prompt input | live |
| `check_reads_isolation` | No rendered read object in any prompt input (structural pass); no long private "why" text in another player's prompt unless it is also public text (prose pass) | live |
| `check_held_lines_reach_only_their_author` | The current held-line rule, over the round payloads | unit tests only |
| `check_round_players_are_seat_ids` | The round's player list, which reaches the spectator wire, holds bare seat ids and nothing else | unit tests only |

**Audit the data layer, not the presentation layer.** The checks inspect the prompt-input dict
(layer 3's output), not the rendered prompt.

A subtlety the superset formatter forces: layer 3 emits every private key for every role (§2), so a
key is always present and the checks key on the value, not on the key's presence. Missing private data
defaults to an empty value or a sentinel (`"No messages yet."` for the pack's chat, an empty roster,
an empty night record), and a check fires only on real content. The only way real content reaches
the dict is if the layer-2 payload carried it, since layer 3 just forwards `payload.get(field,
default)`. So a non-default value means the payload boundary was crossed.

A flag therefore means "private data crossed the payload boundary", which may or may not have
rendered (the separate layer-4 question of whether the role's card declares the placeholder), but it
is always a violated invariant and always one template edit from real exposure. Auditing one layer
upstream of where exposure becomes visible is what turned the §4 regression into an early warning
rather than a silent time bomb.

**Where the checks run.** The batch runner (`run_batch`) and the capture scripts under
`evaluation/experiments/` run them after every successful game, record the verdict in each JSONL
record as `leak_check: {passed, leaks}`, print `LEAK DETECTED` per game, and exit non-zero if any
game leaked, while still writing the game result. The unit tests
(`tests/engine/test_round_payload_leaks.py`, `test_night_payload_leaks.py`,
`test_night_whiff_disclosure.py`) run the same checks over payloads built by the real builders from a
fixed ten-seat state, and assert field by field that each private field reaches its own role only. Served games on the
website are audited after the fact: each finished game saves the prompts its agents were sent, its
reads and the six final-state fields the checks read, as one compressed row, and a nightly command
(`leak-audit`, in `server/housekeeping/`) runs the same nine checks over every game not yet audited
and writes the verdict back on the row (built 2026-10-14; live once the `prompt_captures` migration is
applied and the cron line installed).

## 4. Case study: the 109-flag regression (2026-06-06)

A convenience refactor in the sequential-discussion rewrite shipped a superset payload that put
private fields (the wolf roster, the investigator's results, the vigilante's shot feedback) into the
prompt inputs of roles that should not see them. The first wired run of the leak checks flagged 109
violations (`leakwire_smoke.log`). None of it reached a model: layer 4 dropped every contaminated
field, confirmed by an exhaustive grep of the templates. So no past game result is tainted, and even
rendered, the leak would have helped the village, never the wolves. Role-gating the payload at layer 2
(`ef43342`) fixed it; the post-fix run flagged 0 with all checks active (`leakfix_smoke.log`).

**The cause was the documented justification.** The rewrite's speaker builder dispatched one
universal payload to every speaker, justified in its own docstring by "LangGraph ignores extra keys on
a Send payload." That is true of a compiled subgraph's input boundary and false of a `Send` into a
plain node, which is the path these builders are on: the payload arrives verbatim, the state
annotation enforces nothing, and the prompt-input builder reads straight from it. Layers 1, 3 and 4
all forwarded the contraband silently, as the §2 model predicts.

**Why it persisted for three days.** The checkers were correct the whole time. They ran only from a
notebook cell, so nothing fired between the rewrite (June 3 to 4) and the day they were wired into the
batch runner (June 6). One field, the vigilante's feedback, had no checker at all and was found by
inspection, leaking through the vote fan-out as well as the discussion turns.

**What it proved.** A layer-2 violation that every permissive layer forwarded, caught only at the data
layer: the §2 model is not a diagram but the thing that found the bug. The flag-count arithmetic, the
per-field grep, the timeline and the commit-level detail are in
[`experiment_log.md` §2](experiment_log.md).

**Lessons.**
- A boundary that does not reject is not a boundary. State schemas and templates both tolerate surplus
  data silently; any invariant resting on a permissive layer is violated eventually, without an error.
- "Harmless extra keys" must be checked against every consumer of the same dict.
- Checks that do not run on every execution decay into false confidence. The same shape recurred on
  2026-10-14: three checkers had been wired with inputs the runner never passed (§5, closed).
- Audit at the data layer, not the presentation layer.

## 5. Known gaps: what is not guaranteed yet

Where the boundary is not enforced or not verified, with the consequence of each. A gap stays on this
list when minor; the list is the audit trail. Each carries the date it was last confirmed.

### Memory retrieval is enforced by construction, not verified (open, confirmed 2026-10-14)

Retrieved observations and strategy points come from role-keyed namespaces,
`("observations", role, phase)` and `("strategy_points", role, phase)` in
`Agents/memory/retrieval/accessors.py`, where `role` is the requesting agent's own. The boundary holds
because a caller can only query its own namespace, exactly like the payload boundary before the §3
checks existed, and it is not independently asserted. It is worse than the payload case in one way:
the checks key on structured fields and are blind to free-text memory, so a refactor that passed the
wrong role would leak another role's memory silently. The exposure is latent (it needs a future
refactor to break the keying), which is why this is the top gap but not a live hole. The fix is an
assertion in the retrieval path that the requesting role equals the namespace served, run per game as
the memory-pipeline analogue of the §3 set. Memory in the served demo is currently strategy points
only, behind a per-game toggle; the gap applies whenever memory is on.

### A served game resumed after a restart is only partly captured (open, 2026-10-14)

The capture lives with the game's process, so a game resumed after a server restart saves only the
prompts sent after the restart. Its row is marked partial and the audit says so. Low consequence: the
builders and unit tests still cover the lost turns; only the after-the-fact audit is incomplete for
that game.

### Lower criticality (tracked, confirmed 2026-10-14)

- **Two call sites build a prompt input without logging it.** The situation-summary query
  (`Agents/memory/retrieval/situation_agent.py`) and the human seat (`Agents/turn/human_turn.py`)
  both build their prompt input from the same role-gated payload, so the layer-2 fix covers them, but
  neither appends to `prompt_log`, so the checks cannot see them. A checker-visibility gap, not an
  active leak.
- **No standing audit of the rendered prompt.** The §4 grep confirmed non-rendering once; the layout
  tests check that a held line reaches no rendered prompt. A spot check that wolf-only rendered
  phrases ("Your wolf allies:") never appear in a non-wolf's rendered prompt would verify the last
  layer end to end. Worth one run per major prompt rework, not standing CI.
- **The served-game audit needs a deploy step.** The `prompt_captures` table arrives with alembic
  migration 0013; until it is applied, each save fails, is logged, and the game is unaffected. The
  nightly cron line is documented in the audit module and `server/README.md`, not installed.
- **The two unit-only checks have no live counterpart.** The held-line rule and the round's player
  list are checked over payloads built in tests; a live game does not retain the round lists. Low risk:
  the gated-candidate check covers held text live, and the wire's own schema holds seat ids.

### Closed

- **Fast unit regression for payload gating** (opened 2026-06-06, closed 2026-10-07): the day
  builders are pinned by `tests/engine/test_round_payload_leaks.py`, the night builders by
  `test_night_payload_leaks.py` (2026-10-14).
- **Three checkers fed nothing on live games** (found and closed 2026-10-14): the night-record,
  held-line and eliminated-player checks had optional inputs the batch runner never passed, so they
  were no-ops on every live game; the night-record check had been the only live check on night-result
  isolation since 2026-10-03. `leak_inputs(result)` now feeds all three from the final game state. The
  eliminated-player check was also rewritten onto the death records; it had parsed the game master's
  prose, which the ten-seat game no longer writes in that form.
- **The served game ran no leak check** (opened 2026-06-06 as a gap in coverage, closed 2026-10-14):
  the prompt capture was one process-global list, which the server never cleared, so served games'
  prompts both interleaved across rooms and accumulated in memory for the life of the process. The
  capture is now scoped per game (a context variable set beside the game's model handle), saved at
  game end, and audited nightly by `leak-audit` (§3). Tests: concurrent games never write into each
  other's capture; the audit finds a fixture game clean and flags a planted leak and a prompted dead
  player.
