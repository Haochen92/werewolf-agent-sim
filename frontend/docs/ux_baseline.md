# Frontend UX baseline — v1 (the build spec for the first version)

> Ruled 2026-08-20. This is the UX/visual companion to [`build_plan.md`](build_plan.md)
> (architecture/stack/phasing) — together they are the complete handoff for implementation.
> Idea source: [`design_log.md`](design_log.md) §3/§7 (aesthetics) and §2/§6/§8 (UX); wire
> contract: [`server_client_transport.md`](server_client_transport.md). Everything in §6
> (the parking lot) is OUT of v1 — do not build affordances for it.
> Screen-by-screen grain: [`ux_journeys.md`](ux_journeys.md) — the journey-trace
> derivation (D1–D24). Ruled 2026-08-21: its §0 is binding, D1–D24 are provisional
> build-on-these defaults, adjusted against the running app post-MVP (not pre-ruled
> on paper); as-built outcomes distill back here.

---

## 1. Aesthetic ruling: hi-bit pixel × séance noir (ruled 2026-08-21)

The design log holds two art directions — §3 "séance noir" tarot-card portraits and §7
hi-bit pixel art (Coffee Talk formula). **v1 takes the fusion §7 itself anticipated:
hi-bit pixel is the MEDIUM, séance noir is the MOOD** — "pixel tavern + amber pooled
light"; large moody-lit pixel portraits in the Coffee Talk / VA-11 Hall-A register,
dark-mystery palette, never bright-retro. (Supersedes the 2026-08-20 "neither picked"
deferral; §3's tarot-card framing is dropped.)

Hard rules (from §7, non-negotiable — this is a reading app):

- Portraits big and detailed; sprite-scale minimalism would hurt a dialogue game.
- ALL dialogue + UI text stays on the clean sans stack; pixel display type for
  titles/chrome ONLY (the contrast collapses if pixel type leaks into body text).

The v1 asset set (generated; ONE palette, ONE canvas ratio — consistency is enforced at
generation time, not in code; structure + manifest rule = `build_plan.md` §3): ~12 seat
portraits · 4 kill glyphs (wolf / SK / vigilante / lynch) · optional table backdrop
(day + night variants). **The build never blocks on art**: the manifest's
initials-`Avatar` fallback ships in P0, portraits land whenever ready with zero
component edits — asset generation is its own timeboxed pass, not a P0 dependency.

What the tokens bake in (unchanged by the pixel ruling — pixels change assets, not
tokens; the two-world contrast is the visual thesis of the whole project):

- **Story world (table, transcript, lobby)**: Mantine dark scheme tuned warm — deep
  ink/charcoal surfaces (not Mantine's default blue-gray), one amber accent (`--amber`)
  for interactive/highlight, generous line-height (this is a reading app).
- **Machine world (X-ray panes, vote matrix, scheduler detail)**: deliberate contrast —
  monospace type, thin borders, cold cyan accent (`--xray-cyan`) on darker ground.
  Flipping into an agent's mind must FEEL like switching instruments.
- **Day/night shift**: night-phase transcript sections and the table header shift to a
  blue-black tint (CSS class on the phase wrapper, driven by the fold's `phase`). Cheap,
  werewolf-native, and the single most atmospheric thing tokens can do.
- **Typography**: clean sans (Mantine default stack) for ALL dialogue and UI — both art
  directions agree readability rules; the display face for page titles/chrome is the
  pixel face per the §1 ruling (GM narration stays clean sans — it is body text).
  Monospace reserved exclusively for machine-world panes (the contrast collapses if
  monospace leaks into story chrome).
- **Deaths**: dead players desaturate + dim (CSS filter on the portrait/name chip);
  death notices carry the attacker type (wolf / SK / vigilante / lynch — the data is
  attacker-typed) as a small typed glyph + distinct accent, not just gray text.
- **Portraits**: pixel portraits from the asset manifest, per-seat deterministic pick
  (`PORTRAITS[hash(seat) % len]`); until the set lands, the fallback is Mantine `Avatar`
  with initials on a per-seat deterministic hue (same hash). Role icon overlay (tabler)
  where the viewer is entitled to see the role, in either mode.

## 2. Layout system

**Mobile-first, one column** (werewolf reading is phone-shaped — design log §8):
roster strip (horizontal scroll of seat chips) pinned atop → transcript scroll →
action dock pinned at bottom (live seat only). X-ray content opens as a bottom sheet.
**Desktop (`visibleFrom="md"`)**: three regions — roster rail left (seat cards,
vertical), transcript center (max-width reading column), inspector panel right (X-ray /
vote tally / game info). Same components, re-flowed; no desktop-only features.

## 3. Page-by-page UX (v1)

### Landing `/`
Three doors as large cards: **Watch a replay** (primary — it's the portfolio
centerpiece and needs zero keys) · **Quick game** (`/play`) · **Multiplayer rooms**
(`/rooms`). Below: the latest ~6 replays (reuses the `/replays` list component). One
paragraph of what this is ("watch AIs deceive each other — and see exactly why").

### Replay browser `/replays`
Table/card list from `GET /replays`: finished-at, days, winner chip (faction-colored),
cast summary, n_humans badge. Pagination via `useFilterState` (`?offset=`). 503 →
"archive not configured" empty-state.

### Replay theater `/replays/[gameId]` — the centerpiece
- **Scrubber**: day/phase stepper (Day 1 · Night 1 · Day 2 …) URL-addressed
  (`?day=&seq=`); prev/next buttons + a compact timeline bar. v1 is step-through, NOT
  autoplay (autoplay + staged pacing is a polish item, §6).
- **Transcript paginated by day** (owner-ruled chat-box UI): one day per view — GM
  narration, speeches as chat bubbles (speaker chip + text), vote section (ballots as
  chips on the accused, then the lynch result), night section (blue-black tint, public
  deaths at dawn). The reducer already keys transcript by day; the page renders one key.
- **X-ray toggle**: a single prominent switch in the header ("X-ray"). ON adds, in
  place: role badges on every seat chip · pass markers incl. the novelty-gated vetoed
  speeches (collapsed "gated" rows that expand to show what the agent WOULD have said —
  the differentiator, make it discoverable) · wolf-channel entries interleaved in their
  night section (visually machine-world) · night actions. Clicking any seat (X-ray on)
  opens the **agent inspector** (sheet/panel, machine-world styling): role, strategy
  timeline (`strategy_update`s in order), firing reasons for its speeches, its night
  actions, addressed-targets list.
- **Vote matrix**: a per-day grid (voters × targets) in the inspector panel region,
  derived from `vote_cast` — the veteran's view; X-ray not required (votes are public).
- **Ghost guesses (localStorage)**: at each day boundary a compact "who do you suspect?"
  widget — pick seats, locks on advance, reveal at game end vs the truth. Skippable,
  never blocking.

### Solo door `/play`
One form card: role picker (optional, from the cast list, "random" default) · model
select (from `GET /models`, disabled until a key is entered; empty = house default) ·
`ByokField` (key input, opt-in "remember on this device", masked + clear when loaded —
`build_plan.md` §5) · start button → redirect to `/games/[id]`. Copy states plainly:
key is sent once, never stored server-side, BYOK games do not survive server restarts.

### Rooms `/rooms` and `/rooms/new`
Browser: rows from `GET /rooms` — name (fallback "Unnamed table"), roster count
(`players/max_seats`), created-ago, lock state (locked rows render with a padlock,
join disabled). Join = name prompt → `POST /join` → `/games/[id]`. Create page: room
name + optional model/BYOK (same `ByokField`) → stash `host_{gameId}` → redirect to
the room, showing the share link prominently.

### Game `/games/[gameId]` — one route, three states (`GameStatus.state`)
- **waiting**: lobby card — room name, roster with join order, share-link copy button,
  "waiting for host" vs (host) start button + lock toggle. Status poll drives it.
  Carry the room name into the session store at start (status blanks it once running).
- **running**: the live table = the SAME transcript/roster components as the theater,
  fed by the SSE store, pinned to the newest day. Additions: typing indicators from the
  `pacing` channel (seat chip pulses + "…" row) · **turn dock** when `me.pending` — the
  form by `action_kind` (textarea for discuss/wolf_discuss with pass button where
  `can_pass`; radio/select of `candidates` for votes and night actions), the AFK
  countdown ring from `deadline`, and an explicit "let my agent decide" delegate
  button · wolf players additionally see the wolf channel (own tinted section) ·
  private results (investigations, bullets) as machine-world cards inline · 422
  messages render verbatim in the dock; 409 clears the form and re-syncs · dead-game
  detection (status poll `error`) → full-width error state.
- **finished**: game-over banner (winner, faction-colored) → the R7 flush re-folds and
  the view becomes exactly the replay theater with X-ray unlocked ("the SK was WHO?"
  moment). One "reveal" transition, no re-route.

## 4. Interaction rules (cross-page)

- Every load-bearing async region gets a skeleton (dota2pred convention); errors are
  Mantine notifications for transient (turn rejected, reconnect) and inline states for
  terminal (dead game, 503 archive).
- SSE reconnect is silent (browser-native); show a thin "reconnecting…" bar only after
  repeated `onerror` while visible.
- No token streaming anywhere; messages appear whole after a typing indicator
  (transport §9 — the backend decides this).
- Spectators get the same running view minus dock/private tiers; nothing is gated
  client-side (the server withholds — never hide data that arrived, never fake data
  that didn't).

## 5. Component inventory (v1)

`SeatChip/SeatCard` (alive/dead/typing/role-badge variants) · `Transcript` +
`DayView` (GM/speech/vote/night sections) · `SpeechBubble` · `VoteBlock` + `VoteMatrix`
· `XrayToggle` · `AgentInspector` (sheet/panel) · `GatedPassRow` · `TurnDock` (form per
action_kind + countdown + delegate) · `PacingIndicator` · `DayScrubber` · `GhostGuess`
widget · `ByokField` · `RoomRow`/`LobbyCard` · `WinnerBanner` · `ReplayCard`. All
presentational components take folded `GameView` slices as typed props (no fetching).

## 6. Future / parked (do NOT build in v1)

**Needs backend that doesn't exist yet** (each is its own future slice):
ghost-guess persistence + beat-the-ghost scoring · daily puzzle (curation/publish/share
grid) · MVP score + autopsy screen · accounts/OAuth/stats/personal board · memory
showcase modes (live memory-ON, store changelog explorer, deep memory X-ray from
eval-case exports — gated on the memory-research posture) · kick-player · raised-hand
proactive speaking · coach mode · achievements · guess-the-human mode.

**Pure frontend, deliberately later** (styling/polish pass): replay autoplay with staged
pacing + speed control · dramatic-irony meter · mention graph · vote-chip slide /
kill-cinematic micro-animations · PWA manifest · "play of the game" deep links ·
the §7 green-phosphor-CRT variant of the machine-world (v1 keeps cold cyan). The
theme-slice structure is where all of this lands without touching app code.
(The art-direction pick is no longer parked — RULED in §1, 2026-08-21; the generated
asset set is a scheduled timeboxed pass that can land any time after P0.)
