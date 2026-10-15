# Orchestrator_Graph — event derivation (final)

> The companion to `server/game/translate.py`: one section per graph node, in the order the
> nodes run, titled with the node's registry name so a `@node("...")` in the code and its
> section here share a string. Each table says what that node sends and to whom; IGNORED marks
> a state field the node writes that the browser has no use for. This is prose and nothing
> checks it against the code. The exact output on a recorded game is pinned by the goldens
> in `tests/fixtures/translator_golden*.jsonl`; when the two disagree, the goldens are right
> and this file gets corrected.

**INITIALIZE_GAME**

| Tier | Events |
| --- | --- |
| Public | `game_started {seats, cast_role_counts, lineup}` — `lineup` the ten dealt roles in the rules block's order |
| Faction | — |
| Seat | `role_assigned {role, pack? (the pack's roles), uses? (a limited ability's start), bullets? (nine-seat records)}` ×10 |
| Observer | `roles_assigned {player: role}` — nobody receives it live; exists so the game_over backlog replay has survivor roles from minute zero |
- `phase_change("day")` — marker table (node identity). `human_player` = no event (session handshake).

**DAY_PHASE · SCHEDULE** — registered silent. SCHEDULE writes nothing; DAY_PHASE is the root wrapper whose commit repeats what the day subgraph already streamed (see Stream behaviours below).

**START_OPENING · START_CLOSING** (the entry node of a round, Phase 2 — discussion_evidence.md §7: every player of the round takes a turn at once; the day opens with the opening round, the closing gives the most-accused a last word. The scheduler's sweep turns, which give the floor to the players who have not spoken one at a time, are ordinary `discuss` turns with `firing_reason.tier = proactive`)

| Tier | Events |
| --- | --- |
| Public | `round_opened {round: opening\|closing, players}` — the node's `round_players` delta, in the order the lines will be played (seat order; the accused as called). The stage reads "preparing" from it and derives a round's passes as players of the round with no speech, so there is no pass event for a round |
| Public | `gm_message` — START_CLOSING only: the moderator's announcement of who is accused and by whom, written to `day_channel` by the node from the accusation tags (no model call) |
| Seat | `input_request {.., round}` — a human in the round, born from the `human_turn_opened` custom chunk `fan_out_round` writes as the round starts (same mechanism as the vote's); `round` names the round so the composer can label the ask. The interrupt that ends the step then emits none |
- `day_round` (which round runs) → IGNORED: loop control; the event carries the round.

**round_turn · round_turn_human** — a round's turn (the generic actor, cached; the human seat through the uncached twin). Its line is held in `round_candidates` → IGNORED on this node (not yet numbered, not yet filtered); only `strategy_update` (observer) is sent from here.

**COLLECT_ROUND** — the barrier after a round: orders the held lines, runs the round's filter (the opening's allow-list, the proactive round's echo filter; a held line becomes a pass marker that keeps its text), numbers them into `day_channel`. Sent through `discuss`'s loop: `speech` or `pass_marker` per line, plus `addressed_targets`; no `firing_reason` (a round turn has none). `turn_started` is never sent for a round turn — `round_opened` announces the whole round instead.

**route_speaker edge** (a `custom` stream chunk, not a node) — `turn_started {player, day}` via `get_stream_writer()` (edge emission — cannot double-fire on interrupt resume).

**every AI decision that produced reads, memory on or off** (a `custom` chunk from inside the acting node, `Agents/turn/pipeline.py`) — observer `player_reads {player, role, day, round, action_phase, reads[{player, suspected_role, confidence, why}]}`: the agent's per-player suspicions at that decision. Never graph state. Node emission, so a re-run fires it again — sent once per `(player, day, round, action_phase)`. A wolf's night turns are told apart by `round`: the chat rounds 1 to 3, the carrier's kill 4, its skill turn 5.

**every AI decision, memory-on games only** (a `custom` chunk from inside the acting node, `Agents/turn/pipeline.py`) — observer `memory_consulted {player, role, day, round, action_phase, lessons[], verdicts[], observations[], applicability[]}`: the lessons/observations retrieved for the decision and the agent's verdict on each. Never graph state (the verdicts are kept out of state on purpose). Node emission, so a re-run (human answer, restart resume) fires it again — sent once per `(player, day, round, action_phase)`, the same guard as a re-run speech. Day 1 never retrieves, so it starts on day 2.

**discuss**

| Tier | Events |
| --- | --- |
| Public | `speech {day, channel_seq, player, message, claim}` — `channel_seq` = position in the day transcript (the state-side DayChannel seq), renamed on the wire because the durable base class already owns the global `seq`; `claim` = the role the speaker's own output claimed in the line, or `none` (Phase 3: the claim ledger's role lines come from these, the summariser's `role_claims` fill in the night actions; records from before the field read `none`) |
| Faction | — |
| Seat | `input_request {player, action_kind, candidates, round}` (interrupt source; human seat only) — `action_kind` + legal-target list lifted from `HumanTurnRequest` so the client can render the right control, and `round` (opening / discussion / proactive / closing) for the label of the ask; the full prompt payload deliberately stays server-side (it duplicates the event log as prose and churns with every prompt epoch) |
| Observer | `strategy_update` · `pass_marker {pass_reason: voluntary\|novelty_gated\|generation_failed\|round_echo\|opening_filtered, gated, gated_candidate}` (the engine's typed reason, not a bare `passed` bool; `novelty_gated` is the echo gate's hold on a sweep turn and `opening_filtered` the opening filter's, both with the held text in `gated_candidate`; `round_echo` only in records of the parallel proactive round, 2026-10-07) · `firing_reason` · `addressed_targets` — annotations join the speech via `about_channel_seq` |
- One delta → speech **or** pass_marker (branch on `entry.passed`). `None` return = no events (turn_started is not a promise).

**SUMMARIZE_DAY_DISCUSSION**

| Tier | Events |
| --- | --- |
| Public | `day_summary {day, summary}` — shown next morning: client render rule, **no buffer** (buffers gate entitlement; render timing gates pacing). Renders as a "Previously…" recap card at the TOP of day D+1's page (mirrors the LLM payload: full current day + summaries of prior days); the full transcript stays readable per day — the summary is a header, never a replacement |
| Observer | `day_summary_structured {day, data}` — `data` is the summarizer's structured output verbatim (accusations / role_claims / alliances / village_dynamics; PROVISIONAL `dict`, typed once the summarizer schema freezes). Sent right after the day's `day_summary`, from the `structured` field the engine stores beside the text (2026-09-15); not sent when that field is empty, i.e. the summarizer failed and the raw channel was stored as the text. Meant for the X-ray ("what the agents carry into today"), never the story surface. |

**START_VOTING** — public `phase_change` (self-disambiguating: anchored on the routed-to node).

**vote · vote_human**

| Tier | Events |
| --- | --- |
| Ephemeral | `phase_progress {stage: "day_vote", done, total}` — anonymous voting-progress snapshot (replaces the durable `player_voted {voter}` indicator; progress ticks are replay noise, and the pattern unifies with night pacing. Denominator = surviving roster, public, no padding needed. Loss accepted: no per-player "waiting on X" checkmarks — reversible additively.) |
| Seat | `input_request` — born from the `human_turn_opened` custom chunk the vote router writes before the step (2026-10-06, server_client_transport.md §8b), so the ballot opens while the agents vote; the interrupt that ends the step then emits none. A night solo role's `input_request` is born the same way at `NIGHT_START`. |
| Observer | `strategy_update` |
- Ballots buffered server-side (entitlement deferral — wire is the boundary, not the render).

**COLLECT_VOTES** — public `vote_cast {voter, votee, day}` batch. Content from the translator buffer, timing from node identity (its own delta is empty). Buffer-empty-at-day-end alarm.

**DAY_RESOLUTION**

| Tier | Events |
| --- | --- |
| Public | `gm_message {day, channel_seq, text}` — verbatim narration (record fidelity outranks derivability for authored text) |
| Public | `lynch_result {outcome: lynched\|tie\|abstain\|no_vote, player?, role?, vote_counts, no_lynch_streak, day}` — the death atom (= the dead_roster delta) + the free-rider fields the node already computed |
| Public | `roster_update {surviving_players}` — **union only**: translator merges the wolf-partitioned lists before the public tier |
| Faction | `pack_roster_update {surviving_wolves}` |
- `voted_player` delta → IGNORED (inside `lynch_result`). The nine-seat `*_player` role markers are gone: a role's aliveness is read off the rosters.
- `day_summaries` vote-result append → IGNORED: verbatim the node's own `gm_message`, and the client renders a day's summary from SUMMARIZE_DAY_DISCUSSION's event alone (ruled 2026-09-15; completion note 3).

**NIGHT_START** (between the `check_game_end_day` and `route_night_actors` edges) —
`check_game_end_day` is binary (END_GAME | NIGHT_START); NIGHT_START is a no-op marker node
(START_VOTING analog) anchoring public `phase_change("night")` — it runs only past the END_GAME
check, so a game-ending day can never ghost a night marker. `route_night_actors` fans out the
present night actors; the real actor list this router computes must **never** reach the wire —
the pacing denominator comes from public knowledge only (see Ephemeral channel).

**`<ROLE>_NIGHT_PHASE`** — one named node per solo night role of the pool (INVESTIGATOR, SENTINEL, TRAILSEER, VIGILANTE, SIGILIST, HEALER, SERIAL_KILLER, NECROMANCER, SPECULATOR, FORTUNE_TELLER), one shared body (Agents/nodes/night/solo.py). The node commits the role's choice to `night_choices` and its strategy note.

| Tier | Events |
| --- | --- |
| Public | — silence is the spec: no per-role markers, no engine-state progress |
| Faction | — |
| Seat | `input_request {action_kind: the role's field}` — born from the `human_turn_opened` chunk `route_night_actors` writes at `NIGHT_START`; the interrupt that ends the step then emits none. `candidates` lists the players and the role's no-action word (`hold_fire`, `keep_sigil`, `stay_put`, `not_yet`) or, for the speculator, the sides; a necromancer's ask also carries `bodies`, the dead players it may act through, and its answer names one beside the target. A fortune teller's `candidates` include itself only while it has a self-bet left |
| Observer | `night_action {actor, role, target, day}` — one per choice (the speculator's `target` is the side; the illusionist's conceal has none) · `strategy_update` |
- A declined action (the no-action word) commits no choice, so no `night_action`.
- `None` return = no events (engine fallback), same as discuss.

**PREPARE_PACK_NIGHT · PACK_CHAT · START_CARRIER · CARRIER_KILL · CARRIER_KILL_HUMAN · PACK_SKILL · PACK_SKILL_HUMAN · COLLECT_PACK** (the pack subgraph, Phase 3: prepare → chat loop, the carrier first, up to three rounds, ending early once every wolf passed in a round → the carrier's kill → the skills in parallel → collect). The pack vote is gone.

| Tier | Events |
| --- | --- |
| Public | — |
| Faction | `wolf_message {wolf, message, day, round, passed}` — sequential chat, sent live; `passed` marks a round the wolf passed (empty message) |
| Faction | `wolf_kill_decided {target, carrier, day}` — the carrier's choice, sent as it is made (no vote buffer: nothing is blind any more) |
| Seat | `input_request` (a human wolf's chat turn, `wolf_discuss`, may be passed; the carrier's `carrier_kill`; a skill turn `block_target` / `conceal`) |
| Observer | `night_action` for the carrier's kill (`role` = the carrier's own role) and for each skill · `strategy_update` |
- `current_round` (written by PREPARE_PACK_NIGHT), `wolves_target` (the carrier's kill, inside `wolf_kill_decided`) → IGNORED. START_CARRIER, COLLECT_PACK and the `PACK_NIGHT_PHASE` root wrapper → registered silent.

**NIGHT_RESOLUTION** (the barrier — fattest commit in the game: one delta, four audiences). The node resolves every choice once (Agents/rules/night.py) and commits the public outcome as `night_report`; the translator reads that report and recomputes nothing.

| Tier | Events |
| --- | --- |
| Public | `gm_message {day, seq, text}` — dawn narration verbatim: the deaths by attacker type, the saves, the dead town roles' records read out, the speculator's pick |
| Public | `night_result {day, deaths: [{player, role, attacker_types, concealed}], save?, saves[], pick?}` — the death atom (= the dead_roster delta): `role` is "" and `concealed` true when an illusionist hid it; `attacker_types` now includes `sigilist` and the reanimated kinds `reanimated_wolves`, `reanimated_vigilante`, `reanimated_sigilist` (an attack a necromancer made through a body, 2026-10-10; the stage shows each with the body kind's own attacker icon, no new icons, owner); every save in `saves` (`save` keeps the first); `pick` is the side a speculator picked tonight, never the seat; empty deaths = quiet night |
| Public | `roster_update {surviving_players}` — union only, as day_resolution |
| Faction | `pack_roster_update {surviving_wolves}` |
| Seat (every night actor) | `night_record {actor, action, target, result, outcome, seen}` — the seat's own record as the engine wrote it (the investigator's read, the sentinel's visitors, the sigil's outcome, the fortune teller's points); the pack's kill record goes to every living wolf with `actor: "wolves"`. A seat that died tonight gets none (it learned nothing from the night it died) |
| Seat (a role with a limit) | `uses_remaining {role, count}` — bullets, sigils, conceals, self-bets, the pick; to a holder alive at dawn |
- `investigation_result`, `vigilante_confirmation` and `bullets_remaining` are nine-seat events, kept in the schema for archived replays and no longer sent.
- Silent whiffs (an attack on an immune player: the serial killer, the necromancer on night 1, a self-betting fortune teller) send NOTHING publicly — absence is the design; the wire must not un-silence what the engine silences (see pacing denominator). A concealed death lowers no public role count: the audience cannot tell which unit it was.
- `day_summaries` append → IGNORED (verbatim inside this node's `gm_message`); `night_report`, `uses_left`, `speculator_pick`, `fortune_points`, `last_body` → folded into the events above.
- Metric append + langfuse span → diagnostic plane, never the wire.

**ONE_MORE_DAY** — `phase_change("day") {day}` (content-disambiguated, as day_resolution's night marker). `current_day` delta → IGNORED (inside it). Also commits the new-day RESETS — `night_choices` / `night_report` / `day_votes` / `voted_player` all cleared → IGNORED (blank-slate bookkeeping, zero information).

**END_GAME**

| Tier | Events |
| --- | --- |
| Public | `game_over {winner, neutral_result, day}` — thin: an entitlement flip, not a data package; `winner` is a side (`villagers`, `wolves`) or the lone killer's role (`serial_killer`, `necromancer`), None for a draw; `neutral_result` how the speculator or fortune teller fared beside it |
- At game_over the client's tier becomes observer; the server streams the withheld O-tier backlog from the durable log (full X-ray replay: wolf channel, probes, strategies, `roles_assigned`). No reveal payload is duplicated into the event.
- POST_GAME_ANALYSIS → registered silent with the key check off: its state output is large and never sent. In a memory-on game it streams one `custom` chunk from inside the node, observer `memory_extracted {observations[], strategy_points[], day}` — what the game taught, raw (a served game never writes the store, so there is no post-dedup form). Arrives after game_over, so every viewer is already an observer. Sent once per game (a re-run streams it again).

## Stream behaviours the translator guards

Four things about the engine's stream shape what the translator does, each handled at one
guard. The stories behind them are in `server_encountered_challenges.md`.

- **A committed step can stream again**, tagged `__metadata__: {cached: true}`, when a cached
  node re-runs after a human answers. Dropped whole: its events already went out. (§4)
- **Every interrupt streams twice**, once under the subgraph's namespace and once mirrored at
  the root. Only the root copy becomes an `input_request`. (§1)
- **The two votes re-run when a human answers.** The AI ballots streamed before the pause are
  provisional; the same voters stream again on resume. Ballots are buffered until the tally and
  the last write per voter wins, so the batch converges on the set the engine kept. (§2, §3)
- **A root wrapper's commit repeats its subgraph.** DAY_PHASE and the five night wrappers call
  their subgraph as a function and commit its result; the subgraph's own chunks already carried
  every field. The wrappers are registered silent so their keys are still checked.

## Ephemeral pacing channel (translator-derived, not node-anchored)

One snapshot event paces both waits: `phase_progress {stage: "night" | "day_vote", done, total}`.
Night: `phase_change("night")` starts the wait, denominator = padded alive-role census (below).
Day vote: START_VOTING starts it, denominator = surviving roster (public, unpadded).

- **Durable vs ephemeral split is structural**: separate event union with no `seq`, distinct SSE event name (`event: pacing` vs `event: game`), so the exporter *cannot* persist it and the game reducer never sees it. Replay doesn't wait — pacing has no place in the log.
- **Denominator from public knowledge only** (ruling 2026-10-11: the number of publicly alive players, one padded unit per living seat every night, from the roster, never the role census and never the real fan-out list). The role census (the earlier design: special roles not on the dead roster, pack = 1) leaked uses-left: a spent vigilante's missing slot + a public shot count < 2 ⇒ the vig shot someone immune ⇒ SK confirmed alive + vig disarmed; and it could not place a concealed body.
- Completion = the translator seeing the actor's delta key commit (no node writers → no interrupt re-fire problem). Padded non-actors (zero-bullet vig) get a fake completion after ~20–30s; anonymous ticks make padding indistinguishable.
- Snapshots, not increments (idempotent: duplicates from resume/reconnect are harmless; client applies monotonic-max). Fresh snapshot on SSE subscribe.
- This is the leak-free residue of the banned `night_progress`: the ban covers engine-state-derived progress; public-knowledge-derived pacing is exempt.

## Derived Votes

| Value | Current frontend derivation |
| --- | --- |
| Vote tally | Count received `vote_cast.votee` values |
| Who hasn't voted | NOT derivable live (anonymous `phase_progress` replaced `player_voted`); post-batch, `surviving_players − vote_cast voters` |
| Alive-role census | Initial public cast counts − publicly revealed deaths by role (`lynch_result` + `night_result`) |

## Derived (night)

| Value | Current frontend derivation |
| --- | --- |
| Night actor progress | ephemeral `phase_progress` snapshots only — never derivable from game events (by design) |
| Pacing denominator | alive-role census above (public knowledge) |
| Human wolf's view of the kill | `wolf_kill_decided {target, carrier}`, sent as the carrier names it |
| Full chat history | the client's own event log (`speech`/`gm_message` accumulate; `day_channel` is append-only server-side, but the client never re-fetches) |

---

## Completion notes (2026-07-31 — what was added, and three reconciliations)

Added by Claude from the ruled night derivation (`night_derivation_draft.md`, interactive session):
the seven night sections (fan-out edge → END_GAME), the Ephemeral pacing channel section, the
Derived (night) table, and `roles_assigned` in initialize_game (game_over unlock dependency).

Reconciliations where today's rulings met the existing day-side text — day precedent won twice:

1. **Rosters are sent** (`roster_update`/`pack_roster_update` at night_resolution). The draft's R6 note
   had survivor lists folding as derived state, but the day table already sends the translator
   union — and "send the client-facing form" says the day table is right. Fold doctrine still
   covers marker clears and `current_round`.
2. **`night_result` instead of a shared `player_died`.** R4 wanted one death event for both phases,
   but `lynch_result` already exists as the day death atom with vote free-riders that night deaths
   don't have. Two parallel death atoms (`lynch_result` / `night_result`), same shape philosophy:
   the dead_roster delta + what the node already computed. The alive-role census derives from both.
3. **`day_summaries` night append = IGNORED**, not a `day_summary` event. It's verbatim the same
   text as this node's `gm_message` (the `voted_player` precedent). Resolved 2026-09-15: the
   day_resolution append is IGNORED too. The registry handler never sent it, the goldens carry one
   `day_summary` per day, and the client renders a day's summary from the summarize node's event alone.

One correction to the original text: `vote_cast.vote_target` → `vote_cast.votee` in Derived Votes
(the field name ruled day-side).

Rulings that used to be dated inline in the tables above (2026-09-14: dates moved here, section
titles aligned to the translator's registry names, NIGHT_START fixture warning dropped since the
2026-08-19 capture includes it):

- 2026-08-05 — anonymous `phase_progress` replaces the durable `player_voted` indicator (vote node).
- 2026-08-06 — `day_summary` renders as the "Previously…" card atop day D+1 (SUMMARIZE_DAY_DISCUSSION).
- 2026-08-06 — ONE_MORE_DAY's new-day resets ruled IGNORED; hole found by the chunk-catalogue
  exhaustiveness check.
- 2026-08-08 — owner added the NIGHT_START anchor, superseding the translator's lazy
  first-night-chunk inference.
