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
2. `haze` — the atmosphere's back half: the key light on the wall, the wall pieces' shadows, the veil
3. `floor` — apron, trap, lift
4. `figures` — puppets, plush, chips on strings, cards on strings
5. `stand` — the stand, plaque, footlights
6. `instruments` — table, jar, plates, verdict board, act marks, the shelf's objects
7. `light` — the pool, specials, glows, the "chosen" lighting
8. `grade` — the atmosphere's front half: the key light's falloff, the vignette, the grain
9. `hud` — top strip, wing, side slot (drawer or film), the dock

The HUD is inside the box (it is part of the 1600×900 geometry), so the drawer's width and the
wing's tiles scale with everything else. A modal overlay (the full card, the epilogue's sheet, the
portrait interstitial) sits above the box in normal page flow. `grade` and `hud` sit outside the
camera's box: a push-in moves the room under the grade, as under a lens.

**Atmosphere (2026-09-27, the polish pass's first step).** One warm key light from the upper left
(the puppets' own), carried over the whole room so the painted props and the flat vector pieces
sit in one lit, filmed set. `Atmosphere.tsx`, one per scene (the car's and the rooms'; the
platform has none), fills two layers:
- `haze` (over the paint, under everything that stands in front of it): the key light's warm lift
  on the upper-left wall (`KEY` in `paint/atmosphere.ts`: day 1, dusk and dawn 0.8, night 0.3,
  so the night stays lamp-led); in the car, `carHaze`: the soft shadow the window's frame and
  pelmet throw down-right onto the wall (masked by the window, so it never lies on it; the clock
  and the lamp throw their own, below), then a warm dark veil over the whole back (0.15 at the ceiling to 0.07 at
  the floor) that sets the wall, window, clock and lamp back behind the stand, the table and the
  figures, left open round a lit lamp; in the shelf room a lighter plain veil and no key light
  (its candle leads: `shelfLight`, beat sheet §6, 2026-09-27).
- `grade` (over the light, under the HUD, outside the camera): the key light's falloff (0 to
  0.14 towards the lower right), a vignette on the puppet's room (0 to 0.18 at the corners) and a
  still film grain (`SPRITES.grain`, a 160 px noise tile at 1.5 units a grain, 0.16).
- Contact and cast shadows, all down-right: each puppet and doll throws a baked silhouette on the
  wall (`cast/CastShadow.tsx`; `SPRITES.shadow`, 55 WebPs, ~98 KB; a puppet's falls 0.09 × 0.05
  of its height at 0.5, a doll's 0.05 × 0.035 at 0.38), a chip on its string a soft disc, the
  lynch's card a soft box, the wall clock (swaying with it) and the wall lamp their baked
  silhouettes (`SPRITES.shadow.wall`, 18×15 at 0.46 and 26×22 at 0.5). No shadow lies on the window's glass (a view through glass
  takes none): where the shutter is open behind them, the puppets' and the chips' shadows move in
  a still box clipped to everything but the glass (`offGlass` in `cast/CastShadow.tsx`), in step
  with their figure; the stand throws a soft pool off its right side; on the vote's table,
  soft gradient ellipses under the table (the lift shadow, retuned), the jar (tipped with it),
  each plate and each tower of chips.
- GPU (§6): nothing moves or fades; normal alpha only, no blend mode and no CSS filter. The one
  SVG blur is `carHaze`'s, static like the car's own cut-outs. Baked shadows ride inside their
  figure's box, so they rise and fall with it and nothing is blurred live. The pass adds five
  static composited layers (the grade and the haze, promoted for overlapping the window's idle
  animations) and no extra churn while a beat plays (measured 2026-09-27).
- Ruled 2026-09-27: kept, and unconditional (the workbench's `light=off` compare switch is gone).

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
  src/assets/sprites/wood/walnut.webp               (the station's beam and ledge only)
  src/assets/sprites/textures/{walnut,boards,velvet}.webp
  src/assets/sprites/station/{sky,floor,post,lamp,train,blind}.webp
  src/assets/sprites/window/{day,dusk,night,dawn}-{far,near}.webp
  src/assets/sprites/props/{jar-glass,jar-lid,stand-front,vote-table}.webp
  src/assets/sprites/props/{wall-clock,wall-lamp-unlit,wall-lamp-lit}.webp
  src/assets/sprites/shadow/day/<character>/{base,talking,thinking,out}.webp
  src/assets/sprites/shadow/plush/<character>.webp
  src/assets/sprites/shadow/{wall-clock,wall-lamp}.webp
  src/assets/sprites/atmosphere/grain.webp
  ```
  Characters: `cat hare owl badger cyclops threeEyes dragon onion whale polarBear shade`.
- Imported only from [src/assets/manifest.ts](../src/assets/manifest.ts) (the existing ruling:
  static imports through `next/image`, content-hashed URLs, inferred dimensions). The manifest
  exports typed handles — `SPRITES.day[character][state]`, `SPRITES.plush[character]`,
  `SPRITES.kits[name]`, `SPRITES.wood`, `SPRITES.textures[name]` — and `BODY: Record<Character, { top: number; body:
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
- The dining car's window (ruled 2026-09-27): the country behind the glass is painted felt, a
  pair per hour, `SPRITES.window[hour].{far,near}`, drawn by `instruments/FeltWindow.tsx` over the
  car's paint, inside the glass: `far` (sky, peaks, hills) stands still and covers the glass;
  `near` (pines, fence, pole, with alpha) fills the bottom 52% and loops left one tile width,
  crossfading with the car at an hour change. The vector paint draws only the frame and a flat
  sky fill under it. Masters: `claude_artifacts/design/rasters/window-<hour>-{far,near}.png`
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
- The wall clock and the wall lamp (2026-09-27): the owner's paintings replace the kit's vector
  clock and lantern, `SPRITES.props.{wallClock,wallLampUnlit,wallLampLit}`. Masters:
  `claude_artifacts/design/rasters/{wall-clock,wall-lamp-unlit,wall-lamp-lit}.png`. Recipe: crop
  to the alpha box plus a margin (clock `844x1216+206+6`; both lamps one frame, `986x1526+25+0`),
  `-resize 50%` (they hang ~230 units tall), then the props' `-alpha background` and quality
  85. The unlit lamp's frosted panes were first darkened and cooled a little (a feathered box
  over the glass, master px 395–955 × 725–1270, its pale grey pixels ×0.82 towards blue-grey) so
  the glass is not the brightest spot on the wall by day.
  - **Clock** (`WallClock.tsx`): a picture with no hands, hung at the plan's clock and sized so
    its twelve dots (file px, centre 210.53, 385.78, radius 134.34) lie at the kit's 0.66 r; the
    face is then the kit's 0.8 r and the hands, the red ring and the pivot, still code, turn
    about its centre. The cord ties to the chain's top (file px 4.5). The room's tint (a masked
    overlay, the face left out) falls on the brass and fades with the car's at an hour change;
    CarPaint hangs it with the hour's time (`CLOCK`), the hands sweeping forward from the last.
  - **Lamp** (`WallLamp.tsx`): its glass (file px 187.5–462.5 × 365–632.5) centred on the kit's
    lantern glass and 78 units tall. Unlit or lit by the hour's `lit`; where the lit changes, the
    old picture fades off over the new with the car's fade (an image's opacity). The room's
    tint is a still overlay in its shape (lit, 0.6 of it and none on the glass). Its special,
    halo, pool and glow stay the car's code, round the same centre.
  - The car's paint no longer draws either; the kit-fidelity test swaps them out of the kit
    (`paint.test.ts`, with the lit lantern's flame), as it does the window's country.
- The room's surfaces (2026-09-27): the flat vector walls, floor and valance are filled with
  seamless textures, `SPRITES.textures.{walnut,boards,velvet}`, as SVG patterns
  (`paint/texture.ts`). The shapes stay the paint's vector (they move with the side slot, the
  bleed and the hours); the texture only fills them, anchored to the world's units, so it runs on
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
    pelmet, and the bleed's strips of the car and the shelf room. The panel lines, dado, brass
    rail and mouldings stay vector on top.
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
    exactly and its folds and pile. The replay's valance and its bleed; the gold hem, the border
    and its scallops stay vector.
  - **The method: the pattern is inside the paint's SVG**, not a DOM layer under it. The car's
    hour tint is a multiply and its glows a screen inside its SVG; they have to reach the texture,
    and a layer under a transparent wall would take them as flat colour instead. The paints take
    the textures' URLs (`wood`, `walnut`, `velvet` options; without them they draw the kit's flat
    colours, byte for byte). The one catch is the fading car: an SVG drawn as an image cannot load
    files. `PaintPicture` (Stage.tsx) therefore writes each picture its SVG points at into it as a
    data URI, the same bytes the live paint shows, fetched once (from the browser's cache) and
    kept; the car scenes warm that cache when they mount (`preloadPictures`), and until it is
    ready (a change on a page's very first frame) the fading copy is the live SVG. So nothing is
    added to the JS or the HTML; a fading car's data URL is ~177 KB, built once per fade.
    Checked 2026-09-27: the picture, forced back to full opacity after the vote's dusk→night and
    the morning's change, matches the live paint of its hour (mean difference under 2.5/255, the
    image's own resampling of the boards' fine grain).
  - Kit fidelity: `paint.test.ts` holds the textured car to the kit's `scene()` with its
    documented swaps (the pattern defs after the kit's first defs; the wall, dado, floor strip and
    trap fills; the dado's veil), as it does the window, clock and lantern.
- The atmosphere's pictures (2026-09-27, §3 "Atmosphere"), made from the shipped WebPs, not
  masters. Shadows, per day figure and state, per plush doll, and for the wall clock and the
  (unlit) lamp: `convert <sprite> -alpha extract
  -resize x128 -bordercolor black -border 12 -blur 0x3 -background '#0c0704' -alpha shape
  -quality 80 -define webp:alpha-quality=70 -define webp:method=6` (`CastShadow` reads the 128
  and the 12). Grain: a 160 px `+noise Gaussian` tile on gray50 (`-seed 7`), each pixel white or
  black by its side of the middle, alpha its distance from it (×0.5 white, ×0.9 black, so it
  does not grey the dark), lossless.
- Sharpness: the 600 px day cuts are right at 1× and slightly soft at 2× for the puppet at the
  stand. If the ~900 px cuts still exist in the chat, re-export them as the masters. **Never
  upscale.** No sprite atlases: HTTP/2 makes 44 small files cheap and an atlas adds tooling.
- Preload the game's nine characters (four states + chip) at the deal; `next/image` `priority`
  on the first scene's figures.
- Known defect: the shade's base cut has a baked "3"; regenerate.

### Vector

Two kinds, by whether they carry state:

- **Paint** — the dining car's panels, window frame, the shelf and brackets, the drape, the
  shutter's geometry, the station cloth. Pure functions of `(phase, units)`, no state, no
  children, no event handlers. **Ported as string generators** (the kits' style, typed) under
  `src/stage/paint/`, rendered by one memoised `<Paint html={…} />` per layer via
  `dangerouslySetInnerHTML`. Porting these to JSX buys nothing. Every `<filter>`, `<mask>`,
  `<linearGradient>` id is prefixed with `useId()` from the caller so two stages can share a page
  (the kits' `opts.id` rule).
- **Instruments** — stand and plaque (the stand's front a raster, §4), trap and lift, the clock (dial, hand, arc, counter),
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
  The paint's textures go into the image as data URIs, so it matches the live paint (§4).
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
├── Atmosphere.tsx           # the key light, haze, shadows, vignette and grain (§3 "Atmosphere")
├── countdown.ts             # a prompt's `m:ss` and the share left (the dock, the ballot, the plate)
├── textures.ts              # the room's surface pictures by URL (WOOD, VELVET), for the paints
├── paint/                   # string generators: diningCar, shelfRoom, station, window,
│                            #   shutter, drape, light — (phase, units) → svg string;
│                            #   texture.ts: the surfaces' SVG patterns (veneer, boards, velvet);
│                            #   bleed.ts: the room's two strips past the world's sides (§3);
│                            #   station.ts: the platform (stationBack/Front, stationPlan);
│                            #   atmosphere.ts: the key light by hour, the car's haze;
│                            #   shelf-room.ts: the seat's room, its candle light (shelfLight)
│                            #   and a choice's darkness (shelfChoice), gradients only
├── instruments/             # JSX: Stand, Plaque, Trap, Lift, Clock, WallClock, WallLamp, Shutter,
│                            #   Bleed (the bleed's paint, under a room's own),
│                            #   FeltWindow (the felt country behind the car's glass),
│                            #   RoleCard, CardBack, SmallCard, Chip, String, WingTile, Wing,
│                            #   VerdictBoard, ActMark, Sigil, Jar, VoteTable, Plate,
│                            #   ActPlate (the night room's plate, with its countdown: the room
│                            #   has no clock since 2026-09-27; CarriageClock is gone), Pin (the
│                            #   pin in the chosen doll), ...
│                            #   (the jar's glass and lid, the stand's front, the table, the
│                            #   wall clock and the wall lamp are painted rasters,
│                            #   SPRITES.props: §4)
├── cast/                    # Puppet, Plush, Kit (sprite + numeral overlay), castForGame,
│                            #   CastShadow (a figure's baked shadow on the wall)
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
