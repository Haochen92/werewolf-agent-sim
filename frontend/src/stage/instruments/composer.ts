/**
 * The full-screen composer's rules (beat sheet §12): the speaking turn's line written in a box
 * as big as the screen, opened from the dock's keyboard button, or by a tap on the dock's small
 * box on a phone. It holds the same line as the dock (the container's `dock.text`), so these are
 * only what the composer adds: when it is open, where it sits, and the word count.
 */
import type { DockInput } from '../scenes/types';

/** A frame this wide or narrower (css px) is a phone: a tap on the small box opens the composer. */
export const PHONE_MAX = 900;

/** The media query for `PHONE_MAX`. */
export const PHONE_QUERY = `(max-width: ${PHONE_MAX}px)`;

/** How many words the line holds: runs of anything but white space. */
export function wordCount(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

export const wordsText = (n: number) => (n === 1 ? '1 word' : `${n} words`);

/**
 * Whether the composer shows: opened, and the turn still this seat's. Once the turn is closed
 * (sent, or run out) it shuts and stays shut; the dock itself goes when the turn ends.
 */
export function composerShown(open: boolean, dock: Pick<DockInput, 'closed'>): boolean {
  return open && !dock.closed;
}

/** What the browser says of the visible part of the page (`window.visualViewport`). */
export interface VisibleArea {
  width: number;
  height: number;
  offsetLeft: number;
  offsetTop: number;
}

/**
 * Where the composer sits, in css px: the visible part of the page when the browser says what
 * it is (a phone's soft keyboard takes the foot of the screen, and the composer shrinks to what
 * is left, so the box and Send stay in view); otherwise the whole frame (null: `inset: 0`).
 */
export function composerBox(
  area: VisibleArea | null | undefined,
): { left: number; top: number; width: number; height: number } | null {
  if (!area || !(area.width > 0) || !(area.height > 0)) return null;
  return {
    left: Math.round(area.offsetLeft),
    top: Math.round(area.offsetTop),
    width: Math.round(area.width),
    height: Math.round(area.height),
  };
}
