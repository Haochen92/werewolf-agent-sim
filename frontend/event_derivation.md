# Orchestrator_Graph — event derivation (final)

**initialize_game**

| Tier | Events |
| --- | --- |
| Public | `game_started {seats, cast_role_counts}` |
| Faction | — |
| Seat | `role_assigned {role, pack? (wolves), bullets? (vigilante)}` ×9 |
| Observer | `roles_assigned {player: role}` — nobody receives it live; exists so the game_over backlog replay has survivor roles from minute zero |
- `phase_change("day")` — marker table (node identity). `human_player` = no event (session handshake).

**day_phase entry / SCHEDULE** — no-op anchors → IGNORED.

**route_speaker edge** — `turn_started {player, day}` via `get_stream_writer()` (edge emission — cannot double-fire on interrupt resume).

**discuss node**

| Tier | Events |
| --- | --- |
| Public | `speech {day, seq, player, message}` |
| Faction | — |
| Seat | `input_request` (interrupt source; human seat only) |
| Observer | `strategy_update` · `pass_marker {passed, gated, gated_candidate}` · `firing_reason` · `addressed_targets` — annotations join the speech via `about_seq` |
- One delta → speech **or** pass_marker (branch on `entry.passed`). `None` return = no events (turn_started is not a promise).

**SUMMARIZE_DAY_DISCUSSION**

| Tier | Events |
| --- | --- |
| Public | `day_summary {day, summary}` — shown next morning: client render rule, **no buffer** (buffers gate entitlement; render timing gates pacing). RULED 2026-08-06: renders as a "Previously…" recap card at the TOP of day D+1's page (mirrors the LLM payload: full current day + summaries of prior days); the full transcript stays readable per day — the summary is a header, never a replacement |
| Observer | `day_summary_structured {day, role_claims/accusations}` |

**START_VOTING** — public `phase_change` (self-disambiguating: anchored on the routed-to node).

**vote node**

| Tier | Events |
| --- | --- |
| Ephemeral | `phase_progress {stage: "day_vote", done, total}` — anonymous voting-progress snapshot (RE-RULED 2026-08-05: replaces the durable `player_voted {voter}` indicator; progress ticks are replay noise, and the pattern unifies with night pacing. Denominator = surviving roster, public, no padding needed. Loss accepted: no per-player "waiting on X" checkmarks — reversible additively.) |
| Seat | `input_request` (interrupt) |
| Observer | `strategy_update` |
- Ballots buffered server-side (entitlement deferral — wire is the boundary, not the render).

**COLLECT_VOTES** — public `vote_cast {voter, votee, day}` batch. Content from the translator buffer, timing from node identity (its own delta is empty). Buffer-empty-at-day-end alarm.

**day_resolution**

| Tier | Events |
| --- | --- |
| Public | `gm_message {day, seq, text}` — verbatim narration (record fidelity outranks derivability for authored text) |
| Public | `lynch_result {outcome: lynched\|tie\|abstain\|no_vote, player?, role?, vote_counts, no_lynch_streak, day}` — the death atom (= the dead_roster delta) + the free-rider fields the node already computed |
| Public | `roster_update {surviving_players}` — **union only**: translator merges the wolf-partitioned lists before the public tier |
| Faction | `pack_roster_update {surviving_wolves}` |
| Public | `day_summary` — this node also appends the vote-result to `day_summaries`; same key → same event |
- `phase_change("night")` **only if no winner** (the one content-disambiguated marker).
- `voted_player` delta → IGNORED (inside `lynch_result`).

**check_game_end_day edge (static night fan-out)** — router → IGNORED (no marker: `phase_change("night")` already anchored on day_resolution). The real actor list this router computes must **never** reach the wire — the pacing denominator comes from public knowledge only (see Ephemeral channel).

**healer_act · investigator_act · serial_killer_act · vigilante_act** — one pattern ×4 (structural clones)

| Tier | Events |
| --- | --- |
| Public | — silence is the spec: no per-role markers, no engine-state progress |
| Faction | — |
| Seat | `input_request` (interrupt; human seat only) — ⚠️ fires inside a parallel superstep; resume semantics gated on the spike cell |
| Observer | `night_action {actor, role, target, day}` · `strategy_update` |
- No seat ack for the target (ruled): the seat re-learns its act from dawn's `gm_message`; the live client echoes locally. Observer event is the only committed-target record.
- `None` return = no events (engine fallback), same as discuss.

**wolf subgraph** (PREPARE → DISCUSS loop → parallel VOTE → COLLECT)

| Tier | Events |
| --- | --- |
| Public | — |
| Faction | `wolf_message {wolf, message, day, round}` — sequential talk, ships live |
| Faction | `wolf_vote {wolf, votee, day}` — **buffered** until the tally |
| Faction | `wolf_kill_decided {target, day}` — the plurality tally + random tiebreak; flushes the vote buffer |
| Seat | `input_request` (human wolf talk/vote — interrupt nested inside the outer parallel superstep) |
| Observer | faction mirror + `strategy_update` |
- Vote buffer rationale: live shipping leaks packmate votes to the interrupted human wolf (LLM wolves vote blind → unfair edge); tally-only gives the human LESS than the LLM seat (next-night `_wolf_payload` carries past votes → parity violation). Buffered release = blind voting + wire/state parity, full per-vote breakdown at round end. Same pattern as the day ballot buffer; same buffer-empty-at-dawn alarm.
- `current_round` delta → IGNORED (loop control). prepare/fan_out/collect/check_night_end anchors → IGNORED.

**night_resolution** (the barrier — fattest commit in the game: one delta, four audiences)

| Tier | Events |
| --- | --- |
| Public | `gm_message {day, seq, text}` — dawn narration verbatim |
| Public | `night_result {day, deaths: [{player, role, attacker_types}], save?: {player, attacker_types}}` — the death atom (= the dead_roster delta) + the free-rider fields; empty deaths = quiet night |
| Public | `roster_update {surviving_players}` — union only, as day_resolution |
| Faction | `pack_roster_update {surviving_wolves}` · `wolf_message {wolf: "game_master", ...}` — the SK-whiff note: first server-authored *faction* narration |
| Seat (investigator) | `investigation_result {target, role, day}` |
| Seat (vigilante) | `vigilante_confirmation {target, day}` (immune-whiff SK confirmation) · `bullets_remaining {count}` |
- The investigator survival gate lives in the NODE (no delta committed → no event exists) — the translator needs zero logic for it; committed→shipped does the right thing automatically.
- Silent whiffs ship NOTHING publicly — absence is the design; the wire must not un-silence what the engine silences (see pacing denominator).
- `day_summaries` append → IGNORED (verbatim inside this node's `gm_message`; precedent: `voted_player` inside `lynch_result`).
- `*_player` marker clears → IGNORED (fold doctrine: ship the client-facing form, fold the internal form — committed→shipped governs INFORMATION, not raw keys).
- Metric append + langfuse span → diagnostic plane, never the wire.

**one_more_day** — `phase_change("day") {day}` (content-disambiguated, as day_resolution's night marker). `current_day` delta → IGNORED (inside it). Also commits the new-day RESETS — `healer_target` / `investigator_target` / `serial_killer_target` / `vigilante_target` / `wolves_kill_target` / `day_votes` / `voted_player` all cleared → IGNORED (blank-slate bookkeeping, zero information; hole found by the 2026-08-06 chunk-catalogue exhaustiveness check).

**END_GAME**

| Tier | Events |
| --- | --- |
| Public | `game_over {winner, day}` — thin: an entitlement flip, not a data package |
- At game_over the client's tier becomes observer; the server streams the withheld O-tier backlog from the durable log (full X-ray replay: wolf channel, probes, strategies, `roles_assigned`). No reveal payload is duplicated into the event.
- POST_GAME_ANALYSIS → IGNORED on the wire.

## Ephemeral pacing channel (translator-derived, not node-anchored)

One snapshot event paces both waits: `phase_progress {stage: "night" | "day_vote", done, total}`.
Night: `phase_change("night")` starts the wait, denominator = padded alive-role census (below).
Day vote: START_VOTING starts it, denominator = surviving roster (public, unpadded).

- **Durable vs ephemeral split is structural**: separate event union with no `seq`, distinct SSE event name (`event: pacing` vs `event: game`), so the exporter *cannot* persist it and the game reducer never sees it. Replay doesn't wait — pacing has no place in the log.
- **Denominator from public knowledge only** (special roles not on the dead roster; wolf pack = 1) — never the real fan-out list. A naive count leaks the silent SK-whiff: missing vigilante slot + public shot count < 2 ⇒ the vig shot someone immune ⇒ SK confirmed alive + vig disarmed. The UX layer must not break a silence the engine maintains.
- Completion = the translator seeing the actor's delta key commit (no node writers → no interrupt re-fire problem). Padded non-actors (zero-bullet vig) get a fake completion after ~20–30s; anonymous ticks make padding indistinguishable.
- Snapshots, not increments (idempotent: duplicates from resume/reconnect are harmless; client applies monotonic-max). Fresh snapshot on SSE subscribe.
- This is the leak-free residue of the banned `night_progress`: the ban covers engine-state-derived progress; public-knowledge-derived pacing is exempt.

## Derived Votes

| Value | Current frontend derivation |
| --- | --- |
| Vote tally | Count received `vote_cast.votee` values |
| Who hasn't voted | NOT derivable live since the 2026-08-05 re-ruling (anonymous `phase_progress` replaced `player_voted`); post-batch, `surviving_players − vote_cast voters` |
| Alive-role census | Initial public cast counts − publicly revealed deaths by role (`lynch_result` + `night_result`) |

## Derived (night)

| Value | Current frontend derivation |
| --- | --- |
| Night actor progress | ephemeral `phase_progress` snapshots only — never derivable from game events (by design) |
| Pacing denominator | alive-role census above (public knowledge) |
| Human wolf's kill-vote view | buffered `wolf_vote` batch + `wolf_kill_decided`, flushed together at the tally |
| Full chat history | the client's own event log (`speech`/`gm_message` accumulate; `day_channel` is append-only server-side, but the client never re-fetches) |

---

## Completion notes (2026-07-31 — what was added, and three reconciliations)

Added by Claude from the ruled night derivation (`night_derivation_draft.md`, interactive session):
the seven night sections (fan-out edge → END_GAME), the Ephemeral pacing channel section, the
Derived (night) table, and `roles_assigned` in initialize_game (game_over unlock dependency).

Reconciliations where today's rulings met the existing day-side text — day precedent won twice:

1. **Rosters ship** (`roster_update`/`pack_roster_update` at night_resolution). The draft's R6 note
   had survivor lists folding as derived state, but the day table already ships the translator
   union — and "ship the client-facing form" says the day table is right. Fold doctrine still
   covers marker clears and `current_round`.
2. **`night_result` instead of a shared `player_died`.** R4 wanted one death event for both phases,
   but `lynch_result` already exists as the day death atom with vote free-riders that night deaths
   don't have. Two parallel death atoms (`lynch_result` / `night_result`), same shape philosophy:
   the dead_roster delta + what the node already computed. The alive-role census derives from both.
3. **`day_summaries` night append = IGNORED**, not a `day_summary` event. It's verbatim the same
   text as this node's `gm_message` (the `voted_player` precedent). ⚠️ Review question for the
   owner: day_resolution's own `day_summary` row ("same key → same event") ships text that is also
   verbatim its `gm_message` — should it become IGNORED too, or is the summary-stream-completeness
   argument (client renders summaries only from `day_summary` events) the reason to keep both?

One correction to the original text: `vote_cast.vote_target` → `vote_cast.votee` in Derived Votes
(the field name ruled day-side).
