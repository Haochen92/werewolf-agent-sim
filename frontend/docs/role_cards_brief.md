# Role cards brief: the eight 1920s roles (draft 2026-10-07)

Status: DRAFT, revised 2026-10-07 after review. The three rulings in section 0 are the owner's;
the rest is proposed. The engine work for Phase 3 runs in
parallel; this brief only needs the role ids and sides, which `src/stage/roles.ts` already fixes,
and the sigil set, which `instruments/Sigil.tsx` already draws.

What a role card figure is, and how it differs from a cast puppet:

- The cast puppets (`cast_expansion_brief.md`) must never hint at a role. The role card figures
  are the opposite: the card tells the player what they are, so the figure carries the role's
  prop in plain view. The costume rule does not apply here; the six existing figures hold a
  magnifier, a bandage roll, a popgun, a scythe, a pitchfork.
- One rule ties the figure to the rest of the stage: **the figure holds what its sigil shows.**
  The sigil is on every card, chip and ledger row; the figure is the sigil made into a toy. The
  investigator's magnifier, the healer's cross, the vigilante's bullet and the reaper's scythe
  already do this. The eight new sigils were chosen on the bench on 2026-10-07, so the props
  are fixed before the figures are drawn.
- Side reads from colour and body, role reads from the prop. The two new wolf roles are wolves
  first: the grey wolf head with ears and small fangs, as the Grandma wolf, in a costume. A
  player dealt the Chanteuse must see "wolf" before "singer".

## 0. Rulings (owner, 2026-10-07)

1. **The side is "Town", not "Villagers".** The word goes everywhere the UI prints the side:
   `FACTION_NAME.villagers` in `roles.ts`, the four existing town cards' win lines and the
   wolf's in `card-text.ts`, the archive's "Won by", the filter chips, the ending box. The
   wire's `villagers` id stays until the engine renames it. This is a UI-wide change made once,
   with the engine's naming, not patched card by card. The Villager role itself is not dealt in
   the ten-seat game; "a town player" is the phrase for anyone on the town side.
2. **The Fortune Teller bets at the start of every night**, and learns whether the bet was right
   at the very end of the night's resolution. It is a night action, as the sheet's table says;
   the sheet's "bets lock when night starts" is read as "placed first, before anything resolves".
3. **The self-bet works:** it helps the Fortune Teller survive that night. The exact rule is
   decided later; the card says only that much.
4. **The Chanteuse is told when her block fell on a non-town player:** "it doesn't affect the
   target". She learns that player is not town; the leak is accepted so she does not repeat a
   block that never worked.
5. **The Fortune Teller's result can reveal a concealed role.** The sheet scores the role bonus
   correctly even when the Illusionist concealed the victim, so a two-point result tells her the
   hidden role. Accepted as a stated choice: one neutral player learning one hidden role.

For the engine (Phase 3), from these and the review: rule 4's feedback line; rule 5's result;
the self-bet's survival effect; and the rules prompt must tell an agent Sentinel or Trailseer
that a dead name at a door is a Necromancer's borrowed body, since the card's clause (section 4)
only reaches a human.

6. **The villager and wolf cards retire** with the ten-seat deal. They leave the landing's hand
   and the ticket's role picker (`ROLES` in `ticket/RoleCards.tsx`, the roles a solo player may
   ask to be dealt) when the engine deals the ten seats, not before, since today's engine can
   only deal the nine-seat set. Their sprites and card text stay: archived nine-seat replays deal
   them, and the stage draws a replay's cards from them.

Review points adopted the same day, two rounds (the reviews are in the chat record): the Sigilist in a cream
robe with green thread, the Illusionist in a rust cape, the Fortune Teller in a turban, the Necromancer's doll
raised to chest height with the set's closed-eye stitches, the head colour named biscuit, the
Sigilist and Investigator card lines corrected against the sheet.

## 1. The house style, read off the six

The six figures (`claude_artifacts/design/rasters/roles/`, masters 1024×1536 or 1145×1374,
shipped as 720×960 WebP) share these, and the new eight keep every one:

- Needle-felted wool, matte, visible fibres; stitched seams in cream thread; a running-stitch
  hem along the bottom edge; one small square felt patch low on the body with cross stitches at
  its corners; one cross-stitched mend on a cheek.
- The head: a plain egg in warm biscuit felt, clearly darker than the cream cloth and thread
  (the wolf's is grey with a cream muzzle), two black glass bead eyes with one highlight, a tiny stitched cat mouth (the "3" curve), no nose. Eyebrows only for
  attitude (the villager's frown, the wolf's raised brows); most have none.
- The body: a glove, a cone from shoulders to hem, no legs, no neck, two mitten arms with a
  stitched cuff. The egg itself is about 40% of the figure's height, measured without the
  headwear (a top hat or a tall cowl framed 3% from the top would otherwise shrink the head
  under it; the frame rule stays and the avatar offset absorbs the difference, as it does for the
  vigilante's feather). The figure is about two thirds as wide as it is tall. Less chibi than the
  cast; the cast's 60 to 65% head is wrong here.
- One headwear, one garment, one prop held in a mitten. Nothing on the floor.
- Colours are muted and vintage. Town figures wear earth tones (tweed brown, dusty blue,
  moss green, slate grey); the wolf wears the pack's rust red; the killer wears aubergine.
  Cream is cloth and thread, never skin.
  No pure red, no violet, no cyan, no writing anywhere.
- Soft warm light from above, a slightly darker right side, transparent background, no ground
  shadow, the figure centred, the headwear's top within 3% of the top edge, feet on the bottom
  edge.
- The avatar crop takes the top ~56% (`paint/role-kit.ts`), so the hat, the head and anything
  raised to shoulder height carry the identity; a prop held low will not show in the small card.

## 2. The lineup

| Id | Name | Side | Sigil (fixed) | Figure in one line |
|---|---|---|---|---|
| sentinel | Sentinel | Town info | candle in a chamberstick | night attendant on his rounds, candle raised |
| trailseer | Trailseer | Town info | two wingtip soles | tweed rambler with a pair of brogues over one shoulder |
| sigilist | Sigilist | Town kill | pyramid with an eye | cream-robed seal-keeper, green cap and sash, the pyramid-eye amulet shown flat and forward |
| chanteuse | Chanteuse | Wolves | rose bud | grey wolf cabaret singer, rust drop-waist dress, one rose |
| illusionist | Illusionist | Wolves | top hat and wand | grey wolf stage magician in a rust cape, ears through the top hat, wand up |
| necromancer | Necromancer | Lone killer (level 2) | marionette control cross | sallow, green-cowled puppeteer after Necrophos, a tiny doll on strings |
| speculator | Speculator | Neutral | two stacks of coins | silver pinstripe financier holding up a stack of gold coins |
| fortune_teller | Fortune teller | Neutral (level 2) | crystal ball on a claw stand | séance medium in a 1920s turban and fringed silver shawl, the ball on its stand |

Unchanged figures: healer, investigator, vigilante, serial killer. The villager and the plain
wolf retire with the ten-seat deal (ruling 6) and keep their figures only for archived nine-seat
replays.

Colour by side, from the stage tokens (`paint/materials.ts`): town earth tones as now; wolves
rust red on grey fur; the lone killer aubergine on the reaper (the necromancer wears Necrophos's green instead, by the owner's direction, and the card frame carries the side);
the neutral side is moon-silver cloth on slate with one gold accent (`benign` `#d5dce4`,
`benignFelt2` `#8d97a3`, `benignAccent` `#f0c24a`), so both neutral figures wear silver-grey
with gold.

## 3. The figures

Each entry: the idea, then what the model is asked for (headwear, garment, prop, colours,
pose), then the choices still open. Props are the sigils; the open choices are about everything
else.

### Sentinel (town info)

The sleeping-car attendant making his rounds at night, who sets a candle at one door and sees
everyone who passes its light.

- Headwear: a flat-topped attendant's cap, midnight blue with a cream band, no badge.
- Garment: a long double-breasted greatcoat in midnight blue (not navy toward cyan; a dark
  slate-blue), two rows of cream stitched buttons, a cream muffler at the neck.
- Prop: a brass chamberstick, saucer with a finger loop, a short cream candle, a small felt
  flame, held up in the right mitten at shoulder height so it survives the avatar crop. The left
  mitten cups toward the flame.
- Colours: slate-blue, cream, brass. The healer already owns dusty blue; this is darker.
- Open: cap versus a nightcap with a tassel (cosier, but the vigilante's hat already slouches).

### Trailseer (town info)

A rambler who follows one trail through the night to its door. The sigil is two wingtip soles,
so the figure carries the shoes themselves.

- Headwear: a tweed flat cap, mustard herringbone.
- Garment: a belted Norfolk jacket in the same mustard herringbone, a cream scarf tucked in.
  The investigator's tweed is grey-brown; this is warmer and yellower so the two tweeds never
  read as one.
- Prop: a pair of two-tone wingtip brogues (cream and tan) tied by their laces and slung over
  the right shoulder, the soles facing out, so the sigil's two soles show at the crop.
- Colours: mustard, tan, cream.
- Taken on review: over the shoulder, so the soles sit inside the avatar crop; held by the
  laces they hang below it.

### Sigilist (town kill)

A keeper of seals who marks a door with a sign; whoever strikes from behind it answers for it.
The sigil is the two-tone pyramid with an eye.

- Headwear: a low round pillbox cap in bottle green with the pyramid-eye embroidered on its
  front in gold. The emblem appearing twice has a precedent: the healer's cross is on the
  kerchief and the apron.
- Garment: a long robe in warm, undyed, flecked oatmeal leaning tan, never grey, with a gold
  chevron at the chest and a bottle-green sash. The only warm pale body in the set (the two
  neutrals are pale too, in cool moon-silver; the pair separates by temperature, and the lineup
  step checks the Sigilist beside the Speculator for exactly that). Green is confined to the cap
  and sash so the figure never pairs with the Necromancer's green robe at tile size (review,
  2026-10-07: the two had the same read, a dark robe and a raised mitten with something hanging
  from it).
- Stitching: on this robe the set's cream thread would vanish, so the seams, the running-stitch
  hem and the cuffs are in bottle-green or tan thread, and the square patch is bottle-green felt
  with cream cross stitches. The cheek mend stays cream on the biscuit head.
- Prop: the pyramid-eye amulet, a felt two-tone pyramid with a stitched eye, held flat and
  forward in the right mitten at the upper chest, just under the chin, as one shows a seal, so it
  sits inside the avatar crop (chest height on a cone body straddles the 56% line); not hung from
  its chain.
- Colours: warm oatmeal, bottle green, gold.
- Open: a lit match in the other mitten for "your sigil never burned" (a second prop; the
  house rule is one).

### Chanteuse (wolves)

The cabaret singer who kept you at her table all night. A wolf in a dress, as Grandma is a wolf
in a bonnet.

- Head: the Grandma wolf's grey head, ears up, cream muzzle, two small fangs in the smile.
- Headwear: a cream beaded headband with one short plume, the rose bud tucked at the side.
- Garment: a rust-red drop-waist dress (the pack's rust, as the Grandma dress), a cream feather
  boa over the shoulders, a long string of cream pearls.
- Prop: one long-stemmed rose held across the chest in the right mitten; the bud is the sigil.
  The left mitten raised, open, as if holding a note.
- Colours: wolf grey, rust red, cream, one dark rose.
- Open: boa versus a fur stole (the stole is pelt, and pelt on a wolf reads wrong).

### Illusionist (wolves)

The stage magician whose trick makes a body's secret vanish with the body.

- Head: the same grey wolf head; the ears poke through two slits in the hat.
- Headwear: a black top hat with a rust band, ears through it.
- Garment: a short rust-red cape (the pack's rust on the body, so the side reads from the
  cloth as the brief's rule says) with a black lining showing at the front, a cream bow tie, a
  black waistcoat under the cape.
- Prop: a black wand with cream tips held up in the right mitten at head height. The sigil is
  the top hat with the wand leaning across it; the figure wears the hat and holds the wand.
- Colours: rust red, charcoal black, cream, wolf grey.
- Open: cape versus tailcoat (the tailcoat needs a body with legs; the cone body suits the cape).

### Necromancer (lone killer, level 2)

The owner's direction (2026-10-07): closer to Dota 2's Necrophos. What carries Necrophos is the
sallow grey-green skin, the tall pointed cowl with its high collar, the gaunt chest, the dark
green cloth with a sickly yellow-green light about it, and a ragged hem. What does not carry
over is the scythe (the reaper's), the glow and the sunken-eyed menace; the felt set has no
glow and every face is a toy's. Nothing in the set changes for him: felt, cream stitching, the
square patch, the cheek mend, bead eyes, the cat mouth, the glove body, one prop, the same
light and framing. The reaper is the figure to keep him apart from: the reaper's hood is round
and aubergine and its scythe is held high; this hood is pointed and green and the hands hold
strings.

- Head: the biscuit egg with a sallow olive cast, a shade greener and paler than the others'
  (the set already allows another head colour: the wolf's is grey). Bead eyes set a little lower than the others' with a
  faint darker felt shadow under each, the only hint of the sunken look. The cat mouth stays.
- Headwear: a tall pointed cowl in dark forest green that rises above the head and falls
  behind, with a high collar standing up to the chin; the cowl's edge bound in a muted
  chartreuse stitched trim, the one place his sickly light lives. Not the reaper's rounded hood.
- Garment: a long dark forest-green robe, the hem cut ragged (the running stitch follows the
  ragged edge), a bronze clasp and a narrow bronze shoulder piece on one side. On the chest, a
  gaunt ribcage stitched in cream thread over the green, as a toy's idea of his bony frame.
- Prop: the marionette's control cross, held up high in the right mitten, three short cream
  strings down to a tiny grey felt figure hanging limp at chest height beside the body, inside
  the avatar crop. The doll has the set's egg head with the puppets' "out" face, two closed-eye
  stitches and a flat mouth, the mark the stage already uses for a dead toy; never X eyes, which
  would be new vocabulary. The sigil fixes the prop; Necrophos lends the body, not the weapon.
- Colours: dark forest green, olive-cream skin, muted chartreuse trim, bronze; a grey-green
  patch. Yellow-green, never toward cyan or turquoise.
- Trade recorded: the figure's cloth no longer rhymes with the reaper's aubergine; the two lone
  killers rhyme by the hood instead, and the card's frame carries the side as it does for every
  town figure in a different colour.
- Taken on review: the ribcage (the bottles were a second prop in all but name); the chartreuse
  stays on the cowl's edge only, since chartreuse strings would vanish against the green.

### Speculator (neutral)

The financier who backs a side like a stock and collects if it pays. Nineteen twenty-nine is in
the air.

- Headwear: a pale grey homburg with a slate band.
- Garment: a silver-grey pinstripe waistcoat and jacket (moon-silver cloth, thin slate stripes),
  a slate cravat, a gold watch chain across the waistcoat.
- Prop: a stack of gold coins held up in the right mitten at shoulder height, the top face
  bright; a second, shorter stack tucked in the left mitten at the waist so both of the
  sigil's stacks are present.
- Colours: moon-silver, slate, gold.
- Open: a ticker-tape ribbon trailing from a pocket (a second prop, and it invites writing).

### Fortune teller (neutral, level 2)

A séance medium who reads tomorrow's news in tonight's glass. Deliberately the parlour
clairvoyant of the 1920s, not the carnival stereotype: no coin-fringed headscarf, no hoop
earrings.

- Headwear: a 1920s evening turban, the soft wrapped cloth of the period in moon-silver felt,
  a gold brooch at the front holding one short white plume. Rounder and taller than the
  Chanteuse's headband, so the two do not share a hat at tile size.
- Garment: a slate dress under a long fringed shawl in moon-silver, the fringe in gold thread,
  a gold brooch at the shawl's clasp.
- Prop: the crystal ball on its claw stand, the left mitten under the stand so the stand shows
  as the sigil draws it, the right mitten raised open beside the glass; a pale swirl inside and
  one stitched star on the glass.
- Colours: moon-silver, slate, gold, a pale glass.
- Open: nothing; the headband and the two-mitten hold were dropped on review.

## 4. The card text

The words the card says, in the register of `card-text.ts` (the front line wry and short, the
back three plain sentences). The side is "the town" (ruling 1), so the town win lines read
"With the town" and the wolf's counts "the town"; the four existing town cards and the wolf's
change the same words. Town win lines say "the lone killer" rather than "the serial killer",
because the necromancer takes that seat at level 2. The lines were checked against the role
sheet on review; the corrections are noted after the block.

```ts
sentinel: {
  name: 'Sentinel',
  line: 'Lights one candle at one door,\nand counts who passes.',
  day: 'You hold names, not verdicts. A visitor at a victim\'s door is a lead; say when you saw it and let the room weigh it. A dead name at a door is no ghost: someone is working the body.',
  night: 'Watch one player. In the morning you learn the names of everyone who visited them.',
  win: 'With the town, when both the wolves and the lone killer are gone.',
},
trailseer: {
  name: 'Trailseer',
  line: 'Follows one trail through the night,\nall the way to the door.',
  day: 'Where someone went is a fact; why is for the room to argue. Pair your trail with the Sentinel\'s names and the morning report.',
  night: 'Follow one player. You learn who they visited, or that they visited no one.',
  win: 'With the town, when both the wolves and the lone killer are gone.',
},
sigilist: {
  name: 'Sigilist',
  line: 'Marks a door with a sign.\nWhoever strikes from it answers for it.',
  day: 'Your sigils are few; spend them where the talk points. A miss means only that your target struck no one with their own hand that night.',
  night: 'Place a sigil on one player, two in the game. If they attack anyone tonight, your sigil strikes them back afterwards; the victim still dies. The serial killer survives it, and you learn they attacked.',
  win: 'With the town, when both the wolves and the lone killer are gone.',
},
chanteuse: {
  name: 'Chanteuse',
  line: 'Keeps one guest at her table\nuntil the night is over.',
  day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
  night: 'Talk with your packmate and choose the kill. Then keep one player at your table all night: a town player\'s act comes to nothing, and they learn they were held, not by whom. Anyone else is unaffected, and you are told so.',
  nightAlone: 'Choose one player to kill, then keep one player at your table; only a town player is held. You hunt alone now.',
  win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
},
illusionist: {
  name: 'Illusionist',
  line: 'Makes a body\'s secret\nvanish with the body.',
  day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
  night: 'Talk with your packmate and choose the kill. Twice in the game you may conceal the victim\'s role from the morning report; you learn it yourself.',
  nightAlone: 'Choose one player to kill, and conceal if you still can. You hunt alone now.',
  win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
},
necromancer: {
  name: 'Necromancer',
  line: 'Pulls the strings\nof those already gone.',
  day: 'Blend in as an ordinary town player, neither dominating the talk nor vanishing from it. The vote can remove you; from the second night, so can a bullet.',
  night: 'Night 1: nothing, and nothing can kill you. From Night 2: pick a dead, unconcealed player and use their night ability on one target, never the same body two nights running.',
  win: 'Alone, when at most one other player is left alive.',
},
speculator: {
  name: 'Speculator',
  line: 'Backs a side like a stock.\nCollects if it pays.',
  day: 'Watch which side is pulling ahead. Once your pick is announced, keep that side winning and keep yourself alive.',
  night: 'Pick the side you think will win, at the latest on the night after Day 2. The next morning announces the pick, not your name.',
  win: 'When the side you picked wins and you are still alive.',
},
fortune_teller: {
  name: 'Fortune teller',
  line: 'Reads tomorrow\'s news\nin tonight\'s glass.',
  day: 'Nobody fears you and nobody needs you. Listen for who the night will take, and keep your own name out of it; the vote never pays.',
  night: 'As the night begins, bet on who dies tonight: one point for the player, two for the player and their role. Or, twice in the game, bet on yourself, which scores nothing but helps you live through the night. You learn how the bet went once the night is over.',
  win: 'Once you hold two points, whether or not you live to see the end.',
},
```

The Speculator's lines follow the owner's ruling that its pick is a night action (2026-10-07).

Corrections taken on review, against the sheet: the Sigilist's strike is an attack, so night
immunity and a healer's protection stop it, and a miss says only that the target struck no one
with their own hand (the wolf who let its packmate carry, and a Necromancer working through a
borrowed body, both give a miss; "carried" is wolf-chat vocabulary a Sigilist never sees); the
Chanteuse keeps "one player", since she cannot see sides, and the card says what she is told
on a non-town pick (ruling 4); the Fortune Teller's bet is placed as the night begins and
answered at its end, so her day line points at the night only, and the self-bet is named for
what it does (rulings 2 and 3); the Sentinel's day line explains a dead name at a door, which
a borrowed body produces.

Existing cards that change their words with the engine: the investigator's night line becomes
"Check one player. Suspicious or Not suspicious. Wolves read suspicious, and so does the
Necromancer on a night it attacks; the Serial Killer never does" (named roles, since at level 1
the lone killer is the serial killer and "the lone killer" would contradict itself); the four town win lines take "the town" and "the lone killer";
the wolf's win line takes "the town". The villager card is not dealt in the ten-seat game and
keeps its text apart from the side's name.

## 5. The prompt (shared blocks, then one figure per call)

Modelled on the cast brief's method, with the figure style in place of the chibi plush: a
lineup first to judge colour and silhouette, then one figure per call with two existing figures
attached as the style anchor. No states: a role figure has one pose.

```
STYLE: a handmade needle-felted wool figure, matte with visible fibres, stitched seams in
cream thread, a running-stitch hem along the bottom edge, one small square felt patch
stitched low on the body, one cross-stitched mend on a cheek. [sigilist: the seams, hem
and cuffs in bottle-green or tan thread, the patch in bottle-green felt with cream cross
stitches, so the stitching shows on the pale robe.] Soft warm studio light from
above, a slightly darker right side. No text, letters or numbers anywhere.

HEAD: a plain egg head in warm biscuit felt, darker than the cream cloth and thread, no nose; two black glass bead eyes each with one
highlight; a tiny stitched cat mouth. No eyebrows unless the figure is given an attitude.
[wolf roles: a grey wolf head with upright ears, a cream muzzle, two small cream fangs in
the smile, as the attached Grandma wolf.]

BODY: a glove body, a cone from the shoulders to the hem, no legs, no neck, two mitten
arms with stitched cuffs. The egg head alone, not counting any hat or cowl, is about 40% of
the figure's height, and the figure is about two thirds as wide as it is tall. One headwear, one garment, one prop held in a mitten.
Plain rounded mittens with no thumb or fingers. The figure ends at the hem: no feet, boots,
base or shadow below it. Exactly one cross-stitched mend, on one cheek. No blush, no eyelids,
no lashes. Every object is felt, thread or a brass fitting: a flame is a felt flame, a gem a
felt gem; nothing glows and nothing is real fire or glass except the crystal ball.

PALETTE: muted vintage felt. No pure red, no violet or purple, no cyan or turquoise.
[town: earth tones] [sigilist: a warm, undyed, flecked oatmeal robe leaning tan, never grey;
bottle-green cap and sash; gold] [wolves: rust red on grey fur] [serial killer: aubergine]
[necromancer: dark forest green, a sallow olive cast on the biscuit head, muted chartreuse trim, bronze]
[neutral: moon-silver and slate with one gold accent]

STEP 1, LINEUP (investigator and wolf attached): landscape 1536x1024 on plain dark brown
#1a120c, the eight new figures left to right in the lineup order of section 2, all one
height, feet on one line, the two attached figures at the ends for scale. Judge colour,
silhouette and the hats here only; in particular the Sigilist beside the Speculator, warm
oatmeal against cool moon-silver.

STEP 2, ONE FIGURE (investigator, wolf and the lineup attached): portrait 1024x1536,
transparent PNG. The shared blocks, then "Reproduce figure N from the sheet (the <role>)
exactly. One figure, full body, facing front, centred, feet on the bottom edge, the top of
the headwear about 3% below the top edge. <the figure's entry from section 3>."

GATE on the alpha box: the headwear's top within 3% of the top edge, the feet on the bottom
edge, width over height between 0.63 and 0.75 (the shipped sprite is 3:4 with the figure at
full height, so a box wider than 0.75 is cut at the sides; the healer, at 0.74, fills 99% of
the width and is the limit), nothing touching the side edges. Measure
the egg: about 40% of the figure's height, not counting the hat (a top hat or a tall cowl
shrinks the egg under it; the avatar offset in role-kit.ts absorbs it). Then check the
avatar crop: the top 56% must show the headwear, the prop, and for the Necromancer the doll.
```

Habits seen in the first generations (2026-10-07), which the block above now forbids: a dark base
or boots under the hem (Illusionist, Trailseer, Sentinel), a thumb on the prop hand
(Illusionist, Chanteuse, Fortune Teller), a second cheek mend (Fortune Teller, Sigilist), blush
and eyelids (Necromancer), a real flame (Sentinel), and a metal Egyptian-styled inverted
pyramid for the Sigilist (the Millennium Puzzle, an identifiable object from another property;
the sigil's pyramid is upright, two-tone felt).

Toy wording where a word could trip a filter: the vigilante's gun was a "popgun"; here nothing
is a weapon, but "crystal ball" and "marionette" are fine as toys and "amulet" is a pendant.

## 6. Shipping a figure

Shipped 2026-10-07: all eight, through `scripts/fit-role-figures.mjs` (the fit below, written
down for the first time; it refuses to overwrite an existing sprite without `--force`). The
default avatar crop carries each figure's prop, so none needed an offset.

The same path as the six (stage_architecture §4): the master PNG, portrait 1024×1536 as the
model outputs it, to `claude_artifacts/design/rasters/roles/<id>.png` (gitignored); then fitted
to the 720×960 sprite the way the six were (measured 2026-10-07: the alpha box is trimmed, the
figure scaled to the full 960 height, feet on the bottom edge, centred on the width, so the
master's own margins and size do not matter and only its box proportion does), written as WebP at
`src/assets/sprites/roles/<id>.webp` plus the `@small` tile, 180×240 (`scripts/small-sprites.mjs`, 0.25),
then the manifest's `RoleSprite` union and its `roles` and `roleTiles` maps, an avatar offset in
`paint/role-kit.ts` if the hat or prop sits off the centre line (the vigilante's feather, the
reaper's hood), and the entry in `card-text.ts`. The ids are the engine's style and already in
`roles.ts`; `fortune_teller` follows the engine's word when it lands.

## 7. Open for the owner

Resolved on review, 2026-10-07: grey wolf heads for the two wolf roles; the séance medium in a
turban; the ribcage and the cowl-edge chartreuse; the brogues over the shoulder; "the lone
killer" in the town win lines; and the four defaults confirmed in the second round: no
match for the Sigilist, the boa for the Chanteuse, the cap for the Sentinel, the cape for the
Illusionist.

Still open: the self-bet's exact rule, decided later with the engine; the card's wording is
written to survive whichever rule lands.
