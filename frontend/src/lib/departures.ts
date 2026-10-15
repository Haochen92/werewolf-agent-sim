/**
 * The games for one this tab has just created at the ticket office and is about to open: their
 * page plays the train's departure, as a room's does when its host departs (owner, 2026-10-15),
 * with the puppet the ticket chose aboard (null: the house draws it). In memory only, so a
 * reload lands on the game and never departs twice; the page reads it once and forgets it.
 */
const fresh = new Map<string, { character: string | null }>();

export const departures = {
  mark(gameId: string, character: string | null): void {
    fresh.set(gameId, { character });
  },
  get(gameId: string): { character: string | null } | undefined {
    return fresh.get(gameId);
  },
  forget(gameId: string): void {
    fresh.delete(gameId);
  },
};
