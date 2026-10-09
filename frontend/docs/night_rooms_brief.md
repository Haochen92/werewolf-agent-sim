# Night rooms brief: the new roles' compartments (draft 2026-10-07)

Status: DRAFT, revised 2026-10-07 with the owner's rulings: the Speculator's pick is a night
action, so it gets a room; the Necromancer's light matches his figure; the Fortune teller's
crystal ball is her room's light. The owner also ruled that the wolves keep their
existing room: the Chanteuse and the Illusionist play in the pack's red-lit "Grandma's things",
which `ROOM_OF` in `scenes/NightRoom.tsx` now says. Companion to `role_cards_brief.md`, whose
figures (shipped the same day) each room should agree with.

## 1. Which roles get a room

A room is where a seat makes its night choice. So a role gets one only if it acts at night.

| Role | Room | Why |
|---|---|---|
| Sentinel | new | watches one player every night |
| Trailseer | new | follows one player every night |
| Sigilist | new | places a sigil at night |
| Necromancer (level 2) | new | borrows a body from Night 2 |
| Fortune teller (level 2) | new | bets at the start of every night |
| Chanteuse, Illusionist | the wolves' room | ruled: the pack's room; their skill prompts open in it |
| Speculator | new | picks a side at night (owner, 2026-10-07: a night action, to keep it simple) |
| Investigator, healer, vigilante, serial killer | as now | unchanged |

Six new paintings. Build the four level 1 rooms first, as the engine does.

## 2. The plan every room keeps

The five rooms were painted to one plan (`claude_artifacts/design/rasters/refs/compartment-night.png`)
and the code relies on it (`paint/compartment.ts`). Every new room keeps all of it, identical:

- The camera, the 1536×1024 canvas, the walnut panelling, the brass luggage rack across the
  top, the carpet with its gold border.
- **The upper middle wall stays clear**: the photo line hangs there, one twine for every room,
  tied to the rack's lowest rail at x 280 and 835 (`LINE` in `compartment.ts`), with prints
  hanging from it down to about y 480 in the master (the lowest foot is ~430 units). So the
  clear band is x ≈ 280 to 835, from the rack down to the wooden rail at table height (y ≈ 570,
  a visible line the model can hold to, a little below what the photos need). A small
  overhang is tolerated, as shipped: the healer's herb bunch reaches x ≈ 335. **Below that
  rail the whole width is free**, which the shipped rooms already use: the wolves' rocking
  chair and yarn, the vigilante's barrel and rope. Tall pieces stand in the left corner
  (x 0 to about 260, the strip before the big plain panel).
- **The window** at the right in its rounded brass frame, the glass empty. In the plan file the
  glass is transparent (alpha 0), which one viewer shows as black and another as white, so the
  prompt says "empty, as in the attached picture" and names white as the fallback; either is a
  fill of the rounded rect when the glass is cleared. Nothing is placed in front of the glass:
  the five rooms' flames, flowers and lamp shades over it had to be cut out by hand, one picture
  at a time. The light on the table therefore stays **below the window frame's lower edge**:
  the healer's candle flame already reaches it, and the serial killer's and the wolves' rise in
  front of the glass.
- **The fold-down table** under the window, its light source at the right of it, and **a clear
  spot on its left half** where the stage stands the role card (200 units tall). The right
  half is only about 280 px wide, so a table holds **the light and at most two small things**;
  anything more goes to the floor corner.
- **The light source** on the table lights the room: its colour is the room's colour on the
  stage too (`warm` in `ROOMS`). The plan is already lit amber from the table. The four amber
  rooms keep that; the Speculator, the Necromancer and the Fortune teller need the prompt to
  replace the amber with their own colour, in words (image models ignore RGB values), or the
  model keeps the amber and adds a coloured prop on top. The stage does not animate the flame
  (the light is a still pool at the flame point), so a lamp or a glowing ball needs nothing
  different from a candle.
- **The carpet** keeps only a thin strip after the shipping crop (1536×915 from y 40), so
  nothing important goes on the floor's open middle.

Each new picture is then measured as the five were (glass rect, flame point, card spot) and
gets a `ROOMS` entry, a `RoomPicture` id and a `ROOM_OF` line.

## 3. The rooms

The same material as the five: walnut, brass, and the props in felt and stitched cloth, toy-like,
warm and a little macabre, never gory. The props are the figure's world, never the figure
itself (no doll of the role in its own room).

**Each room has its own shape** (revised 2026-10-07, the owner: the first draft's six rooms
shared one slot plan, a tall piece on the left, two things on the right wall's hooks, one in
the right floor corner, and would have come out as one room re-dressed). The shipped five
differ in density, in where their weight sits, and in whether the right wall is used: the
investigator's is the densest, the healer's a full apothecary wall, the vigilante's a shooting
gallery, the serial killer's nearly empty, the wolves' built around one rocking chair with the
right wall bare. The six spread over the same range:

| Room | Shape | Where the weight sits | Right wall |
|---|---|---|---|
| Sentinel | dense, a working room | left corner cupboard, a trolley low in the middle | coat and cap |
| Trailseer | medium, low and long | a long bench along the lower wall | bare |
| Sigilist | sparse, ceremonial | one banner, one lectern | one cap on one hook |
| Speculator | one big piece | the armchair, tape across the floor | bare |
| Necromancer | the densest | theatre, workbench, dolls along the wall's foot | crosses and cowl |
| Fortune teller | soft and draped | cloth spilling onto the floor, cushions | an empty birdcage |

These entries are the rationale. What the model reads is the prompt in section 4, written from
them with the notes, names and colour values left out, and with the "kept apart" negatives
moved to the gate (a negative that names an object tends to summon it).

### Sentinel: the attendant's pantry (dense)

The sleeping-car attendant's room, the one who knows every door on the corridor. A working room,
full of the night shift's stock, as dense as the healer's.

- Left corner: **a tall linen cupboard** standing open, its shelves stuffed with folded
  blankets, pillows and towels. High on the left wall beside it, a brass call-bell board, small
  bells each with a felt flag, a few flags dropped (a bell has rung), no numbers.
- Lower middle: a small tea trolley parked against the lower wall, a brass teapot, stacked cups
  and a folded cloth on it.
- Right wall: the attendant's midnight-blue coat and the cap with its gold crescent, on hooks.
- Right floor: a wicker laundry basket overflowing with pillowcases.
- Table: a short candle in a brass chamberstick (the light, the sheet's "sets a candle at one
  door"), a small brass hand bell.
- Light: amber, as every town room (`255,180,96`).
- Not taken from the review: a door by the bell board for the candle. The plan has no door.

### Trailseer: the rambler's boot room (medium, low and long)

The one who follows a trail to its door. The figure holds a card of two sole prints; the room is
about where shoes have been. Its weight is low and runs along the wall, with the right wall left
bare.

- Left corner: **a bentwood coat stand** with a mackintosh, a mustard tweed rucksack and a
  walking stick hung on it.
- Lower wall: **a long low wooden bench** running from the coat stand toward the middle, pairs
  of felt shoes lined along its seat and under it, every pair different (brogues, slippers,
  boots, heeled shoes), some muddy, one pair set a little apart from the rest.
- Right wall: bare.
- Right floor: a pair of muddy boots on a sheet of brown paper, a coiled cloth tape measure.
- Table: a short candle (the light), a plaster cast of a footprint, a brass compass.
- Light: amber.
- Gate, not prompt: kept apart from the investigator's office (no cork board, no red string, no
  magnifier). The footprint trail across the carpet stays dropped (the crop keeps only a strip
  of carpet).

### Sigilist: the seal-keeper's study (sparse, ceremonial)

The one who marks a door with a sign. The set's second sparse room after the serial killer's,
but warm and orderly rather than ominous: a few deliberate things and a lot of quiet wall.

- Left corner: **one tall bottle-green banner on a brass pole**, standing, an upright two-tone
  felt triangle with a stitched eye on it in gold.
- Lower middle: **a low walnut lectern** holding a large open book whose pages carry rows of
  green wax seals, no writing.
- Right wall: a low round bottle-green pillbox cap on a single hook. Nothing else.
- Right floor: nothing.
- Table: a short candle (the light), a brass seal stamp, a folded letter closed with a green wax
  seal.
- Light: amber.
- Gate, not prompt: every pyramid upright felt, no metal inverted pyramid (the Millennium Puzzle
  problem the figure had).

### Speculator: the financier's office (one big piece)

The one who backs a side like a stock. Built like the wolves' room, around one piece of
furniture, with one thing running across the floor as their yarn does.

- Left: **a deep chestnut-leather wing armchair**, a silver-grey overcoat thrown over its arm,
  a pale grey homburg on its seat. High on the left wall above it, three small plain felt
  pennants hung one above another: cream and green for the town, rust for the wolves, aubergine
  for the lone killer (three, not four: the neutral side is his own, not a pick).
- Beside the chair: a brass ticker machine on a narrow stand, its blank paper tape spilling out
  in long curls across the whole floor to under the table.
- Right wall: bare.
- Right floor: a small iron strongbox with brass corners, a closed felt purse on its lid.
- Table: a squat brass lamp with a small frosted glass globe, its top below the window frame
  (the light), two stacks of gold coins.
- Light: pale moon-silver (`214,224,240`), the neutral side's colour; the prompt replaces the
  plan's amber with it.
- Gate, not prompt: no green banker's lamp (the investigator's).

### Necromancer: the puppeteer's workshop (the densest, level 2)

Necrophos's room, as his figure: green, sallow, toy-macabre, and more crowded than the
investigator's. The prompt calls it the puppeteer's workshop; the figure's game reference stays
out of it.

- Left corner: **a narrow puppet theatre** on a cabinet, felt curtains half open, one limp grey
  doll hanging on strings inside its little stage.
- Lower middle: **a low workbench** against the lower wall, a half-sewn grey felt doll lying on
  it with a pincushion, scraps of grey felt and spools of thread. Along the foot of the wall and
  in an open crate, more small grey felt dolls sitting slumped, each with closed eyes stitched as
  two short curves and a flat mouth, the stage's "out" face: the borrowed dead, nobody in
  particular. Felt scraps and loose thread on the carpet.
- Right wall: two marionette control crosses hanging with their strings empty, a dark-green
  hooded cowl on a hook.
- Right floor: a toy coffin-shaped felt box, its lid ajar, one small grey felt hand over its edge.
- Table: a short candle with a sickly yellow-green flame (the light), a spool of cream thread
  with a needle in it.
- Light: yellow-green (`190,230,110`) to match his figure (owner, 2026-10-07), never toward
  cyan; the prompt replaces the plan's amber with it. The serial killer's room keeps its violet.

### Fortune teller: the séance parlour (soft and draped, level 2)

The parlour medium who reads tonight's deaths in the glass. The only room whose walls are soft:
cloth, not furniture.

- Left wall: **drapes of moon-silver and slate cloth** hung from high on the left wall and
  spilling onto the floor in folds, a gold fringe, a small star chart pinned to them (stars
  joined by lines, no writing), a bead curtain at their edge.
- Lower middle: a heap of tasselled floor cushions around **a low round tea table** with a
  fringed cloth, a small teapot and two cups on it (tea leaves, the parlour's other way of
  reading).
- Right wall: an empty brass birdcage hanging from a hook, its door open, one small feather on
  its floor. Empty, not with a bird: the cast has a songbird and an owl, and a bird here could
  read as one of them.
- Right floor: nothing.
- Table: a low crystal ball on a short claw stand (the light, its top below the window frame),
  a fan of felt cards with stars on their backs, a small slate with chalk tally marks (her
  points; tallies, not numerals).
- Light: the crystal ball (owner, 2026-10-07), pale moon-silver (`214,224,240`); the prompt
  replaces the plan's amber with it.

## 4. The prompt

The five were made by repainting the plan. The same here: the plan attached, one room per call.

```
EDIT THE ATTACHED COMPARTMENT. This is a set-dressing task, not a redesign. Create one
image, landscape 1536x1024.

<the KEEP IDENTICAL, THE WINDOW, STYLE OF THE PROPS and WHERE THINGS MAY GO blocks from
the all-six prompt below, as they are>

<that room's block from the all-six prompt, starting at "ROOM n">
```

Attach one picture: `claude_artifacts/design/rasters/refs/compartment-night.png`, the bare
plan the five were painted from (owner, 2026-10-07). Its glass is empty (transparent) and its
table already empty, so the prompt only adds. If a room's props come out in a different
material from the five, a finished room (the healer's) can go in as a second attachment for
the props' style only, named as such in the prompt so its props are not copied. Use the
healer's uncropped master (`rasters/rooms/healer.png`, 1536×1024, the plan's size; the shipped
crop is 1536×915 and a second size can nudge the framing). Its glass holds a painted
checkerboard, so say in the prompt that the second picture's window is not to be copied.

**All six in one call** (owner, 2026-10-07: handed to ChatGPT as one request, which returns
separate images; the plan attached once). The per-room prompt above stays for reruns: if one
room comes back wrong, rerun that room alone with the plan attached.

```
EDIT THE ATTACHED COMPARTMENT SIX TIMES.

This is a set-dressing task, not a redesign. The attached picture is the bare plan of a
1920s sleeping-car compartment at night. Create SIX SEPARATE IMAGES, one per room below,
each one the attached compartment with that room's props added. The six rooms should
feel different from each other: some crowded, some nearly empty, each arranged its own
way, as described.

Do NOT create a contact sheet, collage, grid or multi-panel image. Six separate images,
each landscape 1536x1024, in the order listed.

KEEP IDENTICAL IN EVERY IMAGE (do not move, resize, recolour or restyle any of it):
the camera and framing; the walnut panelling and its brass studs; the brass luggage rack
across the top; the rounded brass window frame at the right; the fold-down table under
the window; the dark carpet with its gold border.

THE WINDOW: the glass stays empty, exactly as in the attached picture. If the image
cannot keep it transparent, fill the glass with flat plain white. Nothing stands or
hangs in front of the glass.

STYLE OF THE PROPS: handmade felt and stitched cloth with brass and walnut, toy-like,
softly lit, warm and a little macabre, never gory. No text, letters or numbers anywhere,
on anything. No people, figures or faces except the small dolls named in room 5.

WHERE THINGS MAY GO:
- The upper wall between the left corner and the window (the two big plain panels under
  the luggage rack, above the wooden rail that runs along the wall at table height) stays
  completely clear and bare.
- Tall things stand in the left corner and on the left wall only, never in front of the
  big plain panel.
- Below the wooden rail, the whole width of the room is free for low furniture and floor
  props.
- The left half of the fold-down table stays clear and empty. The room's light stands at
  the right end of the table; it is short, its top below the bottom edge of the window
  frame, and it is the room's only light, casting its colour over the whole room. The
  table holds the light and at most two small things.

ROOM 1, THE ATTENDANT'S PANTRY. Crowded, a working room. Light: a short candle in a brass
chamberstick, warm amber.
- Left corner: a tall linen cupboard standing open, its shelves stuffed with folded
  blankets, pillows and towels. High on the left wall beside it, a brass call-bell board,
  small brass bells each with a little felt flag; a few of the flags have dropped.
- Low against the wall in the middle: a small tea trolley with a brass teapot, stacked
  cups and a folded cloth.
- Right wall, on brass hooks: a midnight-blue attendant's coat and a midnight-blue cap
  with a small gold crescent.
- Right floor corner: a wicker laundry basket overflowing with pillowcases.
- Table, beside the light: a small brass hand bell.

ROOM 2, THE RAMBLER'S BOOT ROOM. Long and low, the right wall left bare. Light: a short
candle in a brass holder, warm amber.
- Left corner: a bentwood coat stand with a mackintosh, a mustard tweed rucksack and a
  walking stick hung on it.
- Low along the wall: a long low wooden bench running from the coat stand toward the
  middle of the room, pairs of felt shoes lined along its seat and underneath it, every
  pair different (brogues, slippers, boots, heeled shoes), some muddy, one pair set a
  little apart from the rest.
- Right floor corner: a pair of muddy boots standing on a sheet of brown paper, a coiled
  cloth tape measure beside them.
- Table, beside the light: a plaster cast of a footprint and a brass compass.

ROOM 3, THE SEAL-KEEPER'S STUDY. Nearly empty, calm and orderly: a few deliberate things
and a lot of quiet wall. Light: a short candle in a brass holder, warm amber.
- Left corner: one tall bottle-green felt banner on a standing brass pole, showing an
  upright two-tone felt triangle with a stitched eye in gold thread.
- Low in the middle of the room: a low walnut lectern holding a large open book whose
  pages carry neat rows of green wax seals.
- Right wall: a single brass hook with a low round bottle-green pillbox cap. Nothing else.
- Table, beside the light: a brass seal stamp and a folded letter closed with a green wax
  seal.

ROOM 4, THE FINANCIER'S OFFICE. Built around one big armchair. Light: a squat brass lamp
with a small frosted glass globe. Replace the warm amber glow on the table and walls with
a pale, cool silver light from this lamp.
- Left: a deep chestnut-leather wing armchair, a silver-grey overcoat thrown over its arm
  and a pale grey homburg hat on its seat. High on the left wall above it, three small
  plain felt pennants hung one above another: one cream and green, one rust red, one
  aubergine.
- Beside the armchair: a brass ticker machine on a narrow stand, its blank paper tape
  spilling out in long curls across the whole floor to under the table.
- Right wall: bare.
- Right floor corner: a small iron strongbox with brass corners, a closed felt purse on
  its lid.
- Table, beside the light: two stacks of gold coins.

ROOM 5, THE PUPPETEER'S WORKSHOP. The most crowded room. Light: a short candle with a
sickly yellow-green flame. Replace the warm amber glow on the table and walls with a
sickly yellow-green light from this candle.
- Left corner: a narrow puppet theatre on a cabinet, its felt curtains half open, one limp
  grey felt doll hanging on strings inside its little stage.
- Low against the wall in the middle: a low workbench with a half-sewn grey felt doll lying
  on it, a pincushion, scraps of grey felt and spools of thread. Along the foot of the wall
  and in an open crate, more small grey felt dolls sitting slumped, each with closed eyes
  stitched as two short curved lines and a flat mouth, all alike, none resembling anyone.
  Felt scraps and loose thread on the carpet.
- Right wall: two wooden marionette control crosses hanging with their strings empty, and
  a dark forest-green hooded cowl on a brass hook.
- Right floor corner: a toy coffin-shaped felt box, its lid ajar, one small grey felt hand
  resting over its edge.
- Table, beside the light: a spool of cream thread with a needle in it.

ROOM 6, THE SEANCE PARLOUR. Soft and draped: cloth instead of furniture. Light: a low
crystal ball on a short gold claw stand, glowing softly from inside; no candle. Replace
the warm amber glow on the table and walls with a pale, cool silver light from the
crystal ball.
- Left wall: drapes of moon-silver and slate cloth hung from high on the left wall and
  spilling onto the floor in soft folds, with a gold fringe, a small star chart pinned to
  them (stars joined by lines), and a bead curtain at their edge.
- Low in the middle of the room: a heap of tasselled floor cushions around a low round tea
  table with a fringed cloth, a small teapot and two cups on it.
- Right wall: an empty brass birdcage hanging from a hook, its little door open, one small
  feather on its floor.
- Table, beside the light: a fan of felt cards with stars on their backs and a small slate
  with chalk tally marks.
```

**Gate**, before measuring: the rack, window frame and table sit where the plan has them
(overlay at 50%); the glass is empty (transparent or flat white), nothing over it; the light's
top is below the window frame; the upper middle wall (x ≈ 280 to 835, rack down to the rail at
table height, an overhang to x ≈ 335 tolerated) is clear; the six rooms differ in shape as the
table in section 3 says (a crowded room that came back sparse, or the reverse, is a rerun); the
table's left half is clear and its right half holds the light and at most two things; the
three relit rooms carry their own colour, not the plan's amber. Then the negatives kept out of
the prompt: no checkerboard in the glass; the Trailseer's room has no cork board, red string or
magnifier; the Sigilist's pyramids are upright felt, never a metal inverted pyramid; the
Speculator's lamp is not a green banker's lamp; the Necromancer's light is not turquoise.

## 5. Shipping a room

Shipped 2026-10-07: all six (the Speculator after one edit that lowered its lamp below the
window frame and made its pennants plain), through `scripts/fit-night-rooms.mjs`. Gate results:
rack and window frame within 2 px of the plan in all six; glass 98 to 99% clean white before
clearing; corner radii 46 to 49 (the five: 44 to 49); one card spot for all six, [1045, 628], the
plan's table; light points on each flame or glow.

As the five (stage_architecture §4 "The night rooms"): the master to
`claude_artifacts/design/rasters/rooms/<id>.png`; clear the glass (an empty or flat white glass makes this a
fill of the rounded rect, no checker to fit); crop the band 1536×915 from y 40; WebP quality
82. Then measure the glass rect, the flame point and the card spot into `ROOMS`, add the id to
`RoomPicture` and the manifest, and the role to `ROOM_OF`.

## 6. Open for the owner

Nothing. Ruled 2026-10-07: the Speculator picks at night and has a room; the Necromancer's
light is yellow-green; the Fortune teller's crystal ball is her light.
