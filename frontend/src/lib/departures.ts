/**
 * The games for one this tab has just created at the ticket office and is about to open: their
 * page plays the train's departure, as a room's does when its host departs (owner, 2026-10-15),
 * with the puppet the ticket chose aboard (null: the house draws it). Kept until the train has
 * left (`LiveTheatre`, as the curtain falls) and in the tab's session too, so a page remounted
 * or reloaded before then still departs (owner, 2026-10-17: a page that fell over and came back
 * opened on the still platform); after it, a reload lands on the game and never departs twice.
 * A mark holds for `FRESH_MS`: a tab that comes back to the game later lands on it.
 */
import { departMark, type DepartMark } from './storage';

const FRESH_MS = 60_000;

const fresh = new Map<string, DepartMark>();

export const departures = {
  mark(gameId: string, character: string | null): void {
    const mark = { character, at: Date.now() };
    fresh.set(gameId, mark);
    departMark.set(gameId, mark);
  },
  get(gameId: string): { character: string | null } | undefined {
    const mark = fresh.get(gameId) ?? departMark.get(gameId);
    if (!mark || Date.now() - mark.at > FRESH_MS) return undefined;
    return mark;
  },
  forget(gameId: string): void {
    fresh.delete(gameId);
    departMark.clear(gameId);
  },
};
