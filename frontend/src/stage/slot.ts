/**
 * The side slot's rules, in one place, so every scene lays itself out the same way
 * (beat sheet §12, "The slot"; handoff §2, "The transcript").
 *
 * The right side of the stage holds one thing at a time: the transcript drawer or the X-ray
 * film (the File tab). While it holds either, the room is drawn narrower (the puppet slides left, the paint
 * and the lights follow) and the wing stays where it is. The two differ below the rail:
 *
 * - the drawer is a long scroll, full height, so the box at the foot moves in under the
 *   puppet and narrows, keeping its pages (the full line is in the drawer);
 * - the film stops at the rail (nothing in it repeats the speech), so the box keeps the band;
 * - on the seated human's own turn (a prompt), the drawer stops at the rail too, so the
 *   prompt keeps the whole width.
 */
import type { BeatId, SceneBeat } from './beats/types';
import type { Presentation, SlotInput } from './scenes/types';

export type SlotOccupant = 'drawer' | 'film';

/** What the slot holds now: the film only exists with the X-ray on. */
export function slotOf(p: Pick<Presentation, 'slot' | 'xray'>): SlotOccupant | null {
  if (p.slot === 'film') return p.xray ? 'film' : null;
  return p.slot ?? null;
}

/** The slot holds something, so the room lays out beside it: `geometry(hud, sideOpen(p))`. */
export function sideOpen(p: Pick<Presentation, 'slot' | 'xray'>): boolean {
  return slotOf(p) !== null;
}

/**
 * The beats where the seated human is answering something, and the scenes that are their own
 * room at night: the drawer stops at the rail so the prompt (the ballot row, the plate, the
 * pack's chat) keeps the whole band.
 */
const PROMPTS: readonly BeatId[] = [
  'day.your-turn',
  'vote.your-ballot',
  'room.opens',
  'pack.your-line',
  'pack.vote',
];

export function atRail(beat: Pick<SceneBeat, 'id' | 'scene'>): boolean {
  return PROMPTS.includes(beat.id) || beat.scene === 'room' || beat.scene === 'pack';
}

/**
 * Where the rail stop holds even on a phone. On a phone the car's prompts (the ballot, the
 * dock) and the own room's plate (centred in the room left of the slot) stop short of it, so
 * the drawer may run full height there (owner, 2026-09-26: it should fill the side); the
 * pack's chat still spans the band's right, under the slot, so the pack keeps the rail.
 */
export function railHolds(beat: Pick<SceneBeat, 'scene'>): boolean {
  return beat.scene === 'pack';
}

/** The box at the foot narrows to the room: only a full-height drawer takes the band's right. */
export function bandNarrows(
  p: Pick<Presentation, 'slot' | 'xray'>,
  beat: Pick<SceneBeat, 'id' | 'scene'>,
): boolean {
  return slotOf(p) === 'drawer' && !atRail(beat);
}

/** The top strip's two tabs for a scene: pressed states from the presentation, presses to the container (and the replay's way back). */
export function stripButtons(p: Pick<Presentation, 'slot' | 'xray'>, slot?: SlotInput) {
  return {
    xray: p.xray,
    file: slotOf(p) === 'film',
    transcript: slotOf(p) === 'drawer',
    onFile: slot?.onFile,
    onTranscript: slot?.onTranscript,
    back: slot?.back,
  };
}

/**
 * What the presses do to the presentation (the containers call these; the workbench writes the
 * result to its URL). The strip's two tabs, File and Transcript, only choose what the slot
 * shows: each brings its pane, or closes it if it is there. File needs the X-ray (the film is
 * the X-ray's), so without it the tab is greyed and does nothing. The X-ray itself is one switch
 * (the replay's band): off takes the film with it, and the slot falls back to the transcript
 * (owner, 2026-09-29, replacing bench 74's X-ray tab that also brought the film).
 */
export function pressTranscript(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return { xray: p.xray, slot: slotOf(p) === 'drawer' ? null : 'drawer' };
}

export function pressFile(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  if (!p.xray) return { xray: p.xray, slot: p.slot };
  return { xray: true, slot: slotOf(p) === 'film' ? null : 'film' };
}

export function pressXray(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  if (!p.xray) return { xray: true, slot: p.slot };
  return { xray: false, slot: p.slot === 'film' ? 'drawer' : p.slot };
}
