# Stage architecture — how the Playhouse design becomes code

Ruled 2026-09-25. The visual redesign in [design_2026-09-25/HANDOFF.md](design_2026-09-25/HANDOFF.md)
is the *what*; this file is the *how*: the rulings that shape the code, the axes every scene renders
from, the stage's coordinate space, the asset rules, the module layout, the workbench, and what the
build replaces. The beat-by-beat truth is [beat_sheet.md](beat_sheet.md). Where this file and the
handoff disagree, this file wins (§9 lists every such point).

## 1. Rulings (owner, 2026-09-25)

1. **Workbench route, not Storybook.** `/workbench/[scene]` mounts the same scene components the
   replay and live pages mount, fed from the bundled fixture with a hand-written control strip
   (§7). Storybook is deferred; if it is ever added it is for leaf components only.
2. **`motion`** (framer-motion's successor) for choreography (§6).
3. **Landscape only** for the stage and for everything inside a game room (`/games/[id]`,
   `/replays/[id]`). The landing, the replay list and the lobby/rooms stay responsive. Amended
   2026-09-26 (review F1): the waiting room inside `/games/[id]` is a stage scene too, landscape
   only; its boarding pass (the name step) is the one upright page there; the lobby (`/rooms`)
   stays responsive. This
   supersedes `ux_baseline.md`'s "mobile-first, one column" for those two routes.
4. **A fixed 1600×900 logical stage** (§3): the one number everything scales from.
5. **The design bundle is split.** Curated: `docs/design_2026-09-25/` (handoff, kits, sprite
   manifest, landing handoff). Shipped: sprites as WebP under `src/assets/sprites/`. Archived,
   not in git: `frontend/claude_artifacts/` (the 54 MB benches with inlined sprites and the PNG
   masters; also on claude.ai, links in the handoff §10).
6. **The v1 theatre is replaced, not flagged.** Tag `theater-v1-baseline` before the first
   deletion; the structural-rewrite rule from the root `CLAUDE.md` applies (§10).

## 2. The axes — what a scene renders from

Five independent inputs; the scene is a pure function of them. No scene reads the store.

| Axis | Values | Set by |
|---|---|---|
| Source | live · replay | the route |
| Tier held | public · seat · faction · observer | the server (live); the X-ray toggle (replay: off = public, on = observer) |
| Me | none (spectator) · a seat (+ pack if wolf) | `GameStatus.you` + my `role_assigned`; never inferred |
| Cursor | a beat index (replay) · the tail behind a catch-up queue (live) | the transport / the stream |
| Presentation | slot (drawer · film) · motion (normal · fast · skip) · X-ray on/off | the user |

```
Scene({ view: fold(events ≤ cursor), beat, me, presentation })
```

`fold` is the existing [foldEvents.ts](../src/game/foldEvents.ts) and **never gates**: the tier is
whatever the log holds. There is no "AI viewer": the X-ray is a lens on observer tier, and an agent
has no client. After `game_over` every live viewer is an observer. The one thing the existing code
lacks is the **beat sheet** ([beat_sheet.md](beat_sheet.md), `src/stage/beats/`): the design's
beats are scene-level ("voting opens", "a chip is counted", "the truth"), finer than
`replayPlayer.ts`'s log-level cuts, and they differ by X-ray state.

## 3. The stage box — 1600×900 units

The stage is a `16 / 9` box. Every position, size, radius and path in every scene is written in
**units** of a 1600×900 space, and the box applies one CSS scale (`--stage-scale`, from a
`ResizeObserver` or container-query units) to fit its parent. Nothing is laid out in viewport px.

- Landscape-only makes the phone a smaller scale, not a relayout. Beat timings, sprite placement
  and the HUD geometry are viewport-independent by construction.
- **The bleed (ruled 2026-09-25).** A phone is ~19.5:9 and most laptops wider than 16:9, so a
  16:9 box alone leaves black bars at the sides. The world stays 1600×900 and nothing that
  matters is placed outside it, but the picture continues past its edges: the stage's outer box
  fills the viewport, the world sits centred in it, and each scene draws a fixed 300 units of
  **bleed** either side (`BLEED` in `units.ts`; a 21:9 screen shows 250, and the camera never
  pulls back past 1), clipped by the outer box (so nothing depends on the viewport's width
  and nothing redraws on resize). What bleeds: the room's paint (wall, floor, phase colour) at
  the sides where the room touches the world's edge; a HUD panel's own ground where the panel
  touches the edge (the wing on the left, the drawer or film on the right, the top strip's
  band). The bleed darkens towards the screen's edge, as a theatre does, so it reads as the
  house's dark rather than as more room. The light layer's glows may spill into it; figures,
  instruments and words never go there. Above 21:9 the bars return. Bars above and below on a
  4:3 tablet stay for now.
- **Legibility (ruled 2026-09-25, two tiers 09-26).** Phones are the main screen (scale ~0.43).
  `--legible` (`Stage.module.css`: 0.75 / scale, clamped 1–1.8) grows the words people read
  (`--said`, `--note`: ~17 css px); `--legible-ui` (the same, capped 1.3) grows `--meta`, headings
  and buttons (~9–10 px, ~22 px tall). Both are 1 at full size (pixel-identical there); neither
  touches the geometry, `--chip`, `--gap` or the painted props. Below scale 0.75 (the same point
  the type starts growing) the box has `data-small`: the drawer's head loses its title (seats and
  Show still wrap, so both toggles stay in reach); the ballot's chips stay on one row.
- The HUD geometry the benches compute with `StageKit.geometry(W, H, …)` is **frozen once** into
  constants (`src/stage/units.ts`: rail, puppet box, wing, side slot, top strip, for `hud: live |
  replay | none`). The port's first job is to evaluate it at 1600×900 and commit the numbers.
- Sprites are placed in units too; their source pixel size only affects sharpness (§4).
- Orientation: request fullscreen and `screen.orientation.lock("landscape")` where allowed
  (Android Chrome); where not (iOS Safari), a portrait interstitial ("turn your phone"). There is
  no portrait layout. The interstitial is the room's, not the stage's.

**Layers** inside the box, bottom to top (each a positioned `div` filling the box):

1. `paint` — the backdrop (dining car / shelf room / station; the phase paint; the window)
2. `floor` — apron, trap, lift
3. `figures` — puppets, plush, chips on strings, cards on strings
4. `stand` — the stand, plaque, footlights
5. `instruments` — table, jar, plates, verdict board, act marks, the shelf's objects
6. `light` — the pool, specials, glows, the "chosen" lighting
7. `hud` — top strip, wing, side slot (drawer or film), the dock

The HUD is inside the box (it is part of the 1600×900 geometry), so the drawer's width and the
wing's tiles scale with everything else. A modal overlay (the full card, the epilogue's sheet, the
portrait interstitial) sits above the box in normal page flow.

## 4. Assets

**The rule** (handoff §1): objects are sprites, surfaces are textures, the frame is vector, and
anything that shows state is drawn over the sprite in vector, never baked in.

### Rasters

- Format: **WebP with alpha**, converted from the PNG masters with `sharp` (already a Next
  dependency). Day figures (paletted flat colour): `nearLossless`. Plush, kits, wood: quality 85.
  Measured (2026-09-25, `scripts/convert-sprites.mjs`): 9.2 MB → 3.7 MB; plush and kits shrank
  5–7×, the paletted day figures only ~13% (2.5 MB is their floor; lossless and lossy both come
  out larger).
- Location and names, mirroring the bundle:
  ```
  src/assets/sprites/day/<character>/{base,talking,thinking,out,chip}.webp
  src/assets/sprites/plush/<character>.webp
  src/assets/sprites/kits/{healer,investigator,vigilante,serial_killer,wolf,villager,clock,lamp}.webp
  src/assets/sprites/wood/walnut.webp
  src/assets/sprites/station/{sky,floor,post,lamp,train,blind}.webp
  ```
  Characters: `cat hare owl badger cyclops threeEyes dragon onion whale polarBear shade`.
- Imported only from [src/assets/manifest.ts](../src/assets/manifest.ts) (the existing ruling:
  static imports through `next/image`, content-hashed URLs, inferred dimensions). The manifest
  exports typed handles — `SPRITES.day[character][state]`, `SPRITES.plush[character]`,
  `SPRITES.kits[name]`, `SPRITES.wood` — and `BODY: Record<Character, { top: number; body:
  number }>`, the head-to-toe measure the cast module scales from, transcribed from
  `docs/design_2026-09-25/sprites-manifest.json` into TypeScript (no JSON at runtime).
- `castForGame(gameId)` (from `kits/puppet-kit.js`) lives in `src/stage/cast/castForGame.ts`
  unchanged: `Character[]`, index 0 = `player_1`. It hashes the **full uuid** (the benches pass
  `9369a5c1-3c28-42ce-86a1-9d594dfa4804`; the 8-char prefix gives a different cast), and
  `CHARACTERS` keeps the kit's order because the shuffle depends on it.
- The bundle manifest's `plush_scale` per character is not yet in `manifest.ts`; add it when the
  shelf room is built (step 5).
- The station (the waiting room's platform, review 2026-09-26 §A5) has no masters in the bundle:
  its pictures exist only inlined in `claude_artifacts/design/pages/waiting-room.html`.
  `scripts/extract-station-sprites.mjs` pulls each out once, by the CSS rule that uses it, into
  the archive as a PNG master (`claude_artifacts/design/sprites/station/`), and
  `node scripts/convert-sprites.mjs station` makes the WebP (quality 85), exported as
  `SPRITES.station.*`. The mapping (2026-09-26): `.sky` → `sky` (2508×627, the painted country),
  `.floor .tile` → `floor` (768×768, the paving, and since 2026-09-27 the platform's edge too), `.post` → `post` (489×1024), `.lamp` → `lamp` (569×1008, the lantern),
  `.cars` → `train` (5990×700, the dining car between two carriages; its window geometry is
  `TRAIN_PX` in `paint/station.ts`), `.place .blind` → `blind` (512×732). Not extracted: `.ch` and
  `.fg` (the stage's own sprites replace them) and `.ledge` (a 512 px copy of `wood/walnut.webp`,
  mean difference 2.5/255; the 2026-09-27 mockup's `.beam` is the same wood). The canopy's felt
  `fringe` was dropped that day: the mockup's top became a walnut beam with a brass trim, and
  its edge the paving's stone under a drift of snow. 12.4 MB of PNG → 1.4 MB of WebP, the train 708 KB of it.
- Sharpness: the 600 px day cuts are right at 1× and slightly soft at 2× for the puppet at the
  stand. If the ~900 px cuts still exist in the chat, re-export them as the masters. **Never
  upscale.** No sprite atlases: HTTP/2 makes 44 small files cheap and an atlas adds tooling.
- Preload the game's nine characters (four states + chip) at the deal; `next/image` `priority`
  on the first scene's figures.
- Known defect: the shade's base cut has a baked "3"; regenerate.

### Vector

Two kinds, by whether they carry state:

- **Paint** — the dining car's panels, window, lantern, the shelf and brackets, the drape, the
  shutter's geometry, the station cloth. Pure functions of `(phase, units)`, no state, no
  children, no event handlers. **Ported as string generators** (the kits' style, typed) under
  `src/stage/paint/`, rendered by one memoised `<Paint html={…} />` per layer via
  `dangerouslySetInnerHTML`. Porting these to JSX buys nothing. Every `<filter>`, `<mask>`,
  `<linearGradient>` id is prefixed with `useId()` from the caller so two stages can share a page
  (the kits' `opts.id` rule).
- **Instruments** — stand and plaque, trap and lift, the clock (dial, hand, arc, counter),
  cards (back, small, full, the framed card), chips and their strings, wing tiles, the shutter's
  motion, the verdict board, act marks, sigils, the jar/table/plates, film rows, the drawer.
  **JSX components with props**, because they carry state, need keys, and animate in and out.
  `RoleKit.sigil()` and the act marks are tiny: `<Sigil role />`, `<ActMark kind />`.

Faction colour appears on a card only once it is face up (the handoff's card-back rule).

## 5. Fonts and tokens

The design's materials (`StageKit.vars()`: walnut, brass, felt, paper, the faction inks) become
CSS custom properties on the stage box, alongside the existing [tokens.css](../src/styles/tokens.css).
Fonts as the benches use them (`IM Fell English` on paper, the sans on dark), via `next/font`.
The stage does not use Mantine components; Mantine stays for the rooms, the landing and forms.
The site around the stage (Mantine chrome, the token bridge where the theatre's values win, the site's fonts, the `(site)` route group) is in [site_architecture.md](site_architecture.md).

## 6. Motion

`motion` (v12), one rule: **arrive still, play moving.**

- A scene rendered at rest passes `initial={false}` (and the beat's "settled" variant) so
  seeking, refresh and reconnect land instantly. Playing forward from beat N−1 to N animates the
  difference.
- Enter/exit (a chip dropping through the trap, a card drawn up out of frame) is
  `AnimatePresence`; sequencing within a beat is variants with `delay`.
- Durations come from the beat sheet's `hold`, not from the component. A `MotionScale` context
  multiplies them: normal ×1, fast ×0.5, skip → `MotionConfig transition={{ duration: 0 }}`.
- "Nothing moves to say chosen": selection is opacity/brightness, never transform.

**GPU rules (ruled 2026-09-25, from an A/B on the owner's Chrome; headless never shows these):**
- The world and the camera wrapper stay pinned to their own compositor layers
  (`will-change: transform` in `Stage.module.css`). Without it the count's push-in drops frames.
- A backdrop that fades out is a **picture**, never a live SVG: `PaintPicture` turns the
  generator's SVG into an image and fades the bitmap. A live filtered SVG fading on a GPU drops
  a whole black frame as Chrome gives it its own layer, and pinning that layer did not help.
- A lift's load fades by its position, not the clock (`lift-fade.ts`), so nothing hangs over
  the trap once the table has gone in; the load is its own layer while it moves.

**If a beat "looks glitched" again** (frames overlapping, a black flash for a few ms, a stutter
while the motion itself completes): it is almost certainly the compositor, not React. Check in
this order before touching the choreography.
1. Confirm zero DOM churn during the beat (React DevTools profiler, or a MutationObserver
   count). If nothing re-renders, stop looking at the code and look at layers.
2. Headless Chromium will not reproduce it, and CDP screencast frame sheets miss one-frame
   flashes. The only instrument is the owner's Chrome on a production build.
3. A/B by subtraction: `next build` copies with ONE thing removed each, on separate ports
   (3004+, never 3000), owner reports which port is clean. Two rounds found both causes above.
4. If nothing isolates, simplify in this order, stopping at the first that fixes it: pin the
   moving layers → rasterise the fading backdrop → drop the `mix-blend-mode` on the light layer
   for that beat → don't move the camera during the change → sequence the moves instead of
   overlapping them → cover the change with a shutter or a cut.
The vote's `table-down` (beat 3) and `dusk→night` (beat 14) on 2026-09-25 are the reference
cases; `PaintPicture`'s docstring in `Stage.tsx` tells the second one.

## 7. The workbench

`app/workbench/[scene]/page.tsx` (one route). It reads the URL, folds the bundled fixture
(`src/stage/fixtures/replay-9369a5c1.json`, the full `ReplayGame`; the beat goldens use the same
file), picks the beat, and renders the scene through exactly the component the real pages use.

```
/workbench/vote?beat=5&viewer=spect|seat:player_7|xray&motion=normal|fast|skip&slot=none|drawer|film&hud=live|replay|none&animate=0|1[&live=1][&frame=iphone14|iphone15max|pixel8|WxH]
```

`live=1` (written only when on) cuts the beats as a game in play would, for any viewer: the day's
`day.turn-thinking` beats appear between the turns.

`frame=iphone14|iphone15max|pixel8|WxH` (written only when set; `fill`, the default, fills the
window) draws the stage in a box of that phone's landscape size in CSS px (844×390, 932×430,
915×412, or e.g. `1000x500`), mounted `fit="contain"` as the real routes do, to judge phone scale
on a desktop; a phone's CSS px is ~0.7× a desktop's in the hand. The workbench's drawer is the
URL's `slot` (closed by default), never the real routes' ≤540 px-tall-window default.

- The control strip (viewer, beat stepper, motion, slot, X-ray, fixture, frame) writes the URL;
  the URL is the whole state, so any view can be named in text and reproduced.
- The registry (`src/stage/workbench/registry.ts`) lists each scene with the beats the sheet
  gives it, so the stepper's range and the caption ("A chip is counted · `vote_cast` seq 244 ·
  everyone") come from the same table as the real player.
- It ships (it is a portfolio page: the workshop); it never reads the store or the stream.
- **Playwright** (`frontend/e2e/`, `@playwright/test`) drives it headless: one screenshot per
  named URL, `toHaveScreenshot` for goldens once a scene settles. Screenshots are for the agent
  to see the screen without the owner; a comparison runs in the test and only a failing diff is
  looked at. Not a CI gate until the scenes stop moving.

## 8. Module layout

```
src/stage/
├── units.ts                 # 1600×900, the frozen HUD geometry, scale helpers
├── Stage.tsx                # the box, the layers, --stage-scale, the paint memo
├── paint/                   # string generators: diningCar, shelfRoom, station, window,
│                            #   shutter, drape, light — (phase, units) → svg string;
│                            #   bleed.ts: the room's two strips past the world's sides (§3);
│                            #   station.ts: the platform (stationBack/Front, stationPlan)
├── instruments/             # JSX: Stand, Plaque, Trap, Lift, Clock, WallClock, Shutter,
│                            #   Bleed (the bleed's paint, under a room's own),
│                            #   RoleCard, CardBack, SmallCard, Chip, String, WingTile, Wing,
│                            #   VerdictBoard, ActMark, Sigil, Jar, VoteTable, Plate, ...
├── cast/                    # Puppet, Plush, Kit (sprite + numeral overlay), castForGame
├── film/                    # Film (side slot), Note, Lessons, ReadCard, Brief, Ledger (epilogue)
├── drawer/                  # Transcript drawer: lines by kind, day tabs, seat chips, Show toggles
├── scenes/                  # StationScene (the waiting room; station.ts its rules) DealScene
│                            #   DayScene VoteScene LynchScene NightLobbyScene ShelfRoomScene
│                            #   PackScene MorningScene ReplayNightScene GameOverScene
├── beats/                   # beatsFor(events, {xray}) → SceneBeat[]; types; fixture goldens
├── containers/              # ReplayTheatre (transport, chapters, slot) · LiveTheatre (queue, dock,
│                            #   the platform and its hand-off to the deal)
└── workbench/               # registry, ControlStrip, fixture loader
app/workbench/[scene]/       # the route
e2e/                         # Playwright
```

The page side of the waiting room lives with its route: `app/games/[gameId]/_components/`
`useRoom.ts` (the status poll's room as `RoomInput`, Lock and Depart with the host key) and
`BoardingPass.tsx` (the name step, the one upright page). `components/LobbyCard.tsx` is gone
(2026-09-26); its `TerminalError` moved to `components/TerminalError.tsx`.

Scenes take `{ view, beat, me, presentation }` and nothing else (the platform also takes `room`,
the waiting room from the status poll: `RoomInput` in `scenes/types.ts`). Containers own the store, the
stream, the transport and the queue. `src/game/` (fold, store, types) is unchanged except where
the beat sheet needs a field the view lacks.

`ReplayTheatre` also has a preview mode, `mini: { from, to, autoplay, speed? }` (the landing's carriage, review
2026-09-26 §F7): `hud: 'none'` (no wing, and `TopStrip` draws nothing), no slot, no transport, no X-ray, no keys, no
hover pause; the same reducer plays `from`..`to` of the public cut round and round (`loop` in `replay-state.ts`, which
plays past a beat that waits) at `fast` by default, and a reduced-motion viewer gets it at rest. The frame is the caller's.

## 9. Where this build departs from the handoff

Verified against the server before ruling; the handoff's bundled schema is byte-identical to
`server/schemas/events.py`, so the wire assumptions hold.

| Handoff says | The build does | Why |
|---|---|---|
| "names or seat numbers: open" | seat numbers | the wire's seats are `player_1..player_9`; there are no names |
| the translator should buffer `wolf_vote` | nothing | it already does (`server/game/translate.py`, `_buffer_wolf_votes`) |
| "your turn": Say it, Pass | + **Draft from notes** (three per turn, the wait credited back) | `POST /games/{id}/draft` landed 2026-09-17 (ux_journeys D25) |
| `day_summary` "hidden from the live client until X-ray unlocks" | the live stage has no beat for it | it is public tier; the client never gates. Same picture, right words |
| the sprite canvas size: open | 1600×900 units, sprites placed in units | §3 |
| landing's miniature replay: same component reduced, or a cut-down build? | decided with the landing, after the theatre | the stage box scales; the question is what beats it plays, not what it is |
| mobile: "phone proportions left to the build" | there are none: landscape only, one scale | ruling 3 |

Deferred by decision, unchanged: `firing_reason` and `addressed_targets` in the film or drawer;
motion for the night rooms beyond the timings in the sheet; whether a seat can be reclaimed
(server's call).

## 10. What it replaces

Tag `theater-v1-baseline` at the last commit before the first deletion. Then, once the replay
container runs on the new scenes, delete: `components/Theater.module.css`, `theater-parts.tsx`,
`transcript-parts.tsx`, `DayTranscript.tsx`, `Transcript.module.css`, `Beats.tsx`,
`ReplayControls.tsx`, `TurnDock.tsx`, `game/replayPlayer.ts` and `resolutionBeat.ts` (their
beat-cutting logic is absorbed by `stage/beats/`), and the theatre halves of `TheaterClient.tsx`
and `GameClient.tsx`. `SeatChip`, `RoleIcon`, `ReplayCard`, `Lobby*`, the forms and the hooks stay.

Done 2026-09-25 (step 7): all deleted, with the v1 scrubber's `useFilterState`; `WinnerChip` now lives in `ReplayCard.tsx`.

## 11. Order of work

| # | Step | Who |
|---|---|---|
| 0 | this file · `beat_sheet.md` · bundle placement | main loop (done 2026-09-25) |
| 1 | assets: WebP conversion, `manifest.ts` + `BODY`, `castForGame` | Opus |
| 2 | stage foundation: `units.ts`, `Stage.tsx`, the paint generators ported, `motion` in | Opus (paint) · main loop (instrument contracts) |
| 3 | `beatsFor` + fixture goldens | main loop |
| 4 | workbench route + control strip + Playwright | Opus |
| 5 | scenes, one task each, in the handoff's order, each checked against its bench | Opus · main loop reviews |
| 6 | containers: replay (transport, chapters, slot) · live (queue, dock + draft, rooms, orientation) | main loop |
| 7 | tag, delete v1, landing after | Opus |
