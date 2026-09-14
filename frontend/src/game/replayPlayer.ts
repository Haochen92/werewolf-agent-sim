/**
 * The replay player's pure half: how a finished log is cut into beats, how long each
 * beat holds the screen, and where a cursor lands when it steps or skips.
 *
 * A replay is the whole event log handed over at once. Paging it by day, as the theater
 * did from the start, reads like a finished book. Playing it means revealing the log a
 * little at a time, the way a live table sees it, and the unit of reveal is a BEAT, not an
 * event: a speech together with the annotations that describe it, the vote batch as one
 * block, dawn's narration together with the deaths it announces. Nothing here touches the
 * DOM or a timer; the hook does that. Nothing here re-folds either: the cursor is just how
 * many beats are visible, and the caller folds the visible prefix.
 *
 * Holds are reading time, not real time. The wire carries no timestamps, and a real game's
 * gaps are model latency and human thinking, which is dead air when replayed. Words at a
 * comfortable reading pace, clamped, with a little extra before a verdict.
 */
import type { DurableGameEvent } from '@/types/contracts';

export type BeatKind =
  | 'setup'
  | 'phase'
  | 'turn'
  | 'narration'
  | 'votes'
  | 'resolution'
  | 'wolf'
  | 'night'
  | 'end'
  | 'other';

export interface Beat {
  /** Index range into the log, end exclusive. Beats tile the log with no gaps. */
  start: number;
  end: number;
  /** The day of the beat's lead event; nights carry their own day number. */
  day: number;
  kind: BeatKind;
  /** How long the beat holds the screen at 1x, in milliseconds. */
  holdMs: number;
}

/** Announcements of what is about to happen. They wait for the beat they announce. */
const MARKERS: ReadonlySet<string> = new Set(['turn_started', 'input_request']);

/** Events that describe or settle the beat they follow, never a beat of their own. */
const TRAILERS: ReadonlySet<string> = new Set([
  'role_assigned',
  'roles_assigned',
  'firing_reason',
  'addressed_targets',
  'strategy_update',
  'roster_update',
  'pack_roster_update',
  'day_summary',
  'lynch_result',
  'night_result',
  'investigation_result',
  'vigilante_confirmation',
  'bullets_remaining',
  'wolf_kill_decided',
]);

/** Events released as a batch: consecutive ones of the same type are one beat. */
const BATCHES: ReadonlySet<string> = new Set(['vote_cast', 'wolf_vote']);

const WORDS_PER_MINUTE = 220;
const MIN_HOLD_MS = 1500;
const MAX_HOLD_MS = 8000;
const VERDICT_EXTRA_MS = 1500;

function isTrailer(event: DurableGameEvent): boolean {
  if (TRAILERS.has(event.type)) return true;
  // The server-authored serial-killer note rides inside dawn's narration.
  return event.type === 'wolf_message' && event.wolf === 'game_master';
}

function kindOf(lead: DurableGameEvent, members: readonly DurableGameEvent[]): BeatKind {
  if (members.some((e) => e.type === 'lynch_result' || e.type === 'night_result')) {
    return 'resolution';
  }
  switch (lead.type) {
    case 'game_started':
      return 'setup';
    case 'phase_change':
      return 'phase';
    case 'speech':
    case 'pass_marker':
      return 'turn';
    case 'gm_message':
      return 'narration';
    case 'vote_cast':
    case 'wolf_vote':
      return 'votes';
    case 'wolf_message':
      return 'wolf';
    case 'night_action':
      return 'night';
    case 'game_over':
      return 'end';
    default:
      return 'other';
  }
}

function wordsIn(members: readonly DurableGameEvent[]): number {
  let words = 0;
  for (const event of members) {
    const text =
      event.type === 'speech' || event.type === 'wolf_message'
        ? event.message
        : event.type === 'gm_message'
          ? event.text
          : '';
    if (text) words += text.trim().split(/\s+/).length;
  }
  return words;
}

function holdFor(kind: BeatKind, members: readonly DurableGameEvent[]): number {
  if (kind === 'end') return 0;
  if (kind === 'phase') return 2000;
  if (kind === 'setup') return 2500;
  if (kind === 'votes') return 3000;
  const reading = (wordsIn(members) / WORDS_PER_MINUTE) * 60_000;
  const clamped = Math.min(MAX_HOLD_MS, Math.max(MIN_HOLD_MS, reading));
  return kind === 'resolution' ? clamped + VERDICT_EXTRA_MS : clamped;
}

/** Cut a seq-ordered log into beats. Every event lands in exactly one beat, in order. */
export function groupBeats(events: readonly DurableGameEvent[]): Beat[] {
  const beats: Beat[] = [];
  let start = 0; // where the beat under construction begins (markers included)
  let lead: DurableGameEvent | null = null; // null = only markers so far
  let batchType: string | null = null;

  const close = (end: number) => {
    if (lead === null) {
      if (end > start) beats.push({ start, end, day: events[start].day, kind: 'other', holdMs: 0 });
      return;
    }
    const members = events.slice(start, end);
    const kind = kindOf(lead, members);
    beats.push({ start, end, day: lead.day, kind, holdMs: holdFor(kind, members) });
  };

  events.forEach((event, index) => {
    if (MARKERS.has(event.type)) {
      // A marker after a settled beat opens the next one; before any lead it just waits.
      if (lead !== null) {
        close(index);
        start = index;
        lead = null;
        batchType = null;
      }
      return;
    }
    if (lead !== null && (isTrailer(event) || (BATCHES.has(event.type) && event.type === batchType))) {
      return; // joins the beat under construction
    }
    if (lead !== null) {
      close(index);
      start = index;
    }
    lead = event;
    batchType = BATCHES.has(event.type) ? event.type : null;
  });
  close(events.length);
  return beats;
}

/** How many events a cursor of `revealed` beats shows. */
export function visibleEventCount(beats: readonly Beat[], revealed: number): number {
  if (revealed <= 0) return 0;
  return beats[Math.min(revealed, beats.length) - 1].end;
}

/** The day the cursor is on: that of the last revealed beat, or null before the first. */
export function dayAtCursor(beats: readonly Beat[], revealed: number): number | null {
  if (revealed <= 0 || beats.length === 0) return null;
  return beats[Math.min(revealed, beats.length) - 1].day;
}

/**
 * The cursor that reveals through the next phase change at or after the current one, so a
 * skip lands on "voting begins", "night falls" or the next morning rather than mid-scene.
 * Past the last phase change it reveals everything.
 */
export function cursorAfterNextPhase(beats: readonly Beat[], revealed: number): number {
  for (let i = Math.max(revealed, 0); i < beats.length; i += 1) {
    if (beats[i].kind === 'phase') return i + 1;
  }
  return beats.length;
}

/** The cursor that reveals a day's first beat; the end of the log for an unknown day. */
export function cursorAtDay(beats: readonly Beat[], day: number): number {
  const index = beats.findIndex((beat) => beat.day === day);
  return index === -1 ? beats.length : index + 1;
}
