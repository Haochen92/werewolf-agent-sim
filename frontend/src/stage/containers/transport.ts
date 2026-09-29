/**
 * The replay's transport, the pure half: where the cursor lands when it steps, seeks or jumps
 * a chapter, how long a beat holds at each speed, and where to land when the X-ray toggle
 * re-cuts the beat list under it. No timers and no DOM here; the theatre component drives
 * a timer off `holdFor` and hands the results to the scene.
 *
 * One rule shapes it all: arrive still, play moving. Only a forward step animates; a seek, a
 * step back or a chapter jump renders the beat at rest (docs/beat_sheet.md §11).
 */
import type { MotionSpeed } from '@/stage/scenes/types';
import { chapterMarks } from '@/stage/beats/beatsFor';
import type { SceneBeat } from '@/stage/beats/types';

export interface Cursor {
  /** Index into the beat list. */
  index: number;
  /** Whether the scene should play the move into this beat, or land on it. */
  animate: boolean;
}

export const still = (index: number): Cursor => ({ index, animate: false });

export function stepForward(cursor: Cursor, beats: readonly SceneBeat[]): Cursor {
  if (cursor.index >= beats.length - 1) return cursor;
  return { index: cursor.index + 1, animate: true };
}

export function stepBack(cursor: Cursor): Cursor {
  return still(Math.max(0, cursor.index - 1));
}

export function seekTo(index: number, beats: readonly SceneBeat[]): Cursor {
  return still(Math.min(Math.max(0, index), Math.max(0, beats.length - 1)));
}

/**
 * Chapter jumps land on a chapter's first beat, still. Back goes to the start of the current
 * chapter when the cursor is inside it, and to the previous chapter's start when it is already
 * on the mark (the way a track button works).
 */
export function jumpChapter(
  cursor: Cursor,
  beats: readonly SceneBeat[],
  direction: 1 | -1,
): Cursor {
  const marks = chapterMarks(beats).map((m) => m.index);
  if (marks.length === 0) return still(cursor.index);
  if (direction === 1) {
    const next = marks.find((i) => i > cursor.index);
    return still(next ?? beats.length - 1);
  }
  const before = marks.filter((i) => i < cursor.index);
  return still(before.length ? before[before.length - 1] : 0);
}

/**
 * How long the beat holds the screen at this speed, or null for a beat that waits for the
 * viewer (a turn, the epilogue, the curtain: `holdMs` 0).
 */
export function holdFor(beat: SceneBeat, speed: MotionSpeed): number | null {
  if (beat.holdMs <= 0) return null;
  // fast halves the hold; anything else (an old 'skip' kept somewhere) plays at normal
  return speed === 'fast' ? beat.holdMs / 2 : beat.holdMs;
}

/**
 * The X-ray toggle re-cuts the list (beats appear or vanish), so the cursor is carried across
 * by what it was on: the same beat if it survives, else the first beat at or after its seq.
 * Either way the viewer lands still.
 */
export function carryAcross(
  cursor: Cursor,
  from: readonly SceneBeat[],
  to: readonly SceneBeat[],
): Cursor {
  const was = from[cursor.index];
  if (!was || to.length === 0) return still(0);
  const same = to.findIndex(
    (b) =>
      b.id === was.id &&
      b.seq === was.seq &&
      b.ordinal === was.ordinal &&
      b.subject === was.subject &&
      b.spoke?.actor === was.spoke?.actor &&
      b.spoke?.step === was.spoke?.step &&
      b.page?.index === was.page?.index,
  );
  if (same !== -1) return still(same);
  const after = to.findIndex((b) => b.seq >= was.seq && b.end >= was.end);
  return still(after === -1 ? to.length - 1 : after);
}

/** The label the transport shows: "Vote 3 · A chip is counted". */
export function transportLabel(beats: readonly SceneBeat[], index: number): string {
  const beat = beats[index];
  if (!beat) return '';
  const marks = chapterMarks(beats).filter((m) => m.index <= index);
  const chapter = marks.length ? marks[marks.length - 1].beat.chapter! : null;
  const where = chapter
    ? chapter.kind === 'over'
      ? 'Game over'
      : `${chapter.kind[0].toUpperCase()}${chapter.kind.slice(1)} ${chapter.n}`
    : '';
  return where ? `${where} · ${beat.label}` : beat.label;
}
