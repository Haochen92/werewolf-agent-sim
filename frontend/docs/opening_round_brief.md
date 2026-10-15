# The opening round's screen — a brief for one painting

Live testing, 2026-10-11: while everyone writes their opening, the stage shows the empty table
and a walnut notice ("Everyone is writing their opening."). The owner wants a screen of its own
there and offered to generate the raster. This brief says what to paint and where it goes, so the
picture drops into the pipeline the night rooms already use.

## What the screen is

The seat's own compartment by day, at its writing table: the passenger is composing their opening
line before the first round of talk. The same picture serves every seat and every role (a role's
props would leak nothing, but there is no need for twelve paintings: the writing is the subject).
It shows at `day.opening-prepares` (beat sheet §2 row 7) for everyone, and under the dock during a
human's own opening turn (§2 row 11, the `opening` head), where the composer sits over its lower
half. On the sweep rounds (proactive, closing) nothing changes.

## The plan to paint on

The night rooms' plan, by day (`docs/night_rooms_brief.md` §2; the plan file is
`claude_artifacts/design/rasters/refs/compartment-night.png`, 1536×1024). Keep all of it: the
camera, the canvas, the walnut panelling, the brass rack, the carpet, the rounded brass window at
the right with its glass **empty** (white or transparent; the stage draws the day's country behind
it), the fold-down table under the window.

What differs from a night room:

- **Daylight.** Lit from the window, not from a table light: cool day on the right wall and the
  table, warm walnut in the room. No flame, no lamp lit; a cold table lamp may stand there.
- **The table is dressed for writing**: a sheet of paper with a few lines begun, a fountain pen,
  an inkwell or a pencil, perhaps a folded timetable. The paper sits on the table's right half;
  the **left half of the table stays clear** (the stage stands the role card there, 200 units
  tall, as in every room).
- **The upper middle wall stays clear** (x ≈ 280 to 835 of the master, from the rack down to the
  rail at y ≈ 570): the stage may hang the day's photo line there later; nothing tall in it.
- **Nobody in the picture.** The passenger is the viewer. No hands, no figure.
- Nothing in front of the glass, nothing over the rack's lowest rail.

One master, PNG, 1536×1024, saved as `claude_artifacts/design/rasters/rooms/opening.png`.

## How it ships

`node scripts/fit-night-rooms.mjs opening` clears the glass and cuts the band the stage uses, and
prints the glass rect and the table's brightest point for `ROOMS` in `paint/compartment.ts` (for a
day room the "light" entry is the paper's brightest point; the room's `warm` colour is a pale day
tone). The manifest gets `rooms.opening`; the day scene mounts the room picture for the two beats
above the way the night rooms mount theirs, with the day's country behind the glass. The walnut
notice goes; the dock keeps its words. A phone keeps the room still (no motion at rest).

## Acceptance

Both beats on the workbench (`/workbench/day`, the opening situations) at 1600×900 and in the
iPhone frame; the card's clear spot and the composer not covering the paper's lines; the
phone-rule test green (the room must not remount between the prepares beat and the human's turn).
