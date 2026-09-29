/**
 * A speech in pages: the speech box is a fixed board of three lines, so a line longer than
 * that is told a page at a time (docs/beat_sheet.md §0, §11), each page its own beat. Pure, so
 * the beat list, the box and the tests all cut the same pages from the same words.
 *
 * A page is at most `PAGE_CHARS` characters, which the box's measure holds in three lines
 * (SpeechBox.module.css sets the measure in ems, so the count is the same on every screen). It
 * ends at the last sentence end that fits; failing that, at the last clause break (a comma, a
 * semicolon, a colon, a dash); failing that, at the last whole word. Never mid-word: a single
 * word longer than a page is a page of its own.
 */
import { seatify } from '../roles';

/** The most characters a page holds: three lines of the box's measure, less a word's slack. */
export const PAGE_CHARS = 150;

/** A page holds for its words at this pace (the pace a speech always held at). */
const WORDS_PER_SECOND = 3;
const PAGE_FLOOR_MS = 2500;
const PAGE_CAP_MS = 9000;

const words = (text: string) => text.split(/\s+/).filter(Boolean).length;

/** How long a page holds at normal speed: its words at three a second, 2.5–9 s. */
export function pageHold(page: string): number {
  const ms = Math.round((words(page) / WORDS_PER_SECOND) * 1000);
  return Math.min(PAGE_CAP_MS, Math.max(PAGE_FLOOR_MS, ms));
}

/** The last index (exclusive end) in `window` that closes a sentence: `.`, `!`, `?` or `…`, then any closing quote or bracket, then a space or the end. */
function sentenceEnd(window: string, budget: number): number {
  let best = -1;
  const re = /[.!?…]+["'”’)\]]*(?=\s|$)/g;
  for (let m = re.exec(window); m; m = re.exec(window)) {
    const end = m.index + m[0].length;
    if (end <= budget) best = end;
  }
  return best;
}

/** The last clause break that fits: after a comma, semicolon or colon before a space, or after a dash. */
function clauseEnd(window: string, budget: number): number {
  let best = -1;
  const re = /[,;:](?=\s)|\s?[—–]|\s-(?=\s)/g;
  for (let m = re.exec(window); m; m = re.exec(window)) {
    const end = m.index + m[0].length;
    if (end <= budget) best = end;
  }
  return best;
}

/** Cut `text` into pages of at most `budget` characters (see the module's note for where). */
export function paginate(text: string, budget = PAGE_CHARS): string[] {
  let rest = text.trim().replace(/\s+/g, ' ');
  const pages: string[] = [];
  while (rest.length > budget) {
    // one character past the budget: a space there means the word before it ends in time
    const window = rest.slice(0, budget + 1);
    let end = sentenceEnd(window, budget);
    if (end <= 0) end = clauseEnd(window, budget);
    if (end <= 0) {
      const space = window.lastIndexOf(' ');
      end = space > 0 ? space : rest.indexOf(' ');
      if (end <= 0) break; // one word, longer than a page: it is the last page
    }
    const page = rest.slice(0, end).trim();
    if (page) pages.push(page);
    rest = rest.slice(end).trim();
  }
  if (rest) pages.push(rest);
  return pages;
}

/** A speech's pages, as the box shows them (seat names rewritten for the table). */
export function speechPages(message: string): string[] {
  return paginate(seatify(message));
}
