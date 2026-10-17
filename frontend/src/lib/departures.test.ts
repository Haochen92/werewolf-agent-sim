import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// A game for one's departure mark (2026-10-17): kept in the tab's session so a page that falls
// over and comes back before the train has left still departs, and stale after a minute.
describe('departures', () => {
  const session = new Map<string, string>();
  beforeEach(() => {
    session.clear();
    vi.resetModules();
    vi.useFakeTimers();
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: (k: string) => session.get(k) ?? null,
        setItem: (k: string, v: string) => void session.set(k, v),
        removeItem: (k: string) => void session.delete(k),
      },
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  const load = async () => (await import('./departures')).departures;

  it('outlives the page that marked it', async () => {
    (await load()).mark('g1', 'hare');
    vi.resetModules(); // a reload: the module's memory is gone, the tab's session is not
    expect((await load()).get('g1')?.character).toBe('hare');
  });

  it('is forgotten once the train has left', async () => {
    const departures = await load();
    departures.mark('g1', null);
    departures.forget('g1');
    vi.resetModules();
    expect((await load()).get('g1')).toBeUndefined();
  });

  it('goes stale after a minute, so a tab coming back later lands on the game', async () => {
    const departures = await load();
    departures.mark('g1', null);
    vi.advanceTimersByTime(59_000);
    expect(departures.get('g1')).toBeDefined();
    vi.advanceTimersByTime(2_000);
    expect(departures.get('g1')).toBeUndefined();
  });
});
