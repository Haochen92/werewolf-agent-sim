/**
 * The side slot's rules, in one place, so every scene lays itself out the same way
 * (beat sheet §12, "The slot"; handoff §2, "The transcript").
 *
 * The right side of the stage holds one thing at a time: the transcript drawer or the case
 * file (the File tab; `film`, its old name). While it holds either, the room is drawn narrower (the puppet slides left, the paint
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

/**
 * What the slot holds now. The file opens with the X-ray off too: then it holds only the
 * Record, the public claims and accusations (owner, 2026-10-04; it was the X-ray's alone).
 */
export function slotOf(p: Pick<Presentation, 'slot'>): SlotOccupant | null {
  return p.slot ?? null;
}

/** The slot holds something, so the room lays out beside it: `geometry(hud, sideOpen(p))`. */
export function sideOpen(p: Pick<Presentation, 'slot'>): boolean {
  return slotOf(p) !== null;
}

/**
 * The beats where the seated human is answering something, and the scenes that are their own
 * room at night: the drawer stops at the rail so the prompt (the ballot row, the plate, your
 * line to the pack) keeps the whole band. On a phone the prompts stop short of the slot (the
 * rooms' plates are centred in the room left of it), so the drawer runs full height there
 * (owner, 2026-09-26: it should fill the side; the pack's too since its chat moved into the
 * drawer, 2026-10-17).
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

/** The box at the foot narrows to the room: only a full-height drawer takes the band's right. */
export function bandNarrows(
  p: Pick<Presentation, 'slot'>,
  beat: Pick<SceneBeat, 'id' | 'scene'>,
): boolean {
  return slotOf(p) === 'drawer' && !atRail(beat);
}

/** The top strip's two tabs and its Reveal switch for a scene: pressed states from the presentation, presses to the container (and the replay's way back, the live game's door). */
export function stripButtons(p: Pick<Presentation, 'slot' | 'xray'>, slot?: SlotInput) {
  const reveal =
    slot?.onReveal || slot?.revealLocked !== undefined
      ? { on: p.xray, onPress: slot.onReveal, locked: !!slot.revealLocked }
      : undefined;
  return {
    file: slotOf(p) === 'film',
    transcript: slotOf(p) === 'drawer',
    onFile: slot?.onFile,
    onTranscript: slot?.onTranscript,
    back: slot?.back,
    reveal,
    leave: slot?.onLeave,
    sound: slot?.sound,
  };
}

/**
 * A seat tap that opens its case file, where one belongs (owner, 2026-09-29): with the X-ray
 * on, at a beat with no speaker (a vote, the count, the lynch, the morning, the night hub and
 * whole), when the container can open the file. Null elsewhere: a turn's wing opens read cards.
 */
/**
 * The scenes whose beats have no speaker, where `fileTap` makes the rail's cards open files:
 * the vote and the count, the lynch, the morning, the night hub and whole. The case file's
 * docket says so ("Tap a seat to open its file").
 */
export function tapsOpenFiles(beat: Pick<SceneBeat, 'scene' | 'id'>): boolean {
  return (
    ['vote', 'lynch', 'morning'].includes(beat.scene) ||
    beat.id === 'rnight.hub' ||
    beat.id === 'rnight.whole' ||
    // the opening's stop: each seat's file leads with what it wrote (2026-10-16)
    beat.id === 'day.opening-prepares'
  );
}

export function fileTap(
  p: Pick<Presentation, 'xray'>,
  slot: SlotInput | undefined,
  noSpeaker: boolean,
): ((seat: string) => void) | null {
  if (!p.xray || !noSpeaker || !slot?.onOpenFile) return null;
  return slot.onOpenFile;
}

/**
 * What the presses do to the presentation (the containers call these; the workbench writes the
 * result to its URL). The strip's two tabs, File and Transcript, only choose what the slot
 * shows: each brings its pane, or closes it if it is there. File opens with the X-ray off too,
 * on the Record, the seats' files greyed (owner, 2026-10-04). The X-ray itself is one switch
 * (the strip's Reveal, left of the tabs; owner, 2026-09-29, replacing bench 74's X-ray tab that
 * also brought the film): it leaves the slot as it is, and a file left open goes to the Record.
 */
export function pressTranscript(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return { xray: p.xray, slot: slotOf(p) === 'drawer' ? null : 'drawer' };
}

export function pressFile(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return { xray: p.xray, slot: slotOf(p) === 'film' ? null : 'film' };
}

export function pressXray(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return { xray: !p.xray, slot: p.slot };
}

/** The scenes from dusk to the morning report. */
const NIGHT_SCENES: readonly string[] = ['night', 'room', 'pack'];

/**
 * The wolves' night in the transcript (owner, 2026-10-17), for a seated wolf, live: the first
 * time the pack's room comes on stage on a night the transcript opens on the pack's lines alone
 * (`open`), and when that night is over it closes, its filters back to all (`close`). `opened` is
 * the night it last opened for: a reader who shut it, or ticked more, keeps that until dawn.
 */
export function packNightStep(
  beat: Pick<SceneBeat, 'scene' | 'day'>,
  wolf: boolean,
  opened: number | null,
): 'open' | 'close' | null {
  if (!wolf) return null;
  if (beat.scene === 'pack' && opened !== beat.day) return 'open';
  if (opened !== null && !NIGHT_SCENES.includes(beat.scene)) return 'close';
  return null;
}

/** What `packNightStep` does to the slot: the transcript in it, or out of it (a file stays). */
export function packNightSlot(
  p: Pick<Presentation, 'slot' | 'xray'>,
  open: boolean,
): Pick<Presentation, 'slot' | 'xray'> {
  if (open) return { xray: p.xray, slot: 'drawer' };
  return { xray: p.xray, slot: slotOf(p) === 'drawer' ? null : p.slot };
}

/** A seat's file opened from the stage: the pane shows File (only with the X-ray on). */
export function showFile(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return p.xray ? { xray: true, slot: 'film' } : { xray: false, slot: p.slot };
}

/**
 * The Record opened from the transcript's pointer ("Day 2's record is in the File →"): the
 * pane shows File, with or without the X-ray (the Record is public). Which page and the
 * Record's tab are the container's (`SlotInput.onRecordPick`, `onFileSeat`).
 */
export function showRecord(
  p: Pick<Presentation, 'slot' | 'xray'>,
): Pick<Presentation, 'slot' | 'xray'> {
  return { xray: p.xray, slot: 'film' };
}
