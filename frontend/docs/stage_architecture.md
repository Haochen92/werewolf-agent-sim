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
| Presentation | slot (drawer · film, the tabs Transcript · File) · motion (normal · fast) · X-ray on/off | the user |

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
  the sides where the room touches the world's edge; a painted room (the dining car, the night
  compartments) cannot carry on past its picture, so its last 28 units sink to 0.6 of the
  house's dark and past its edge the dark starts at 0.82, full by 90 units out (`PaintedBleed`
  in `instruments/Bleed.tsx`; ruled 2026-09-29, replacing the mirrored strip); a HUD panel's own ground where the panel
  touches the edge (the wing on the left, the drawer or film on the right, the top strip's
  band). The bleed darkens towards the screen's edge, as a theatre does, so it reads as the
  house's dark rather than as more room. The light layer's glows may spill into it; figures,
  instruments and words never go there. Above 21:9 the bars return. Bars above and below on a
  4:3 tablet stay for now.
- **Legibility (ruled 2026-09-25, two tiers 09-26).** Phones are the main screen (scale ~0.43).
  `--legible` (`Stage.module.css`: 0.75 / scale, clamped 1–1.8) grows the words people read
  (`--said`, `--note`: ~17 css px; `--said` is 23.5 units × `--legible`, 17.6 css px on an
  iPhone 14, ruled 2026-09-29); `--legible-ui` (the same, capped 1.3) grows `--meta`, headings
  and buttons (~9–10 px, ~22 px tall). Both are 1 at full size (pixel-identical there); neither
  touches the geometry, `--chip`, `--gap` or the painted props. Below scale 0.75 (the same point
  the type starts growing) the box has `data-small`: the drawer's head loses its title (seats and
  Show still wrap, so both toggles stay in reach); the ballot's chips stay on one row.
- The HUD geometry the benches compute with `StageKit.geometry(W, H, …)` is **frozen once** into
  constants (`src/stage/units.ts`: rail, puppet box, wing, side slot, top strip, for `hud: live |
  replay | none`). The port's first job is to evaluate it at 1600×900 and commit the numbers.
  Since HUD pass 2 (2026-09-29) `units.ts` evaluates the kit's formula once at load with the
  wing at `WING_N` = 192 units (the seat rail's two columns, 12%) in place of the kit's 5.5% (88).
- Sprites are placed in units too; their source pixel size only affects sharpness (§4).
- Orientation: request fullscreen and `screen.orientation.lock("landscape")` where allowed
  (Android Chrome); where not (iOS Safari), a portrait interstitial ("turn your phone"). There is
  no portrait layout. The interstitial is the room's, not the stage's.

**Layers** inside the box, bottom to top (each a positioned `div` filling the box):

1. `paint` — the backdrop (the dining car's and the night rooms' paintings / station; the felt country in the glass; the shutter)
2. `haze` — the atmosphere's back half: the key light on the wall, the pelmet's shadow, the veil
3. `floor` — the trap (its hole, and its leaves while they move), lift
4. `figures` — puppets, the night rooms' photos on their line, chips on strings, cards on strings
5. `stand` — the stand, plaque, footlights
6. `instruments` — table, jar, plates, verdict board, act marks, the night room's card
7. `light` — the pool, specials, glows, the "chosen" lighting
8. `grade` — the atmosphere's front half: the key light's falloff, the vignette, the grain
9. `hud` — top strip, wing, side slot (drawer or film), the dock

The HUD is inside the box (it is part of the 1600×900 geometry), so the drawer's width and the
wing's tiles scale with everything else.

**The HUD's look (ruled 2026-09-29, pass 1 of 3).** The HUD is furniture of the painted car, not
a glass overlay: deep walnut boards (`--walnut-top`/`--walnut-bot`, the walnut texture as a still
grain under the stain) with a thin brass edge (`--hud-brass`, a dark reveal and a fainter inner
line), the words in lamp-glow cream (`--cream`, `--cream2`), brass the accent for "speaking" (the wing's lit tile). Two voices (§5): Young Serif for what is engraved
or announced, Literata for what is said and read. The pieces: the **day plaque** (a sun or moon
disc, "Day 3" large, the phase beneath; `TopStrip`), the **pane tabs** (File and Transcript as
two tabs of one plaque split by a thin brass rule, the labels muted brass, File greyed without the
X-ray; since 2026-09-29 they only choose the pane, the X-ray being the replay band's one switch;
the pressed tab, File or Transcript alike, sits in a darker engraved walnut well, its label bright cream over a short
brass underline), the **speech box** (a fixed board of three lines with a nameplate tab, paged; beat
sheet §0, §11), and the **stand plate** (the seat engraved on brass, "No. 2", on the stand's
rail; on a phone, where the box rises past the rail, it rises to sit just above the box). In the
replay a **way-out plaque** ("← Replays", or "← Home" from the landing) stands before the day
plaque in the same material, and the count pill joins their row (beat sheet §11). A modal overlay (the full card, the epilogue's sheet, the
portrait interstitial) sits above the box in normal page flow. `grade` and `hud` sit outside the
camera's box: a push-in moves the room under the grade, as under a lens.

**The seat rail (ruled 2026-09-29, pass 2 of 3; beat sheet §0).** The wing is a cork board (a
still 192 px tile, `scripts/make-cork.mjs`, dimmed and darker towards the frame) in a walnut frame
with a brass edge on the room's side, the seats tacked to it (a brass tack, a contact shadow) as
photo cards (the night room's print stock:
`Photo.tsx`'s cream border and grey ground, the head through `ChipSprite`), laid out by
`railLayout(n)` (`instruments/rail-layout.ts`, unit-tested for 5–14 seats): two columns (three
past six rows), rows filling the height, the suspect slot in the spare cell or a strip. Width:
`WING_N` (192) inside the world on every screen, so the geometry stays frozen; the stage writes
`--spare` (how much bleed a `contain` box shows left of the world, in units, from its
`ResizeObserver`), and the rail reaches `min(--spare, target − 144)` past the world's left edge,
where `target` is 310 for two columns (456 for three). On an iPhone 14 (scale 0.433, spare ~174
units) the rail is 310 units, ~134 css px, 51 of them in the letterbox; on a 16:9 desk it is the
192 (12% of the width; the kit's wing was 5.5%). What is left of the bleed past the rail darkens to
the house's dark. A card is flex and a size container: the photo fills its width, up to 1.2× as tall and at most
60% of the card (`min(120cqw, 60cqh)`), the numeral on its corner. The foot holds faint ruled
lines where the seated player may write and their note on them (whole lines,
`round(down, 100%, 1lh)`, at `max(0.9 × --meta, 11px / --stage-scale)`, so never under 11 css
px); under the stage's `data-small` (a phone) the words give way to a pencil scribble. Then a band (the
role's ink, the X-ray's faction, "You" in amber) and the suspect's wax seal. The note editor is a
dialog over a scrim (`z-index` 40–41 in the HUD layer), a walnut board with a ruled paper area;
its presses keep a phone's 44 css px tap area (`--grown`). The notebook is `notebook.ts`: one
store per game id over `localStorage` (`lib/storage.ts` `seatNotes`, every access guarded), read
by every rail through `useSyncExternalStore`; `Presentation.game` is set only by the live
container (and the workbench's live cuts), so a replay's cards are never editable. GPU: the lit
ring is a pseudo-element whose opacity fades; the dead photo's `grayscale` is a static filter on
a small image; nothing moves.

**The transcript (ruled 2026-09-29, pass 3a; beat sheet §11 "The drawer's look").** The drawer is
a page, not a list of cards: a warm dark ground (`--ground-top`/`--ground-bot` on `.drawer`) with
the HUD's brass edge, the chapters as Young Serif headings (the day large; the night in a cool
pale blue-grey, `--night-ink`, never the serial killer's lavender), speeches as a small head, a
brass-cream name and Literata words, the game master's reports as short sentences with the dead in
terracotta (`--dead`), a run of passes as one italic line, and the vote as a tally of the voters'
faces per seat voted for. X-ray lines keep the film's aqua. `drawer-lines.ts` still decides what a
viewer holds; the telling is its pure helpers (`groupPasses`, `voteTally`, `voteSentence`,
`reportParts`), unit-tested beside it. The seat filter, Show and the day tabs are the strip's
plaque tabs (walnut, brass edge, the pressed well). One column at every width. Static: no filter,
no blur, nothing animates but the scroll.

**Atmosphere (2026-09-27, the polish pass's first step).** One warm key light from the upper left
(the puppets' own), carried over the whole room so the painted props and the flat vector pieces
sit in one lit, filmed set. `Atmosphere.tsx`, one per scene (the car's and the rooms'; the
platform has none), fills two layers:
- `haze` (over the paint, under everything that stands in front of it): the key light's warm lift
  on the upper-left wall (`KEY` in `paint/atmosphere.ts`: day 1, dusk and dawn 0.8, night 0.3,
  so the night stays lamp-led); in the car, `carHaze`: the soft shadow the shutter's pelmet
  throws down-right onto the wall (the painted frame and lamps carry their own painted shadows),
  then a warm dark veil over the whole back (0.15 at the ceiling to 0.07 at the floor) that sets
  the painted wall, window and lamps back behind the stand, the table and the figures, left open
  round each lit lamp (the lantern and the two table lamps, dusk and night); in the night rooms (`compartment`) a lighter plain veil
  and no key light (the painted candle leads: `roomLight`, beat sheet §6).
- `grade` (over the light, under the HUD, outside the camera): the key light's falloff (0 to
  0.14 towards the lower right), a vignette on the puppet's room (0 to 0.18 at the corners) and a
  still film grain (`SPRITES.grain`, a 160 px noise tile at 1.5 units a grain, 0.16).
- Contact and cast shadows, all down-right: each puppet throws a baked silhouette on the
  wall (`cast/CastShadow.tsx`; `SPRITES.shadow`, 46 WebPs; a puppet's falls 0.09 × 0.05 of its
  height at 0.5; the night rooms' photos a soft box shadow, since the plush dolls' went with them
  on 2026-09-28), a chip on its string a soft disc, the
  lynch's card a soft box. No shadow lies on the window's glass (a view through glass
  takes none): where the shutter is open behind them, the puppets' and the chips' shadows move in
  a still box clipped to everything but the glass (`offGlass` in `cast/CastShadow.tsx`), in step
  with their figure; the stand throws a soft pool off its right side; on the vote's table,
  soft gradient ellipses under the table (the lift shadow, retuned), the jar (tipped with it),
  each plate and each tower of chips.
- GPU (§6): nothing moves or fades; normal alpha only, no blend mode and no CSS filter. The one
  SVG blur is `carHaze`'s, static. Baked shadows ride inside their
  figure's box, so they rise and fall with it and nothing is blurred live. The pass adds five
  static composited layers (the grade and the haze, promoted for overlapping the window's idle
  animations) and no extra churn while a beat plays (measured 2026-09-27).
- Ruled 2026-09-27: kept, and unconditional (the workbench's `light=off` compare switch is gone).

## 4. Assets

**The rule** (handoff §1): objects are sprites, surfaces are textures, the frame is vector, and
anything that shows state is drawn over the sprite in vector, never baked in.

### Rasters

- Format: **WebP with alpha**, converted from the PNG masters with `sharp` (already a Next
  dependency). Plush, kits, wood: quality 85. Measured (2026-09-25,
  `scripts/convert-sprites.mjs`): 9.2 MB → 3.7 MB; plush and kits shrank 5–7×. The cast (the day
  figures and their heads) has its own recipe since 2026-09-28 ("The cast", below).
- Location and names, mirroring the bundle:
  ```
  src/assets/sprites/day/<character>/{base,talking,thinking,out,head}.webp
  src/assets/sprites/kits/{healer,investigator,vigilante,serial_killer,wolf,villager,clock,lamp}.webp
  src/assets/sprites/wood/walnut.webp               (the station's beam and ledge only)
  src/assets/sprites/textures/{walnut,boards,velvet,cork}.webp  (cork: scripts/make-cork.mjs)
  src/assets/sprites/station/{sky,floor,post,lamp,train,blind}.webp
  src/assets/sprites/window/{day,dusk,night,dawn}-{far,near}.webp
  src/assets/sprites/props/{jar-glass,jar-lid,stand-front,vote-table}.webp
  src/assets/sprites/car/{day,night}.webp
  src/assets/sprites/rooms/{healer,investigator,vigilante,serial_killer,wolf}.webp
  src/assets/sprites/shadow/day/<character>/{base,talking,thinking,out}.webp
  src/assets/sprites/atmosphere/grain.webp
  ```
  Characters: `cat hare owl badger cyclops threeEyes dragon onion whale polarBear shade`.
- Imported only from [src/assets/manifest.ts](../src/assets/manifest.ts) (the existing ruling:
  static imports through `next/image`, content-hashed URLs, inferred dimensions). The manifest
  exports typed handles — `SPRITES.day[character][state]`, `SPRITES.car[hour]`, `SPRITES.rooms[room]`,
  `SPRITES.kits[name]`, `SPRITES.wood`, `SPRITES.textures[name]` — and `BODY: Record<Character, { top: number; body:
  number }>`, the head-to-toe measure the cast module scales from, and `HEAD_FRAME`, how each head
  portrait sits in a round window (both measured from the cast, "The cast" below; no JSON at runtime).
- `castForGame(gameId)` (from `kits/puppet-kit.js`) lives in `src/stage/cast/castForGame.ts`
  unchanged: `Character[]`, index 0 = `player_1`. It hashes the **full uuid** (the benches pass
  `9369a5c1-3c28-42ce-86a1-9d594dfa4804`; the 8-char prefix gives a different cast), and
  `CHARACTERS` keeps the kit's order because the shuffle depends on it.
- The plush dolls (and their shadows and `PLUSH_SCALE`) are gone since 2026-09-28: the night
  rooms hang photographs instead ("The night rooms", below); `convert-sprites.mjs` skips their
  masters. Of the kits only the wolves' is still drawn (the replay night's rail, `RailInstrument`).
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
- The dining car's window (ruled 2026-09-27): the country behind the glass is painted felt, a
  pair per hour, `SPRITES.window[hour].{far,near}`, drawn by `instruments/FeltWindow.tsx` over the
  car's paint, inside the glass: `far` (sky, peaks, hills) stands still and covers the glass;
  `near` (pines, fence, pole, with alpha) fills the bottom 52% and loops left one tile width,
  crossfading with the car at an hour change. The glass is the car painting's cleared window
  (`diningCarPlan().glass`); it holds the hour's flat sky colour until the felt loads. Masters: `claude_artifacts/design/rasters/window-<hour>-{far,near}.png`
  (1536×1024, gitignored). Recipe (ImageMagick, quality 82): `far` crop `1536x576+0+280`; `near`
  first shifted down to register with day's (night 27 px, dusk 10 px: `-background none -gravity
  north -splice 0xN +gravity`), then crop `1536x520+0+440`; night's `near` also `-modulate 65,55`
  so the row is the darkest thing outside.
- The painted props (ruled 2026-09-27, the polish pass): the jar's glass and lid, the stand's front
  and the vote's table are the owner's rasters, `SPRITES.props.{jarGlass,jarLid,stand,voteTable}`,
  replacing their vector bodies (plates, cards, chips, strings, footlights and plaque stay vector).
  Masters: `claude_artifacts/design/rasters/{jar-glass,jar-lid,stand-front,vote-table}.png`.
  Recipe (ImageMagick): crop to the alpha>3% box plus a margin, `-background black -alpha
  background` (zeroes the masters' garbage RGB under alpha 0; the lossy WebP puts don't-care RGB
  back near edges, which the browser's premultiplied alpha discards), `-quality 85 -define
  webp:alpha-quality=100 -define webp:method=6`. Crops: glass `988x1446+18+46`, lid
  `1154x827+50+216`, stand `1510x387+13+347`, table `1536x295+0+352`.
  - **Jar** (`Jar.tsx`, `jarGeometry`): the glass is an SVG `<image>` over its chips, so they take
    its mist; its box is the vector jar's height with the picture's own width (w/h 0.68). Lines
    measured on the picture, as fractions of h above the foot: mouth 0.968 (`yR`), lip's foot
    0.907, neck's foot 0.824 (`yN`), inner floor 0.15 (`floor`, where the pile lies). The lid's
    skirt is as wide as the lip, its foot on the lip's foot; the string ties round the ring.
  - **Stand** (`Stand.module.css`, replaced 2026-09-27): a walnut Pullman sideboard front, a brass
    gallery on its rounded rail, marquetry only in a border band and corner fans, a flame-figured
    panel. Master `stand-front.png` (the first one, a baize front, is kept as
    `stand-front-classroom.png`). Crop `1525x429+6+310`. Drawn with `border-image` as a 9-slice,
    insets 176 210 129 210 px (top right bottom left): the gallery, the rail, the fans and the inlay
    squares nearest them, and the bottom rail keep their painted size; the flame panel, the plain
    band and the stiles stretch (to any `widen` too). The box is ~2.5:1 and the picture 3.6:1, so the
    middle rows stretch 2.6× (3.4× under the replay's HUD): the side bands' inlay stringing between
    the corner slices (crop px 54–68 and 1456–1470, rows 176–298) was made one colour per column at
    conversion (`\( +clone -crop 15x123+54+176 +repage -scale 15x1! -scale 15x123! \) -geometry
    +54+176 -composite`, and at +1456) so it stretches without showing it; the middle square of
    each strip went with it. A pixel is 0.407682 puppet units (605 over the body's 1484 px, the
    stiles' outer edges); the rail's top (px 339) is on the box's top, so the gallery stands ~9
    units above the rail, over the puppet's waist. Darkened at conversion (`-channel RGB -evaluate
    multiply 0.55`, re-judged for this picture and kept): its panel averages a little below the
    car's wall and the puppet stays the brightest thing. 75 KB.
  - **Table** (`VoteTable.tsx` `TablePicture`): two strips of one picture meeting at the top's
    front line (px 88): the top (back line px 9, front corners x 21 and 1518.5) stretched to the
    vote's `depth`, so plates and jar stand where they did; the cloth and legs scaled so 138 px is
    `drop`, so the place cards hang on the cloth. The master's legs reached below the lift's cut;
    they were shortened at conversion to squat turned feet: below row 596 the wood is cleared
    (`-channel A -fx "j>=628||(j>=596&&(lightness<0.45||max(max(r,g),b)-min(min(r,g),b)>0.3))?0:u"`)
    and the legs' lower bulb and foot (rows 662–719) laid under it at row 581.
- The dining car (ruled 2026-09-29): the car is a painting, `SPRITES.car.{day,night}`
  (`instruments/CarBackdrop.tsx`), replacing the kit's vector walls, window frame, floor and
  trapdoor, and the painted wall clock and wall lamp of 2026-09-27 (the owner ruled the clock
  out; the lantern and two table lamps are painted in). Masters:
  `claude_artifacts/design/rasters/car-{day,night}.png`, 1600×900 RGBA, already fitted to the
  stage: `scripts/fit-car.mjs` scales a ChatGPT painting so its glass lands on the kit's glass at
  HUD `none` (x 401–1199, y 113–409, corner radius 28, cleared to transparent) and squashes the
  plain panelling under the window so its floor strip lands on the rail (y ≈ 590–640, where the
  trap is); `scripts/relight-car.mjs` makes the night from the day (dark and warm, pools kept on
  the lamps), so every panel lines up through the fade. Converted as the rooms are (`sharp`,
  quality 85, alpha quality 100, effort 6): 117 KB by day, 54 KB by night.
  - **Placement** (`CAR_PICTURE`, `carOffset` in `paint/dining-car.ts`): the painting moves as
    the drawn car did, across with the puppet's centre line (`cx − 800`: +44 under the live
    wing, left with the open side slot, its right end under the slot) and up with the rail
    (`railY − 639`: 27 up in the replay's frame, where its own last 27 rows are laid again under
    its foot so the floor reaches the frame's edge). The felt window takes the painted glass,
    moved the same way. The shutter keeps the kit's window: its pelmet sits on the painted blind's
    housing, its panel covers the glass and most of the brass.
  - **Hours**: day and dawn show the day picture, dusk the day picture under a flat warm dark
    (`CAR_TINT`, `rgba(78,24,4,.2)`, normal alpha: the kit's `#c0703a` multiply at 0.24 matched on
    the walnut, since a fading backdrop carries no blend mode), night the night picture, with no
    tint over it. An hour's change fades the old picture off over the new (opacity only).
  - **Light**: the kit's plan still says where the light falls; the lantern's special and glow sit
    on the painted lantern (1485,175) and each table lamp (45,400 and 1555,400) glows as the
    lantern does, lit at dusk and night; the car draws no halo, pool or visible cone of its own
    (the night picture has its pools painted in). `carHaze` casts only the drawn pelmet's shadow.
    Over the painting the house is lighter than over the old drawn walls (2026-09-29: the room
    reads as lit, the speaker keeps a gentle pool): `light`'s dark, before → after, is day 50 → 24;
    deal 30/58/40 → 14/40/26 (day begins / your card / dealt); vote 50 → 30; lynch 58/72/74 →
    36/52/54 (standing / named or drop / night); morning 30/58 → 14/38 (day begins / report);
    night lobby 66 → 46; game over 62/40/55/34 → 44/24/38/18; replay night 62/66 → 42/46
    (actor / whole). The painted lamps (lit in both pictures) are always the brightest, warmest
    things in the room: `diningCarPlan().lamps` (lantern r 120, table lamps r 150, strength 1, on
    the painting's lamps in every layout) go to `light`'s `lamps`, each cut as an unblurred
    radial hole (clear to 0.4 of its radius, soft to its rim) and warmed by a screened
    `rgba(255,179,92,.2)` radial over the world and the bleed, in every car scene.
  - **Floor**: the painting is the floor. The stand's dark gathers from nothing at the rail; a shut
    trap at rest draws nothing; an opening or shutting trap draws the hole, the standing leaves
    and flat leaves cut from the painting itself at the car's hour (an SVG pattern of the picture),
    so they fold out of the painted floor and lie back into it.
  - **The bleed**: `PaintedBleed` (below, "The night rooms").
  - Kit fidelity: `paint.test.ts` holds the car's plan (window, floor, slots, glows, specials) and
    the light over it to the kit's `scene()` and `light()`, the kit swapped as documented there:
    the wall clock removed, the lantern placed on the painted lantern, the table lamps' glows
    added. The kit's drawing is no longer compared: nothing draws it.
- The room's surfaces (2026-09-27): the flat vector walls, floor and valance are filled with
  seamless textures, `SPRITES.textures.{walnut,boards,velvet}`, as SVG patterns
  (`paint/texture.ts`). The shapes stay the paint's vector (they move with the side slot, the
  bleed and the hours; since 2026-09-29 the car is a painting and none of this is drawn on it,
  see "The dining car" above); the texture only fills them, anchored to the world's units, so it runs on
  unbroken into the bleed. Each tile is tinted at conversion so its average is the flat colour it
  replaces: the room keeps its value and hue, and each hour's `ROOMLIGHT` tint (a multiply inside
  the car's SVG) still falls on it. A darker flat of the same wood is the tile under a black veil
  (`DARKER`: 0.22 for `#3a2212`, 0.41 for `#2c1a0e`). Masters:
  `claude_artifacts/design/rasters/texture-{wall-walnut,floor-boards,valance-velvet}.png` (1254²,
  seamless). Every resize is `-virtual-pixel tile -distort Resize` so the tile stays seamless.
  - **Walnut** (`walnut.webp`, 640², 53 KB, 400 units a repeat): resized, each channel multiplied
    to the car's wall `#4a2c18` (R 0.7897, G 0.8913, B 0.9436), then its contrast about that
    average raised 1.7× (`\( +clone -scale 1x1! -scale 640x640! \) -compose Mathematics -define
    compose:args=0,-0.7,1.7,0 -composite`) so the grain still reads under the car's veils;
    quality 85. Used on: the car's back wall (a veneer window per panel between the panel lines,
    five different ones before the pattern repeats, `veneer`), its dado (grain across, veiled to
    `#3a2212`), the shelf room's panels (veiled to `#3a2212`), cornice and the shelf's face
    (grain along the board: the new walnut replaced the old `wood/walnut.webp` tile there), the
    shutter's stiles, louvres (veiled), slats (the walnut under their highlight at 0.6) and
    pelmet, and the bleed's strips of the car and the shelf room (the shelf room was replaced by
    the painted night rooms on 2026-09-28). The panel lines, dado, brass rail and mouldings stay
    vector on top.
  - **Boards** (`boards.webp`, 512², 64 KB): the master's eight planks were first rolled so a seam
    sits on row 0 (`-roll +0-91`) and evened out to 157 px each (each plank cropped between its
    seams, rows 0 158 318 478 641 796 959 1125 1254, resized to 0 157 314 470 627 784 941 1097
    1254 and appended), so the seams fall on a regular beat and can be laid on the drawn ones;
    then resized and multiplied to `BOARD` `#5a3f26` (R 1.2441, G 1.4580, B 1.4971). Laid at a
    plank's width per eighth of the tile, stretched to twice its width along the grain (`boards`):
    the car's floor strip and its trap (29 units a plank, a seam on the drawn one), the apron (45,
    on its drawn seams), the trap's two leaves and the lift's slab (half the leaf each), the
    shelf room's floor (36), and the bleed's.
  - **Velvet** (`velvet.webp`, 512², 12 KB, 400 units a repeat): the master's red channel only,
    as light and shade, times the valance's `#4a1418` (`-channel R -separate -evaluate multiply
    1.1102`, then `-compose multiply` with `rgb(148,40,48)`), so it has the valance's colour
    exactly and its folds and pile. It was the replay's valance and its bleed; since 2026-09-29
    nothing uses it: the valance is one walnut board with a brass hem, vector only (`drape.ts`,
    the owner's ruling that the velvet and the dark scalloped border in front read as two
    layers).
  - **The method: the pattern is inside the paint's SVG**, not a DOM layer under it, so the
    paint's own tints and glows reach it. The paints take the textures' URLs (`walnut`, `velvet`
    options; without them they draw the kit's flat colours). The fading car's SVG was once made
    a picture with its textures inlined (`PaintPicture`, 2026-09-27); the car is a painting now
    and fades as the image it is, so that is gone.
- The atmosphere's pictures (2026-09-27, §3 "Atmosphere"), made from the shipped WebPs, not
  masters. Shadows, per day figure and state: `convert <sprite> -alpha extract
  -resize x128 -bordercolor black -border 12 -blur 0x3 -background '#0c0704' -alpha shape
  -quality 80 -define webp:alpha-quality=70 -define webp:method=6` (`CastShadow` reads the 128
  and the 12). Grain: a 160 px `+noise Gaussian` tile on gray50 (`-seed 7`), each pixel white or
  black by its side of the middle, alpha its distance from it (×0.5 white, ×0.9 black, so it
  does not grey the dark), lossless.
- **The cast** (2026-09-28): the owner's costumed 1920s-train cast replaced the bundle's figures,
  same eleven characters, ids and poses. Masters: `claude_artifacts/design/rasters/cast/<id>/
  {base,talking,thinking,out,head}.png` (poses 1024×1536, heads 1254×1254; `shade` is the red
  songbird). Converted with Pillow (premultiplied Lanczos, WebP quality 82, method 6):
  - Cleaning: the masters' body alpha is 253, not opaque, so alpha is scaled by 255/253; alpha
    under 3 (a faint dark fringe) is cleared and RGB under alpha 0 zeroed. No halo shows on dark,
    so no threshold or contraction beyond that.
  - Registration: a few poses had drifted off their base in the masters (up to 32 px and 6% in
    scale: cat talking and thinking, badger talking, hare thinking, owl all three, the polar bear
    talking and thinking). Each was fitted to its base by the alpha overlap below the crown (a
    scale about the base's feet, then a shift) before cropping, so switching states never jumps.
  - One canvas per character, shared by its four poses: the union of their alpha boxes (the
    thinking bubble included), 6 px of air at the top, the feet on the bottom edge, and
    symmetric about the face's centre line (read by eye off the base), so the puppet box centres
    the face and the numeral sits on it. Scaled so the body (crown to toe) is **1000 px**: the
    puppet's body is ~629 units, so that is ~1.6 device px a unit, 2× on a ~1440-wide laptop
    (scale ~0.85) and more than a phone's (scale ~0.43 at 3×) needs. Canvases 826–923 wide,
    1103–1303 tall. 44 poses, 6.2 MB (the bundle's 600 px set was 2.5 MB).
  - `BODY` is measured on the base: `top` is the crown of the skull under any hat (ears, the
    hare's ear, the onion's curl, the three-eyes' antenna and the bubble rise above), the feet
    the canvas's foot. Being on the shared canvas, it serves all four states. The thinking pose's
    bubble raises the canvas top, so `puppetBox`'s HEADROOM/SINK rule sinks (and, the tall
    ones, shrinks) every state alike: alone at the stand (live) all but the polar bear sink the
    full 100 units and the body stands 556–629 units (the hare's ear and the cat's high bubble
    make them the smallest); two or three at the stand barely sink and never shrink.
  - `REACH` (per character, from the widest pose: how far it reaches either side of the centre
    line, in body heights) spaces two or three at the stand (`standSet`): neighbours' reaches
    just meet, the box widens to 1/0.92 of the row, and if that would pass the room (40 units of
    air a side) all shrink together. The replay's night keeps the pack's wolf kit its own place
    on the rail right of the pair (`aside`).
  - The numeral is a fifth of the body's height on the canvas's centre line (it was 24% of the
    image's width, which a wide pose would set).
  - Heads: the head portrait at **384 px** (29 KB each, 321 KB), sharp at 2× for the wing's tile
    and the place cards and ~1.6× for the morning's featured chip, the largest (~240 units). It
    replaced the chip cropped from the base (`chip.webp`, gone). `ChipSprite` (HTML: sized from
    the parent's height, so a tall wing tile shows the circle's framing cut at the sides) and
    `headRect` (the SVG chips: hung, ballot, place card) draw it through `HEAD_FRAME`: the
    portrait at `s` times the window's diameter, moved `x`, `y` diameters, judged by eye at 44 px
    so every face reads at one size. `s / 2 + y ≥ 0.5` keeps the portrait's cut collar out of
    the circle. The hare is tighter and lower (its upright ear runs off), the polar bear smaller
    (its ears stay in), the onion's curl and the three-eyes' antenna run off the top.
  - `scripts/convert-sprites.mjs` skips the old `day` masters so it can never overwrite the cast.
- **The night rooms** (2026-09-28, owner-approved): the acting seat's room and the pack's are the
  owner's paintings of a walnut-and-brass sleeping compartment, the role's props painted in,
  replacing the vector shelf room, the kits on its shelf and the plush dolls. Masters:
  `claude_artifacts/design/rasters/rooms/{healer,invest,vigilante,serial_killer,wolf}.png`
  (1536×1024, all to one plan: `refs/compartment-night.png`). `SPRITES.rooms[room]`, by the acting
  seat's role (the request's kind when the role is unknown); the wolves' room is the pack's.
  Plan and light: `paint/compartment.ts` (`ROOMS` holds every measure below, in master px).
  - **Glass.** The vigilante's master has real alpha in its glass, kept. The other four have a
    grey/white checkerboard painted in; converted with Pillow + scipy (a one-off script, not in the
    repo): the glass's rounded rectangle is fitted to the checker (pale and neutral: min ≥ 180,
    spread ≤ 10), grown 1.5 px into the brass's dark rim and feathered over 1.5 px; the objects
    painted over it (the window's latch, the candles' flames, the healer's flowers, the
    investigator's lamp shade, the wolves' red chimney) are what is not checker inside it
    (opened, pieces over 60 px), carried out to the rim, plus anything they cut off from the
    glass's open middle (a flame's pale core); their edge pulled in 1 px (2 on the chimney) and
    softened; the checker's last pale pixels in the rim cleared too. The chimney's glass showed
    the checker through it: smoothed away (a normalised Gaussian, σ 4, the flame kept). Glass
    rects (x0–x1 × y0–y1, corner r, master px): healer 893–1340 × 253–529 r44; investigator
    892–1339 × 251–528 r48; vigilante 875–1306 × 240–511 r46; serial killer 881–1331 × 241–514 r49;
    wolves 891–1340 × 249–528 r49.
  - **Crop.** Each 3:2 master is cut to the band 1536×915 from y 40 (the rack's rails to the
    floor's gold border and past it) and shipped whole across: WebP quality 82, alpha 100,
    method 6, 88–140 KB each (570 KB the five). On the stage the picture is 1512 units wide (the
    room right of the live wing, 0.984 units a pixel), right-aligned to the world, so its 915 px
    are 900.7 units and fill the height. With the side slot open it slides left, same scale,
    until its glass ends at x 985 (the slot opens at 978): the window stays in view (its frame's
    right edge under the slot), the photo line shortens to the part clear of the wing, the card
    stays on the table left of the slot; on desktop the room's band below the rail runs on
    under the drawer into the dark.
  - **The bleed** (ruled 2026-09-29; the car's too). A painting cannot carry on past its edges,
    and a mirrored stretch showed its props twice (the healer's stethoscope at the right edge on a
    wide phone), so its sides sink into the house's dark instead (`PaintedBleed` in
    `instruments/Bleed.tsx`): its last 28 units darken to 0.6 of `#0c0a07` at the edge, and past
    the edge the dark starts at 0.82 and is full 90 units out, on to the bleed's end (and past the
    picture's right end when it has slid left). Plain gradients, nothing mirrored or moving. On
    the left the wing's own ground covers it (live and replay). The car's (`outside`) sinks only
    past the world's sides, so its table lamps are never dimmed inside the 16:9 frame; a picture
    edge at or inside the world's side meets the 0.82 dark there.
  - **Behind the glass**: `FeltWindow` with the glass rect (grown 3 units under the frame), the
    night's far and near felt (the near row looping, the snow; transform-only, still for reduced
    motion), no blind's pull; the wolves' glass takes a red tint (`rgba(150,24,16,.28)`) so the
    night outside sits in their lamp's light.
  - **The candle and the card** (master px): candle flame healer 1248,522 · investigator
    1233,518 · vigilante 1220,512 · serial killer 1369,468 (violet) · wolves 1265,522 (the red
    lamp); the card's centre and foot on the table's clear spot left of it: 1075,628 · 1005,622 ·
    1000,604 · 1010,625 · 1040,630. The card is 200 units tall (its type scaled from bench 70's
    279), a contact shadow under it. The light's colour: amber, the killer's violet
    (`226,170,255`), the wolves' red (`255,76,52`).
  - **The photo line**, one for all five rooms (they agree): twine tied to the rack's lowest rail
    at master x 280 and 835, y 128 (units 364–910 at y 87; its left end runs a little over the
    hangings on the left walls), sagging 34 units. The photos keep to the part in view (clear of
    the wing by 16, 10 in from each tie). Up to four: one row, each in its own stretch, up to 140
    units wide (3 candidates: 140; 4: 118), while that keeps them at least 104. Otherwise k
    heights (2, or 3 when 2 would fall under 104 with six or more): neighbours overlap across
    the heights, prints at one height k pitches apart with 8 units between, each height a print
    and 24 units below the last, up to 130 wide (5–6: 130, 7: 126, 8: 111, ~48 css px on an
    iPhone 14, the lowest foot at y ~430). With the side slot open the line keeps x 104–478:
    3: 112, 4–5: 130/119 at two heights, 6–8 at three (8: 107, ~46 css px). A print is 1.26 × its width: the portrait square (0.85 of the width,
    `ChipSprite` so `HEAD_FRAME` frames it as in a circle) on a faded studio ground, toned warm
    with an inner vignette, on a cream border yellowed at its edges; the numeral in IM Fell on
    its foot; a wooden peg on its top edge; a box shadow down-right on the wall; tilted by a
    fixed table per seat (±3.1°) about where it hangs.
- **Never upscale.** No sprite atlases: HTTP/2 makes many small files cheap and an atlas adds
  tooling.
- Preload the game's nine characters (four states + head) at the deal; `next/image` `priority`
  on the first scene's figures.

### Vector

Two kinds, by whether they carry state:

- **Paint** — the dining car's plan (its walls, frame and floor are a painting, §4), the night
  rooms' photo line, the drape, the shutter's geometry, the station cloth. Pure functions of `(phase, units)`, no state, no
  children, no event handlers. **Ported as string generators** (the kits' style, typed) under
  `src/stage/paint/`, rendered by one memoised `<Paint html={…} />` per layer via
  `dangerouslySetInnerHTML`. Porting these to JSX buys nothing. Every `<filter>`, `<mask>`,
  `<linearGradient>` id is prefixed with `useId()` from the caller so two stages can share a page
  (the kits' `opts.id` rule).
- **Instruments** — stand and plaque (the stand's front a raster, §4), trap and lift,
  cards (back, small, full, the framed card), chips and their strings, wing tiles, the shutter's
  motion, the verdict board, act marks, sigils, the jar/table/plates, film rows, the drawer.
  **JSX components with props**, because they carry state, need keys, and animate in and out.
  `RoleKit.sigil()` and the act marks are tiny: `<Sigil role />`, `<ActMark kind />`.

Faction colour appears on a card only once it is face up (the handoff's card-back rule).

## 5. Fonts and tokens

The design's materials (`StageKit.vars()`: walnut, brass, felt, paper, the faction inks) become
CSS custom properties on the stage box, alongside the existing [tokens.css](../src/styles/tokens.css).
Fonts via `next/font` (`src/stage/fonts.ts`): the HUD's two voices (ruled 2026-09-29) are
`Young Serif` (`--font-display`: the day plaque, nameplates, tabs, seat numerals on brass and on
the wing) and `Literata` (`--font-body`, the stage's default face: speeches, the transcript, the
dock), no extra letter-spacing on body text; `IM Fell English` stays on paper, `Patrick Hand` on
the film's note slips, and the sans (Outfit) only where a plate still names it.
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
  multiplies them: normal ×1, fast ×0.5 (skip, no motion at all, was removed 2026-09-29).
- "Nothing moves to say chosen": selection is opacity/brightness, never transform.

**GPU rules (ruled 2026-09-25, from an A/B on the owner's Chrome; headless never shows these):**
- The world and the camera wrapper stay pinned to their own compositor layers
  (`will-change: transform` in `Stage.module.css`). Without it the count's push-in drops frames.
- A backdrop that fades out is a **picture**, never a live SVG (the car is a painting since
  2026-09-29, so it fades as an image; before that `PaintPicture` turned the generator's SVG
  into an image and faded the bitmap). A live filtered SVG fading on a GPU drops a whole black
  frame as Chrome gives it its own layer, and pinning that layer did not help.
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
cases; `PaintPicture`'s docstring (in git history, `Stage.tsx` before 2026-09-29) tells the second one.

## 7. The workbench

`app/workbench/[scene]/page.tsx` (one route). It reads the URL, folds the bundled fixture
(`src/stage/fixtures/replay-9369a5c1.json`, the full `ReplayGame`; the beat goldens use the same
file), picks the beat, and renders the scene through exactly the component the real pages use.

```
/workbench/vote?beat=5&viewer=spect|seat:player_7|xray&motion=normal|fast&slot=none|drawer|film&hud=live|replay|none&animate=0|1[&live=1][&frame=iphone14|iphone15max|pixel8|WxH]
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
├── Atmosphere.tsx           # the key light, haze, shadows, vignette and grain (§3 "Atmosphere")
├── countdown.ts             # a prompt's `m:ss` and the share left (the dock, the ballot, the plate)
├── textures.ts              # the room's surface pictures by URL (WOOD, VELVET), for the paints
├── paint/                   # string generators: station, window, shutter, drape, light —
│                            #   (phase, units) → svg string; dining-car.ts: the car's plan
│                            #   (diningCarPlan: the painting's place, its glass, glows, specials);
│                            #   texture.ts: the surfaces' SVG patterns (walnut, boards, velvet);
│                            #   bleed.ts: the platform's two strips past the world's sides (§3);
│                            #   station.ts: the platform (stationBack/Front, stationPlan);
│                            #   atmosphere.ts: the key light by hour, the car's haze;
│                            #   compartment.ts: the night rooms' plan (roomPlan: the painting,
│                            #   its glass, candle, card and photo line, ROOMS), the twine
│                            #   (photoTwine), the candle light (roomLight) and a choice's
│                            #   darkness (roomChoice), gradients only
├── instruments/             # JSX: Stand, Plaque, Trap, Lift, Clock, Shutter, CarBackdrop (the
│                            #   dining car's painting at an hour), Bleed (the bleed's paint,
│                            #   under a room's own; PaintedBleed, a painting's sides sinking),
│                            #   FeltWindow (the felt country behind the car's glass, and
│                            #   behind the night rooms' cleared glass), Compartment (a night
│                            #   room's painting, its window and its sinking edges), Photo
│                            #   (a seat's print on the line),
│                            #   RoleCard, CardBack, SmallCard, Chip, String, Wing (the seat
│                            #   rail: cards, suspect slot, note editor; rail-layout.ts),
│                            #   VerdictBoard, ActMark, Sigil, Jar, VoteTable, Plate,
│                            #   ActPlate (the night room's plate, with its countdown: the room
│                            #   has no clock since 2026-09-27; CarriageClock is gone), Pin (the
│                            #   pin through the chosen photo), ...
│                            #   (the jar's glass and lid, the stand's front and the table are
│                            #   painted rasters, SPRITES.props: §4)
├── cast/                    # Puppet (sprite + numeral overlay), castForGame,
│                            #   CastShadow (a figure's baked shadow on the wall),
│                            #   ChipSprite + headRect (the head portrait, framed by HEAD_FRAME)
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

`ReplayTheatre` also has a preview mode, `mini: { from, to, autoplay, speed?, controls?, under?, underEl? }` (the
landing's carriage, review 2026-09-26 §F7, amended 2026-09-27): the same reducer plays `from`..`to` of the public cut
round and round (`loop` in `replay-state.ts`, which plays past a beat that waits) at `fast` by default, and a
reduced-motion viewer gets it at rest. No keys (the page keeps its arrows and space) and no way back to `/replays`. Its
controls: none by default (`hud: 'none'`); `'stage'`, the replay's own HUD, slot and band, the band showing the window
only; or `'under'`, nothing on the stage and the state (`MiniUnder`) handed to `under`, which the caller portals into
`underEl` (the landing's phone pane). The loop's presses stay in the window, and the X-ray carries the window across to
its own list by the window's two end beats. The frame is the caller's.

## 9. Where this build departs from the handoff

Verified against the server before ruling; the handoff's bundled schema is byte-identical to
`server/schemas/events.py`, so the wire assumptions hold.

| Handoff says | The build does | Why |
|---|---|---|
| "names or seat numbers: open" | seat numbers | the wire's seats are `player_1..player_9`; there are no names |
| the translator should buffer `wolf_vote` | nothing | it already does (`server/game/translate.py`, `_buffer_wolf_votes`) |
| "your turn": Say it, Pass | + **Draft** from instructions to your agent, or its own line with none (three per turn, the wait credited back); **Send**, **Pass**; no hand-over on this turn (HUD pass 3b) | `POST /games/{id}/draft` landed 2026-09-17 (ux_journeys D25) |
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
