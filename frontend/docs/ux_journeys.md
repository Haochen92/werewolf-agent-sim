# UX journeys — the screen-by-screen derivation (v1)

> Status: **PROVISIONAL DEFAULTS — build on these (ruled 2026-08-21).** §0's ground rules
> are BINDING (one is store-architectural); D1–D24 are the working spec for the v1 build —
> the builder follows them instead of inventing, and the owner adjusts them against the
> RUNNING app (P1's replay theater is the ruling instrument), not on paper. Post-MVP this
> doc is updated to as-built + corrections and distilled into
> [`ux_baseline.md`](ux_baseline.md) (which stays the summary spec). Method: this is the UX twin of
> [`event_derivation.md`](event_derivation.md) — instead of tracing the graph to derive
> events, we trace the **user journeys** and derive screens. Completeness is checkable, not
> vibes: every route × `GameStatus.state`, all 27 durable event types (+ `phase_progress`),
> and all 8 `InputRequest.action_kind`s must appear in §8's render table. Decision points
> are numbered **D1…D24** for ruling by reference.

---

## 0. Ground rules (derived, not designed)

- **Visibility is the server's decision, not a UX decision.** Tiers already withhold
  (PUBLIC/FACTION/SEAT/OBSERVER); the client renders what arrives and never hides or fakes
  (ux_baseline §4). Every decision below is about *arrangement and prominence* of entitled
  data. A wolf's screen differs from a villager's only in which sections have content —
  never in bespoke layouts.
- **Two earned takeovers, no more.** Full-screen moments are reserved for the two dramatic
  beats the genre owns: the role reveal (D8) and the game-over banner (D20). Everything
  else — deaths included — lives in the transcript flow. (Overlay inflation is how game
  UIs get noisy.)
- **Beats fire on live arrival only.** During any catch-up fold (refresh, reconnect,
  replay scrub), events render instantly in their settled form — no takeovers, no
  animations, no notification sounds mid-fold. The reducer doesn't know the difference;
  the *store* flags live-arrived seqs vs folded history and the beat layer keys off that.
  This single rule is what makes refresh-mid-game safe (D22).
- **The viewer kinds** (the columns of every decision): seated-alive (by role), seated-dead,
  live spectator, replay viewer (X-ray off/on), lobby host, lobby joiner.

## 1. Journey A — visitor → landing → replay theater

The portfolio path; a recruiter with zero context must reach the X-ray in two clicks.

**D1 · Landing hierarchy.** Hero = the one-liner ("watch AIs deceive each other — and see
exactly why") + three door cards with **Watch a replay visually primary** (larger card,
amber accent; it needs zero keys and zero waiting). Quick game and Rooms as equal
secondary cards. Below: the latest ~6 replays as cards (the `/replays` list component
reused), each deep-linking straight into the theater. Footer: one line on what the
project is + repo link. No screenshots/marketing sections in v1 — the replay rail IS the
demo.

**D2 · Replay browser rows.** One responsive card component (not a desktop table + mobile
cards pair): winner chip (faction color), days, seats, n_humans badge, finished-ago.
Grid on desktop, stack on mobile. Rationale: one component, and replay rows are browsed
casually, not compared column-wise.

Theater UX itself is already ruled at the day-page grain (ux_baseline §3); the in-game
sections below (§4–§6) define the transcript anatomy it shares. Replay-only deltas:
scrubber visible always; X-ray toggle in the header always available; ghost-guess widget
at day boundaries (localStorage).

## 2. Journey B — solo player: `/play` → seated

**D3 · Solo form.** One centered card, three groups top-down: role picker (segmented
"Random" default + the cast list with role glyphs) · model select (from `GET /models`,
disabled state until a key is present where required; "house default" first) ·
`ByokField` (per build_plan P2 ruling). One primary button: "Take a seat." Below the
button, small print: key sent once, never stored; BYOK games don't survive restarts.
Submitting → redirect `/games/[id]`, which opens in `running` (solo games auto-start) —
the player's first screen is the role reveal (D8).

## 3. Journeys C & D — host and joiner: rooms

**D4 · Create form (`/rooms/new`).** Same card pattern as D3: room name (optional,
placeholder "Unnamed table") · optional model/BYOK (same `ByokField`) · "Open the room."
On success: stash `host_{gameId}`, redirect to the lobby.

**D5 · Rooms browser (`/rooms`).** List rows (not cards — a lobby list is scanned, and
rows scale to many rooms): name · seat count `players/max_seats` · created-ago · padlock
on locked rows (visible but join disabled — locked ≠ hidden, mirroring the server).
Tapping a row expands it inline to a name prompt + join button (no modal; mobile-first).
Join success → lobby as a seated joiner. Empty state: "no open tables — create one" +
door to `/rooms/new`.

**D6 · The lobby (`/games/[id]` · state=waiting).** One centered lobby card, driven by the
status poll:

```
┌──────────────────────────────────┐
│  Midnight Table         3/5 🔒?  │   ← name + seat dots + lock state
│  ────────────────────────────    │
│  share link  [copy]              │   ← host: prominent, top; joiner: present, smaller
│                                  │
│  ● haochen (host)                │   ← join order; "you" marked; host badged
│  ● wolfbait_22        ● you      │
│  ○ empty  ○ empty                │   ← capacity as empty dots
│                                  │
│  [ Start game ]   [🔒 lock]      │   ← host only; joiner sees "waiting for the host…"
└──────────────────────────────────┘
```

The share link is the host's primary action (an empty room is a dead room) — top slot,
one-tap copy. No lobby chat (no backend for it; don't fake affordances). Spectate is a
plain link under the card ("just watch"). Start transition: poll flips to `running` →
lobby card dissolves into the game screen; the room name is carried into the session
store at that moment (status blanks it once running).

**D7 · Multiplayer waiting variant.** Same card — a joiner's lobby differs only in what's
absent (start/lock controls). Locked room while inside: a padlock chip appears by the
name. Room-full: join door disabled at `len(players) == max_seats` (server 409 stays the
authority).

## 4. The game-start beat

**D8 · Role reveal — the first earned takeover.** On `role_assigned` (live-arrived only —
never on catch-up fold): full-screen dark takeover, one card center, face-down; tap or
auto-flip after a beat → role portrait (large — the asset set's moment), role name, one
line of ability text, faction-colored card edge. Role-conditional third line:
wolves — "your pack: Ralph, Meg" (from `pack`); vigilante — "2 bullets" (from `bullets`);
SK — "immune to night attacks; your kills are silent". One button: "Take your seat" →
the takeover settles into the table screen. Spectators/replay never see this beat (no
`role_assigned` at their tier / catch-up rule).

**D9 · The persistent role chip.** After dismissal the role lives as a compact chip pinned
in the dock corner (mobile) / roster rail header (desktop): mini portrait + role name.
Tapping re-opens the D8 card as a sheet (memory aid, not a takeover). This chip is also
where "you" is anchored visually — the answer to "which seat am I?" is always one glance
away.

## 5. The day loop (discussion → vote → dusk)

The screen skeleton is ruled (ux_baseline §2): roster strip/rail · transcript (one day
per page) · dock. The decisions below are the transcript's anatomy.

**D10 · Speech bubbles.** All speeches left-aligned in one column — a werewolf transcript
is a *table record*, not a DM thread; own-right alignment would break the table metaphor
and desync the replay view (which has no "own"). Your own messages are marked instead:
amber left-border + "you" on the speaker chip. Bubble = speaker chip (mini portrait +
name) above the text; consecutive speeches by the same speaker merge under one chip.

**D11 · GM narration (`gm_message`).** No bubble: centered, narrower measure, muted color,
small GM glyph — the "voice of the table". GM lines are the day page's structural
punctuation (dawn announcements, vote calls), so they must read as *between* the players,
never as a player.

**D12 · `turn_started` (live).** Renders as a transient "Ralph is thinking…" row with the
pacing pulse at the transcript tail; resolves into that player's speech bubble, or
vanishes on the next event (a pass — invisible live by tier, an X-ray row in replay).
Replay X-ray-off hides turn markers entirely.

**D13 · Day summary (`day_summary`).** Per the wire docstring it renders *next morning*:
a "Previous day" recap card at the top of each day page ≥2, GM-styled, collapsible —
**expanded live** (it's the morning briefing after a night away), **collapsed in replay**
(the reader just read the day). The O-tier `day_summary_structured` feeds the X-ray
inspector only (accusations/claims lists), never the story surface.

**D14 · Voting.** On `phase_change: voting`: a GM line calls the vote; the dock switches
to the vote form (D17). While ballots are out, `phase_progress (day_vote)` drives a thin
"votes are in: m of n" strip (no names — the schema is anonymous by design). `vote_cast`
events arrive as one batch (server buffers until the tally): render a single **vote
block** — ballots grouped per votee as chips ("Ralph ← Meg, Sam ×2"), then the
`lynch_result` line. No one-by-one ballot theater in v1 (that's replay-autoplay polish,
parked).

**D15 · The lynch beat.** `outcome=lynched`: a full-width **death banner** inside the
transcript flow (not an overlay): "{player} was lynched. They were **{role}**." + typed
glyph (lynch), vote-count grid, portrait desaturates everywhere at once. `tie`/`abstain`/
`no_vote`: a GM-styled quiet line ("the village couldn't decide — second day without a
lynch" — `no_lynch_streak` phrased in words, only when >1). The banner is the loudest
in-flow element; it must still not be a takeover (D-rule §0).

**D16 · Vote matrix (inspector).** Desktop inspector panel / mobile sheet, derived from
`vote_cast` history: voters × targets per day. Public data — available without X-ray, in
live and replay both (the "veteran's view", ux_baseline ruling).

## 6. Turn dock, timers, night

**D17 · The dock, by `action_kind`.** One `TurnDock` component, form per kind — this list
is closed (8 kinds) and each is one of two shapes:

- **Free text** (`discuss`, `wolf_discuss`): textarea + "Speak" + "Pass" secondary. The
  wolf variant is visually inside the wolf-channel tint (D19), not the public dock skin.
- **Target pick** (`vote`, `wolf_vote`, `healer_target`, `investigator_target`,
  `serial_killer_target`, `vigilante_target`): radio list of `candidates` (portrait +
  name per row) + confirm. The server's `candidates` list is the *only* source of legal
  targets — the client never derives eligibility (abstain/skip appear iff the server
  lists them; verify their representation at build time).

Always present when a turn pends: the countdown ring (D18) and the **delegate button**
("let my agent decide") as an explicit secondary action. 422 rejections render verbatim
inline in the dock; 409 clears the form and re-syncs (build_plan §5). Local echo: night
picks get an optimistic "You chose to protect Meg" machine-world row (the server sends
no seat ack by design; dawn's GM line is the authoritative confirmation).

**D18 · Timers and pacing.** The AFK countdown = a ring around the dock's submit button,
amber → red over the final 10s, fed by `deadline` (compute server-vs-local clock delta
from the status poll once, then tick locally). No timer in solo (`deadline=None`) — no
ring, think forever. Other seats' pending state: hourglass badge on their roster chips +
their deadlines as tooltips (from `GameStatus.deadlines`). `phase_progress` renders as a
thin strip under the roster strip (mobile) / an inspector block (desktop): night — "the
village stirs… m of n"; day_vote — "votes are in: m of n". Monotonic-max applied in the
store; the strip never moves backwards.

**D19 · Night, by viewer.** On `phase_change: night` the page shifts blue-black (token
ruling) and the transcript starts a night section:

- **Non-acting seat (or acting seat, done)**: a centered **night card** in the transcript
  area — "The village sleeps." + the `phase_progress` night strip. Nothing else; night
  is quiet by design, don't fill it.
- **Acting human seat**: the dock wakes with the target form (D17). Investigation results
  arrive as a SEAT-tier **machine-world card** inline ("Your investigation: Sam is a
  villager") — cold/monospace styling, because private knowledge is an instrument readout, not
  table talk. Same treatment for `vigilante_confirmation` ("your target was the serial
  killer") and `bullets_remaining`.
- **Wolf seat**: the night section contains the **wolf channel** — a crimson-tinted
  sub-transcript (story-world bubbles, faction tint; the GM's SK-whiff note renders as a
  GM line *inside* the tint, `wolf == "game_master"`). `wolf_discuss`/`wolf_vote` docks
  render inside the tint; `wolf_kill_decided` is a pack-only banner ("the pack has
  chosen: Sam"). `pack_roster_update` refreshes pack badges silently.
- **Spectator/replay X-ray-off**: the night card only. Replay X-ray-on: wolf channel +
  `night_action` rows + gated content interleaved, machine-world framed.

**D20 · Dawn.** `night_result` opens the new day page: per-death banner (same D15
anatomy, "found dead" flavor) with the **attacker-type glyph** (wolf/SK/vigilante —
`attacker_types` is public flavor; multiple attackers = stacked glyphs). `save` present →
a GM line ("someone was attacked in the night — and survived"). Empty deaths → "a quiet
night" GM line. Then D13's recap card, then the day's discussion begins.

## 7. Endings and edges

**D21 · Your own death.** A full-width "You have died" banner (in-flow, not a takeover) +
the dock permanently replaced by a slim ghost bar: "you're watching as a ghost". The view
continues exactly as before minus input — tiers keep serving what a dead seat is entitled
to; own historical private cards stay visible (they're yours). Own portrait desaturates
with a small ghost badge. No new information is revealed by dying (server-enforced;
the UI must not pretend otherwise).

**D22 · Game over — the second takeover.** On `game_over` (live-arrived): faction-colored
winner banner takeover ("The Wolves win") over the final table, one button: "See what
really happened." Meanwhile the R7 backlog streams in and re-folds; the button lands the
player in the same route, now the full theater: X-ray toggle available (one-time hint
badge on it: "see what everyone was really thinking"), scrubber unlocked, day 1 selected.
No re-route (build_plan: the live route morphs). If the viewer arrives *after* game over
(refresh, late link): no takeover (catch-up rule §0) — straight to the theater with a
winner chip in the header.

**D23 · Interruption states.**
- *Refresh mid-game*: skeleton → status poll → SSE replay from seq 0 → fold fast-forward
  under the catch-up rule (§0) → land on the newest day, dock restored if a turn pends
  (`pending_input` + a fresh `input_request` in the log). Cost: seconds, zero drama.
- *Reconnect*: browser-native SSE retry, silent; thin "reconnecting…" bar only after
  repeated `onerror` while the tab is visible (ux_baseline §4).
- *Dead game* (`GameStatus.error` set, state still "running"): full-width terminal error
  state over the table — the session's death report (key-redacted server-side), a "these
  games don't survive restarts" note when BYOK, one door: home. No retry affordance (the
  server holds no way back — don't fake one).
- *Seat loss* (403 on a turn POST): inline rejoin flow — the stashed localStorage token
  auto-retries `POST /rejoin` once; on success the turn re-submits; on failure: "your
  seat can be reclaimed on the device you joined from" (cross-device rejoin is v1-out).
- *Room 409/410 paths* (full, locked, started): inline row/lobby states with plain words,
  each offering the spectate link as the consolation door.

**D24 · Live spectator.** The running view minus dock, role chip, and private tiers —
plus a "watching live" chip and the same vote matrix/inspector (public data). No ghost
guesses in live v1 (replay-only widget per baseline; live guesses would want lockable
timing = a later slice). Spectator link is offered at the lobby (D6) and on room rows.

## 8. The completeness table — every wire item → its render

| # | event (tier) | live render | replay (X-ray off → on) |
|---|---|---|---|
| 1 | `game_started` (P) | seats the table, roster + census | same |
| 2 | `role_assigned` (S) | **D8 takeover** + D9 chip | — (tier) |
| 3 | `roles_assigned` (O) | — until R7 | off: — · on: role badges everywhere |
| 4 | `phase_change` (P) | section breaks + night tint (D19) | same, drives scrubber steps |
| 5 | `game_over` (P) | **D22 takeover** → theater | winner chip in header |
| 6 | `turn_started` (P) | thinking row (D12) | off: hidden · on: turn markers |
| 7 | `speech` (P) | bubble (D10) | same |
| 8 | `pass_marker` (O) | — until R7 | off: — · on: pass/gated rows, `gated_candidate` expandable |
| 9 | `firing_reason` (O) | — | on: inspector, per-speech "why it fired" |
| 10 | `addressed_targets` (O) | — | on: inspector tags per speech |
| 11 | `strategy_update` (O) | — | on: inspector strategy timeline |
| 12 | `input_request` (S) | dock form (D17) + ring (D18) | — (tier) |
| 13 | `day_summary` (P) | next-morning recap, expanded (D13) | collapsed recap |
| 14 | `day_summary_structured` (O) | — | on: inspector claim/accusation lists |
| 15 | `vote_cast` (P) | vote block batch (D14) + matrix (D16) | same |
| 16 | `gm_message` (P) | GM line (D11) | same |
| 17 | `lynch_result` (P) | death banner / quiet line (D15) | same |
| 18 | `roster_update` (P) | alive states reconcile | same |
| 19 | `pack_roster_update` (F) | pack badges refresh (D19) | on: visible |
| 20 | `night_action` (O) | — (local echo instead, D17) | on: night rows |
| 21 | `wolf_message` (F) | wolf channel bubble (D19) | on: interleaved, tinted |
| 22 | `wolf_vote` (F) | wolf vote block (D19) | on: same |
| 23 | `wolf_kill_decided` (F) | pack banner (D19) | on: same |
| 24 | `night_result` (P) | dawn banners / quiet line (D20) | same |
| 25 | `investigation_result` (S) | machine-world card (D19) | on: in inspector |
| 26 | `vigilante_confirmation` (S) | machine-world card (D19) | on: in inspector |
| 27 | `bullets_remaining` (S) | count on role chip + card (D19) | on: in inspector |
| — | `phase_progress` (ephemeral) | pacing strips (D18) | absent by construction |

`action_kind` coverage: all 8 in D17 (two shapes). `GameStatus.state` coverage: waiting =
D6/D7 · running = §4–§7 · finished = D22. Orthogonal `error` = D23.

## 9. Component-inventory delta (extends ux_baseline §5 once ruled)

New components this trace surfaces: `RoleRevealCard` (D8) + `RoleChip` (D9) ·
`GmLine` (D11) · `ThinkingRow` (D12) · `RecapCard` (D13) · `DeathBanner` (D15/D20) ·
`NightCard` (D19) · `WolfChannelSection` (D19) · `PrivateResultCard` (D19) ·
`PhaseProgressStrip` (D18) · `CountdownRing` (D18) · `GhostBar` (D21) ·
`WinnerTakeover` (D22) · `TerminalErrorState` (D23). All presentational, fed `GameView`
slices; the beat layer (live-vs-fold flag) lives in the store, not in components.
