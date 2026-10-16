# Typography: three voices, three props

Ruled with the owner on 2026-10-16 (the type review, worked out on a mock with a switch per
change: https://claude.ai/artifact/XomZwHAP9xuq5ahhWcsWuC). One set of faces serves the site and
the theatre. This file is the rule; `src/theme/fonts.ts` and `src/stage/fonts.ts` load the faces.

**Status: ruled, not yet built.** Until the build lands, the code still has Young Serif on the
stage, Outfit in the landing's speech samples, system mono in two typed notes, and the story in
the hero. The build order is at the end.

## The six faces

**The voices** speak wherever their job is:

| Face | Job | Where |
|---|---|---|
| EB Garamond (600) | signs and titles | the landing's name and its tagline, every page and section title, the nav's name and Guide sign, the plate buttons, the theatre's big signs (day plaque, nameplate, seat tab, "Your turn to speak", the drawer's titles) |
| Literata | the voice of the world | the story, everything a passenger says (the stage's speeches, the transcript, the landing's speech samples), and the theatre's small text and controls (600) |
| Outfit | the site explaining itself | explanations, the product, the research, the site's controls and its small labels |

**The props** belong to one object each and never set interface text:

| Face | The object | Where |
|---|---|---|
| IM Fell English | printed paper | tickets, the feature cards, the slates, the case file's titles, the puppets' seat numerals |
| Courier Prime | the typewriter | every typed note (the case file's labels and stamps, the landing's typed lesson and private notes) |
| Patrick Hand | pencil | the case file's margin, the lesson's reasoning, "Your notes" |

Machine text (ids, keys) uses the device's monospace, which is not a downloaded face.

Retired: **Young Serif** (2026-10-16). It was the theatre's engraved voice (stage_architecture §5,
2026-09-29); its big signs go to Garamond and its small text to Literata 600, because Garamond
600 at the theatre's small sizes (a seat number, a day tab, "Pass" on a laptop) came out thin on
brass.

## Which voice: the test

On the site there are two voices for running text: the world, and the site explaining it. The
test is **would this sentence make sense if the train were real?**

- "Every passenger has a story to tell, and a secret worth protecting": yes, so Literata.
- "When the journey ends, Reveal lets you glimpse their private notes": no (Reveal is a button),
  so Outfit, even though it opens in the story's voice.

In the theatre you are inside the train, so Literata carries nearly everything. Speech and
controls share it and part by weight: speech at 400, controls at 600. Outfit stays only where a
plate still names it.

## Sizes, weights, wrapping

- Titles are Garamond 600; the hero's name is the biggest of them, so the hierarchy is size, not
  a change of family.
- Headings small enough to be labels (about 20px, "Latest games") stay Outfit 600.
- Small uppercase labels ("Day 2 · Seat 10", "Its private notes", "Your notes", "Followed") share
  one style: Outfit 600, 11px, 0.14em tracking. Each keeps its own colour.
- Garamond's lowercase is small: set it a touch larger than Outfit at the same job, and never on
  brass below the theatre's big signs. The theatre's signs are scaled by `--display-scale`
  (1.08, Stage.module.css), so they keep the presence Young Serif had at the same size.
- Headings wrap with `text-wrap: balance`, paragraphs with `text-wrap: pretty`, so no line ends
  on one word.
- Hero text stays muted and centred: under the title, not competing with it.

## Numbers

Signs and controls in the theatre (seat numbers, the clock, counts, "Day 3", "No. 10") use
`font-variant-numeric: lining-nums tabular-nums`: every digit the height of a capital and the same
width, so seats 6 and 9 sit level and the clock does not shift as it counts. Numbers inside
sentences (a speech's "seat 5") keep the face's own figures, which sit with the lowercase.

## The build

1. This file, and the pointers to it in site_architecture.md and stage_architecture.md §5.
2. The faces: Young Serif out of `stage/fonts.ts` and Garamond in; Literata and Courier Prime
   wherever the site uses them outside a stage; the speech samples to Literata, the two typed
   notes to Courier Prime, the guide's story to Literata, the labels to one style, the numbers.
3. The landing's hero: the name as title and the hook as its tagline, the title lower (about
   150px under the nav on a desktop, 64px on a phone), the wall lamps hung level with the name
   from the title's own position.
4. The story: out of the hero, into the reading room after the train (its granite raised to take
   it, the room running on into "What makes it different"), on the wall with no paper, under one
   light hung level with the start of the features.
