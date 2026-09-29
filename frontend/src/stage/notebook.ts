'use client';

/**
 * The seated player's notebook for one game: a note on any other seat, the one seat they
 * suspect, and whether they have seen the rail's "Tap a card to write notes" hint.
 *
 * It lives on this device only (localStorage, `notes_{gameId}`), and every scene that draws
 * the seat rail reads the same copy, so a note written in the day is on the card at night.
 * Storage may be missing or refuse a write (a private window): the notebook then lasts as
 * long as the page, and nothing breaks. Nothing here goes to the server, and the suspect is
 * the player's own mark, never a preselected ballot.
 */
import { useCallback, useMemo, useSyncExternalStore } from 'react';
import { seatNotes } from '@/lib/storage';

export interface NotebookState {
  /** A note per seat number, as written. */
  notes: Readonly<Record<number, string>>;
  /** The seat marked as the suspect, or null. */
  suspect: number | null;
  /** The rail's hint has been dismissed (by a first tap on a card). */
  hinted: boolean;
}

export interface Notebook extends NotebookState {
  setNote: (seat: number, text: string) => void;
  /** Mark a seat as the suspect (replacing any other), or clear it with null. */
  setSuspect: (seat: number | null) => void;
  dismissHint: () => void;
}

const EMPTY: NotebookState = { notes: {}, suspect: null, hinted: false };
/** What the server renders: no notes, and no hint (it appears once the page is live). */
const SERVER: NotebookState = { ...EMPTY, hinted: true };

/** A stored record read back, whatever state it is in. */
export function parseNotebook(raw: unknown): NotebookState {
  if (!raw || typeof raw !== 'object') return EMPTY;
  const r = raw as Record<string, unknown>;
  const notes: Record<number, string> = {};
  if (r.notes && typeof r.notes === 'object')
    for (const [k, v] of Object.entries(r.notes as Record<string, unknown>))
      if (typeof v === 'string' && Number.isInteger(Number(k))) notes[Number(k)] = v;
  const suspect =
    typeof r.suspect === 'number' && Number.isInteger(r.suspect) ? r.suspect : null;
  return { notes, suspect, hinted: r.hinted === true };
}

const books = new Map<string, NotebookState>();
const listeners = new Map<string, Set<() => void>>();

function current(gameId: string): NotebookState {
  let b = books.get(gameId);
  if (!b) {
    b = parseNotebook(seatNotes.get(gameId));
    books.set(gameId, b);
  }
  return b;
}

/** Change one game's notebook, keep it, and tell every rail that shows it. */
export function updateNotebook(
  gameId: string,
  change: (b: NotebookState) => NotebookState,
): void {
  const next = change(current(gameId));
  books.set(gameId, next);
  seatNotes.set(gameId, next);
  listeners.get(gameId)?.forEach((f) => f());
}

/** The notebook for a game, or null when there is none to keep (no seated human, no game). */
export function useNotebook(gameId: string | null): Notebook | null {
  const subscribe = useCallback(
    (f: () => void) => {
      if (!gameId) return () => {};
      const set = listeners.get(gameId) ?? new Set();
      listeners.set(gameId, set);
      set.add(f);
      return () => set.delete(f);
    },
    [gameId],
  );
  const state = useSyncExternalStore(
    subscribe,
    () => (gameId ? current(gameId) : EMPTY),
    () => SERVER,
  );
  return useMemo(() => {
    if (!gameId) return null;
    return {
      ...state,
      setNote: (seat, text) =>
        updateNotebook(gameId, (b) => {
          const notes = { ...b.notes };
          if (text.trim()) notes[seat] = text;
          else delete notes[seat];
          return { ...b, notes };
        }),
      setSuspect: (seat) => updateNotebook(gameId, (b) => ({ ...b, suspect: seat })),
      dismissHint: () =>
        updateNotebook(gameId, (b) => (b.hinted ? b : { ...b, hinted: true })),
    };
  }, [gameId, state]);
}

/** The game whose notebook this viewer keeps: a seated human in a live game, else none. */
export function notebookGame(
  p: { hud: string; game?: string },
  me: string | null,
): string | null {
  return p.hud === 'live' && me && p.game ? p.game : null;
}
