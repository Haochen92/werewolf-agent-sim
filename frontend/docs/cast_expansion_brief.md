# Cast expansion brief (2026-10-03)

## Final template (ruled 2026-10-03, after four bases were approved)

What the rounds taught: the model under-delivers on proportions, so the spec aims past the goal
(60–65% head, not 58%); a comparative "make it noticeably cuter" edit on the base moves more than
a fresh generation, so the cuteness pass is a standard step; "simplify the costume slightly" keeps
the outfit from fighting the head; naming the texture, seams and finish as things to preserve
stops an edit drifting in material; a larger cream face area reads baby-like on furred
characters. Blush is per character (kitsune and mushroom yes, lion and automaton no), a design
detail like the patch, not a style constant.

```
SHARED BLOCKS (paste into every step)

STYLE: a handmade plush toy in soft felt: visible stitched seams, one small square felt
patch stitched on the head, a polished toy-like finish. Soft studio light from the upper
left with a gentle darker right side. The noir mood lives in the lighting and the costume
cloth only, never in the expression. No text, letters or numbers anywhere.

FACE: a round face with a large plain forehead. Two large glossy black bead eyes, each
with one white highlight, set wide apart and placed in the lower half of the head. A tiny
dot nose. A very small simple closed smile directly under the eyes. Furred characters get
a large round cream face area for a soft baby-like look. No projecting snout, muzzle or
jaw. [per character: "two faint pink blush spots" or "no blush"]

PROPORTIONS: exaggerated chibi plush-toy proportions. The head is 60 to 65% of the total
height, rounder than it is tall and wider than the body. No visible neck. A small, short,
squat body with very short legs or none, the oversized rounded shoes sitting directly
under the body. Thick mitten-like arms. The whole silhouette about two thirds as wide
as it is tall. Cute first, dressed-up second.

COSTUME: 1920s train-and-travel life, simplified so the character reads cute first and
dressed-up second: one signature garment, one hat or head ornament or none, at most one
small prop held at one side. No magnifying glass, spyglass, medical items, weapons,
badges, masks, pelts or lanterns. No red, violet, purple, cyan or turquoise as a body or
costume colour. No writing on props, tags or patches.

STEP 1, LINEUP (whale base attached): landscape 1536x1024 on plain dark brown #1a120c.
The shared blocks, then the figures left to right with the attached character first,
all one height, feet on one line. Judge colour and silhouette here only.

STEP 2, BASE (whale base + lineup attached): portrait 1024x1536, transparent PNG. The
shared blocks. "Reproduce figure N from the sheet (the <creature> in the <costume>)
exactly. Frame it like the whale: one figure, full body, facing front, centred, feet on
the bottom edge, the top of the head about 6% below the top edge. Base pose: eyes open,
small closed smile, arms relaxed, the prop held at one side."

STEP 3, CUTENESS PASS (the base attached; run once, expect to need it): "Make this
character noticeably cuter in an exaggerated chibi plush-toy style. Enlarge the head to
60 to 65% of the total height with a rounder silhouette and more plain forehead. Place
the eyes slightly lower, large, glossy and wide apart. Keep the nose tiny and the smile
very small. [furred: enlarge the cream face area.] Make the body smaller, shorter and
squatter, no neck, very short legs, thick mitten arms, oversized rounded shoes. Keep the
costume, prop and colours but simplify the costume slightly. Preserve the felt texture,
stitched seams and polished finish. Same framing, transparent background, 1024x1536."

GATE before the poses, measured on the alpha box: width over height at least 0.65, and
the body at its widest at least as wide as the head. (The whale is 0.73 and 1.13; the
four approved bases are 0.65 to 0.70.)

STEP 4 + 5, THE STATES: the owner's exact prompt below, unchanged (the eleven were made with
it, so its pose definitions are the family's). One call, the approved base attached, four
separate images back. Fallback: if one state comes back drifted (the 2026-09-28 masters moved
up to 32 px on some), rerun that single state alone with the base attached, not all four.
```

```
EDIT THE ATTACHED APPROVED BASE SPRITE.

This is a character-state generation task, not a redesign.

Create FOUR SEPARATE PNG IMAGES from the attached approved base sprite:

1. TALKING
2. THINKING
3. OUT
4. HEAD AVATAR

Do NOT create a contact sheet, collage, sprite sheet or multi-panel image.
Return FOUR SEPARATE IMAGES.

PRESERVE THE CHARACTER EXACTLY:
- same identity
- same species
- same anatomy and proportions
- same head size
- same body size
- same costume
- same colours
- same textures
- same stitching
- same patches
- same prop
- same lighting
- same camera
- same scale
- same horizontal position
- feet in exactly the same place for all full-body states

Do NOT redesign anything.
Do NOT simplify anything.
Do NOT change the costume.
Do NOT change the prop hand.
Do NOT change the overall character height.

TRANSPARENCY FOR ALL FOUR OUTPUTS:
REAL PNG ALPHA TRANSPARENCY.
Everything outside the character must be genuinely transparent.
No black background.
No white background.
No coloured background.
No fake checkerboard.
No floor.
No cast shadow.
No scenery.
No halo or glow.

==================================================
IMAGE 1 — TALKING
==================================================

Create the TALKING state.

Change only:
- change the closed mouth into a small slightly open mouth as if speaking
- keep the prop in the same hand
- raise the other, empty hand to chest height in a natural open explaining gesture
- keep the expression earnest, calm, gently cute and reserved
- add exactly THREE short warm-cream motion lines beside the raised hand

Do not move the feet.
Do not change the overall character height.
Do not add text.

==================================================
IMAGE 2 — THINKING
==================================================

Create the THINKING state.

Change only:
- keep the prop in the same hand
- bring the other, empty hand gently up to the chin
- keep the mouth closed
- narrow the eyes very slightly
- let the eyes glance subtly to one side
- keep the expression thoughtful, calm, cute and reserved, not suspicious
- add a small cream thought bubble above the head on the right
- the thought bubble must be made of two small circles rising to one small cloud
- nothing inside the cloud

Do not move the feet.
Do not change the overall character height.
Do not add text.

==================================================
IMAGE 3 — OUT
==================================================

Create the OUT state.

Change only:
- close both eyes into two gentle downward arcs
- tilt the head down very slightly
- keep the mouth closed and neutral

The character should look quietly asleep or inactive,
not dead, sad, creepy or injured.

Keep both arms and the prop exactly as in the base sprite.

Do not move the feet.
Do not change the overall character height.
Do not add symbols, text or effects.

==================================================
IMAGE 4 — HEAD AVATAR
==================================================

Create a HEAD AVATAR of the same character.

This is not a redesign.

Preserve exactly:
- character identity
- face
- head proportions
- colours
- fabric texture
- stitching
- headwear
- horns
- ears
- antennae
- sprouts
- water spouts
- facial markings
- glasses or other head accessories
- base expression
- lighting direction

OUTPUT:
- square 1:1 canvas
- transparent PNG with real alpha transparency
- facing directly toward the viewer
- show the full head
- include all ears, horns, antennae, hats, sprouts, water spouts or other head anatomy
- include a small amount of shoulders / upper chest only
- head centred and filling about 80–85% of the square
- leave comfortable transparent padding around all edges

Use the same base expression:
- calm
- attentive
- quietly curious
- softly serious
- still somewhat cute
- small closed mouth

Do not add:
- prop
- motion lines
- thought bubble
- frame
- border
- floor
- cast shadow
- scenery
- text

==================================================
FINAL CHECK
==================================================

Before returning the four images, verify:

1. TALKING, THINKING and OUT are exactly the same character as the approved base.
2. TALKING, THINKING and OUT keep the same scale, camera distance, body size and foot baseline.
3. The prop stays in the same hand in TALKING and THINKING.
4. HEAD AVATAR clearly matches the same character.
4.5 HEAD AVATAR square size, the head filling about 80% of the image, the
shoulders and scarf running straight off the bottom edge (no curved or rounded crop)
nothing in the corners.
5. Every output has a truly transparent background.

Return FOUR SEPARATE PNG IMAGES only:
- TALKING
- THINKING
- OUT
- HEAD AVATAR
```

The rounds below are the history that produced this template; the character lines in Round 3
and Round 4 are the current designs.


Candidates ruled 2026-10-03: kitsune, axolotl, lion cub, button mushroom, tin automaton, with the
unicorn as the alternate for the pink slot (pick one of axolotl / unicorn). Dropped: shiba (the
kitsune's slot), yeti (the polar bear), dinosaur (the dragon), griffon (the owl), shishi (the
snarl cannot be prompted away; the lion cub is what remains).

New characters are held to the costume rule in full: no role props (magnifying glass, spyglass,
medical items, weapons, badges, masks, pelts, lanterns), no numerals, no dominant red / violet /
cyan, equal mild expressions. The eleven existing characters are grandfathered (shade is red,
threeEyes is cyan).

Free colour slots: rust orange, gold/ochre, pink/coral, warm metal (copper, brass).

## Process

1. One lineup sheet (prompt 1) with the whale base attached as the style anchor and placed at the
   left end. Judge colour clashes and silhouette overlap here, pick the five.
2. Per character, in order: base (prompt 2, whale base + lineup attached), iterate until approved;
   then talking, thinking, out (prompt 3, the approved base attached, never the whale); then the
   head (prompt 4). Six generations per character, one pose per image, no multi-pose sheets (the
   2026-09-28 sheets drifted up to 32 px between poses; see stage_architecture.md "The cast").
3. Masters to `frontend/claude_artifacts/design/rasters/cast/<id>/{base,talking,thinking,out,head}.png`
   (gitignored, beside the eleven existing characters; bases for all four saved 2026-10-03),
   ids: kitsune, axolotl, lionCub, mushroom, automaton, unicorn. Then the Pillow conversion,
   registration, canvas, BODY and REACH per the stage doc.

Adding characters lengthens the pool `castForGame` shuffles, which re-deals every archived game's
puppets; decide before merging whether to freeze the eleven for games before a cutoff date.

## Prompt 1, the lineup sheet (attach the whale base)

```
Landscape image 1536x1024, plain dark warm brown background (#1a120c), no text, no numbers.

STYLE: match the attached plush toy character exactly. Soft felt and plush toy, visible
stitched seams, one small square felt patch stitched somewhere on the head, glossy black
bead eyes with one white highlight, tiny stitched nose, soft studio light from the upper
left with a gentle darker side on the right (noir mood from the lighting only, never from
the expression). Big head about half the total height, short stubby body, little round
shoes, standing facing front. Same mild small closed smile as the attached character on
every figure: nobody smirks, nobody looks innocent, nobody looks sinister.

LINEUP, left to right, all the same height with feet on one line, evenly spaced, the
attached character first as the reference:

1. The attached navy whale captain, reproduced as is.
2. KITSUNE: a fox in rust orange felt (#c8622a) with a cream muzzle and inner ears, two
   soft tails showing behind. Dining-car steward: charcoal waistcoat, white shirt, narrow
   black tie, a folded white napkin over one forearm, a small round pillbox cap. No mask.
3. AXOLOTL: coral pink felt (#e8899a), round head, three soft frilly gill fronds each
   side of the head like feathers, tiny dot nostrils. Telegraph clerk: pale striped shirt,
   dark sleeve garters, small bow tie, a dark green eyeshade visor.
4. LION CUB: golden felt (#d9a441), a short soft mane of felt curls in darker ochre
   around the face, small round ears, mouth closed, round eyes. Not a guardian lion, no
   teeth, no snarl. Engine driver: dark denim bib overalls, a mustard neckerchief, a grey
   flat cap, a small brass pocket watch chain.
5. MUSHROOM: a button-mushroom person, the dome cap is the whole head in ochre gold
   (#c9952b) with a few lighter stitched spots, eyes under the rim, a short cream stem
   body. The cap wears a hat band: a brown ribbon with a small enamel travel pin. No hat
   on top of the cap. Country traveler: a tweed travelling coat and a small leather valise.
6. TIN AUTOMATON: a wind-up toy robot in warm copper and brass (#b87333), painted seams
   and small rivets instead of stitching, a small wind-up key on the back, the same bead
   eyes and small smile as the others so it reads as a toy from the same box. Luggage
   porter: a leather luggage strap across the chest, a porter's round cap with a short
   brim, a brass luggage tag on the strap.
7. UNICORN: blush pink felt (#f0b4c0), a short cream horn, a short soft mane in cream.
   Lady passenger: a small cloche hat, a short travelling cape, a pearl button.

RULES FOR EVERY FIGURE: no magnifying glass, spyglass, medical items, weapons, badges,
masks, pelts or lanterns. No numbers or letters anywhere. No red, no violet or purple,
no cyan or turquoise as a body or costume colour. Costumes are 1920s train and travel
life only.
```

## Prompt 2, the base pose (attach the whale base and the approved lineup crop)

```
Portrait image 1024x1536, transparent background PNG, no text, no numbers.

One plush toy character, full body, standing facing front, centred, feet on the bottom
edge, the top of the hat or ears about 6% below the top edge, the body filling the frame
top to bottom. Same style, material, lighting and proportions as the attached whale
captain: felt and plush, stitched seams, one square felt patch on the head, glossy black
bead eyes with one highlight, big head about half the height, stubby body, round shoes,
soft light from the upper left with a gentle darker right side.

BASE POSE: eyes open, small closed smile, arms relaxed at the sides, one hand holding the
character's one small prop at chest height.

CHARACTER: [paste the character's line from the lineup prompt, adjusted to what was
approved on the sheet]

RULES: no magnifying glass, spyglass, medical items, weapons, badges, masks, pelts or
lanterns. No numbers or letters. No red, violet, purple, cyan or turquoise.
```

## Prompt 3, the other three poses (attach that character's approved base)

```
Portrait image 1024x1536, transparent background PNG, no text, no numbers.

Reproduce the attached plush character exactly: same character, same costume, same
colours, same prop, same size, same position in the frame, feet on the bottom edge, the
same lighting from the upper left. Change only the pose described below. Do not move,
rescale or recolour anything else.

POSE: [one of]
  TALKING: mouth open in a cheerful round "o", one hand raised beside the head with the
  palm out, three short cream motion lines next to that hand, the other hand still
  holding the prop.
  THINKING: one hand raised to the chin, one eyebrow slightly raised, mouth a small
  thoughtful line, and a small white felt thought bubble of three puffs rising above
  the head on the right side.
  OUT: eyes closed as two gentle downward arcs, a content closed smile, the same relaxed
  stance and prop as the base.
```

## Prompt 4, the head (attach the approved base)

```
Square image 1024x1024, transparent background PNG, no text, no numbers.

The attached plush character cropped to head and shoulders, centred, facing front, the
same base expression (eyes open, small closed smile), the same hat, patch, colours and
lighting. The head fills about 80% of the frame height, shoulders cut off at the bottom
edge. Nothing else in the frame.
```

## Round 2 (2026-10-03): narrowed to four, cuteness and costume pass

The first sheet (fox steward, lion engine driver, ochre mushroom, copper porter robot) read as a
family but: the fox and robot came out humanoid (head ~45%, legs visible, projecting snout, flat
tin face); all four costumes were the same brown/charcoal cloth; lion gold, mushroom ochre and
robot copper sat in one colour slot; the robot's side-on wind-up key read as a numeral 8; the
mushroom's pin carried lettering. The mushroom was the cutest because its features sit low under
the rim.

Cute formula to prompt for on every face: large bead eyes in the LOWER half of the head, wide
apart, one big highlight; tiny closed smile right under the eyes; dot nose or none; big plain
forehead; blush spots; no projecting snout; no neck; shoes directly under the torso.

Changes: fox gets a long cream apron + bow tie, no hat (the pillbox was the badger's), rounded
ears, flat cream face circle, two curled tails; lion gets a hickory-stripe engineer's cap and a
full pompom mane; mushroom cap goes blush pink (takes the pink slot freed by dropping the
axolotl/unicorn), plain ribbon band, tartan scarf; robot gets a dome head with a cream enamel face
plate, egg body, few rivets, no key, leather-brown porter cap.

Paste the blocks below over Prompt 1's STYLE block and lineup list. Generate the base poses one
character at a time: a lineup averages proportions across the row.

```
STYLE: match the attached plush toy character exactly. Soft felt and plush toy, visible
stitched seams, one small square felt patch stitched somewhere on the head, soft studio
light from the upper left with a gentle darker side on the right (noir mood from the
lighting only, never from the expression). Nobody smirks, nobody looks sinister.

FACE, identical on every character: two large glossy black bead eyes, each with one big
white highlight, placed in the LOWER half of the head and set wide apart; a tiny closed
smile directly under the eyes; a nose that is a tiny dot or absent; a large plain
forehead above the eyes; two faint blush spots on the cheeks. No projecting snout,
muzzle or jaw: faces are flat and round like the attached whale's.

PROPORTIONS, identical on every character: head about 58% of total height and wider
than the body; no neck; a tiny squat torso; no visible legs, the oversized round shoes
sit directly under the torso; short thick mitten arms. Cute first, dressed-up second.

LINEUP, left to right, all the same height with feet on one line, the attached
character first as the reference:

1. The attached navy whale captain, reproduced as is.
2. KITSUNE: rust orange felt (#c8622a) with a big cream circle covering the lower face
   and cream inner ears; ears short and rounded, not pointed; two plush tails with cream
   tips curling up either side of the body. Dining-car steward: a long cream apron from
   chest to shoes over a charcoal waistcoat, a black bow tie, a folded white napkin over
   one forearm. No hat. No mask.
3. LION CUB: golden felt (#d9a441) with a full round halo mane of soft felt pompoms in
   darker ochre around the whole face, tiny round ear nubs inside the mane; mouth
   closed, no teeth, no snarl. Engine driver: a hickory-stripe engineer's cap (narrow
   blue and white stripes), dark denim bib overalls, a mustard neckerchief, a small
   brass pocket-watch chain.
4. MUSHROOM: a button-mushroom person, the dome cap is the whole head in blush pink
   felt (#e8a0ae) with a few lighter cream stitched spots, eyes under the rim, a short
   cream stem body. The cap wears a plain brown ribbon hat band, no pin, no badge. No
   hat on top of the cap. Country traveler: a green and cream tartan scarf, a tweed
   travelling coat, a small leather valise.
5. TIN AUTOMATON: a wind-up toy robot in polished rose copper (#b87333), a round dome
   head with a large oval cream enamel face plate carrying the same bead eyes and tiny
   smile as the others; an egg-shaped rounded body with only a few small rivets at the
   seams; mitten hands. No wind-up key, no figure-eight shapes anywhere. Luggage porter:
   a soft round porter's cap in dark leather brown with a brass band, a leather luggage
   strap across the body, a small brass luggage tag.

RULES FOR EVERY FIGURE: no magnifying glass, spyglass, medical items, weapons, badges,
masks, pelts or lanterns. No numbers, letters or writing anywhere, including on pins,
tags and patches. No red, violet, purple, cyan or turquoise as a body or costume colour.
Costumes are 1920s train and travel life only.
```

## Round 3 (2026-10-03): costume rethink

Round-2 sheet: faces and proportions landed; pink cap cleared the gold clash. Owner: the fox
needs a small nose; the costumes read "lame"; the lion's profession (engine driver) is illegible;
the mushroom's tweed coat + green tartan scarf overlaps the polar bear (loden coat + green scarf);
the robot reads as a postman, keep that.

Ruled directions (alternates considered in brackets):
- Kitsune: Taisho-era traveller, black haori with white crests over cream kimono, striped hakama,
  closed charcoal oil-paper umbrella, furoshiki bundle; dot nose on the cream circle.
  [Taisho café girl kimono + frilled apron; ekiben seller with the box tray on a neck strap.]
- Lion cub: 1920s Egypt explorer, cream pith helmet, khaki safari jacket, rolled map; dot nose,
  tufted tail at the side. [Jazz trumpeter in cream suit + bowler; ringmaster, hatless.]
- Mushroom: aviatrix, flight goggles pushed up on the cap brim as its band, shearling jacket,
  cream silk scarf. [Scottish kilt + sash in cream/brown/pink tartan; pâtissière.] Goggles are
  not on the banned-prop list; swap to the kilt if the owner reads them as role-adjacent.
- Automaton: railway mail clerk, brown peaked postman's cap, mail satchel on a cross strap at the
  hip, bundle of blank envelopes.

```
2. KITSUNE: rust orange felt (#c8622a) with a big cream circle covering the lower face
   and a small black stitched dot nose at its centre, cream inner ears, ears short and
   rounded; two plush tails with cream tips curling up either side. Taisho-era traveller:
   a black haori jacket with three tiny white crests over a cream kimono, grey-and-white
   striped hakama, a closed charcoal oil-paper umbrella held upright at one side, a small
   furoshiki bundle. No mask.
3. LION CUB: golden felt (#d9a441), a full round halo mane of soft felt pompoms in
   darker ochre, tiny round ear nubs inside the mane, a small black stitched dot nose, a
   tail with a tuft showing at one side; mouth closed, no teeth. 1920s explorer back from
   Egypt: a cream pith helmet, a khaki safari jacket with a belt and flap pockets, a rolled
   parchment map tucked under one arm. No spyglass, no magnifying glass.
4. MUSHROOM: a button-mushroom person, the dome cap is the whole head in blush pink felt
   (#e8a0ae) with lighter cream stitched spots, eyes under the rim, a short cream stem
   body. Aviatrix: a pair of brass-rimmed flight goggles pushed up onto the cap's brim as
   its band, a brown shearling flight jacket with a cream fleece collar, a cream silk scarf
   trailing at one side. No hat on top of the cap.
5. TIN AUTOMATON: a wind-up toy robot in polished rose copper (#b87333), a round dome
   head with a large oval cream enamel face plate carrying the same bead eyes and tiny
   smile, an egg-shaped rounded body with a few small rivets at the seams, mitten hands.
   No wind-up key. Railway mail clerk: a dark brown peaked postman's cap with a brass
   band, a leather mail satchel on a cross strap hanging at one hip, a small bundle of
   blank envelopes tied with string in one hand, no writing on them.
```

## Round 4 (2026-10-03): kitsune geisha, lion soldier

Owner: the explorer also overlaps the polar bear (outdoorsy khaki/green traveller); wants the
kitsune geisha-inspired and the lion a 1920s soldier. Mushroom aviatrix (= 1920s woman pilot)
and automaton mail clerk stand.

Soldier caution: closest profession to a role hint (the vigilante shoots), and field khaki/olive
is the polar bear's loden. Ruled as a parade dress uniform in black with gold frogging, no weapon,
no medals, no insignia. Fallback if it still reads as a fighter: 1920s sportsman (cream flannels,
striped cricket sweater, tennis racket).

```
2. KITSUNE: rust orange felt (#c8622a) with a big cream circle covering the lower face
   and a small black stitched dot nose at its centre, cream inner ears, ears short and
   rounded; two plush tails with cream tips curling up either side. Geisha-inspired:
   a long black kimono patterned with small gold chrysanthemums, a wide gold obi tied in
   a large bow at the back, a dangling gold kanzashi hair ornament between the ears, a
   closed paper fan held at one side. No mask, no red lip, no face paint beyond the
   cream circle.
3. LION CUB: golden felt (#d9a441), a full round halo mane of soft felt pompoms in
   darker ochre, tiny round ear nubs inside the mane, a small black stitched dot nose, a
   tail with a tuft showing at one side; mouth closed, no teeth. 1920s parade soldier:
   a black high-collar dress tunic with gold braid frogging across the chest, white
   gloves, a black kepi cap with a gold band sitting on top of the mane. No weapon, no
   medals, no insignia, no belt across the body.
```

## The cast record (built 2026-10-03, commits 9f531eb..e9c82b0)

Ruled: a game's cast is a fact about the game, stored in tables, not recomputed. Owner wanted a
character table with a stable id and a link to the game; ruled slug as the id (`lionCub`, what the
sprites are filed under) with a separate display name (`shade` reads "Songbird"), no UUID.

- `characters(id, display_name, retired, added_at)` seeded with the eleven by migration 0008;
  `game_cast(game_id, seat, character_id, chosen)` with a unique (game, character) and FKs.
- The server draws the cast when the engine deals the seats (`GameSession._deal_cast`), lands each
  joiner's pick on the seat they were dealt, writes it once (retried with the next save), and a
  rebuilt game reads it back. `GET /games/{id}` (live and archived) and the replay carry `cast` in
  seat order; a waiting room's snapshot carries `characters` (picks aligned with `players`).
- Picking: `POST /games/{id}/character` in a room (first come first served; 409 taken/started,
  422 unknown, null gives up), `character` on the solo door's body, `GET /characters` catalogue.
- Frontend: `resolveCast(stored, gameId)` takes a whole stored cast this build can show, else the
  legacy hash over `LEGACY_CHARACTERS` (frozen eleven, in castForGame.ts; the manifest's list may
  grow). Old replays are therefore untouched.

Still to do: (1) DONE 2026-10-03, the sprite conversion for the four new characters (Pillow pass,
canvas, BODY and REACH, manifest imports; `scripts/convert_cast.py`); (2) DONE 2026-10-03, migration
0009 seeding kitsune, mushroom, lionCub, automaton into `characters` plus the four rows in the
server `CATALOGUE`, in the SAME commit as the sprites, so a character exists in the catalogue iff
its sprites ship; (3) DONE 2026-10-03 (merge 79e8d6b), the picker: on the boarding pass under the
name field (a pick is made before boarding and sent right after the join, since the platform scene
has no form; taken puppets dimmed with their holder's name; a pick lost to someone else, before
or after the join, keeps the pass up naming the puppet until another pick lands or the player
presses "Let the house draw", never a silent draw (owner ruling 2026-10-03); a game already begun lets them
go), on the solo ticket under the role cards, and the waiting platform
wears the picks (`castForRoom`). Not done: a real join against a live server; changing a pick from
the platform scene (a stage design question).

Open: the kitsune's thinking master leans ~25 px left of its base; registration split the
difference (head ~12 px left, feet ~10 px right of the base). A rerun of that one state with "keep
the head in exactly the same position and angle as the base" fixes it properly; re-convert with
`poetry run python scripts/convert_cast.py kitsune` afterwards.

Deploy: `poetry run alembic upgrade head` (0008 + 0009) before the new server starts.
