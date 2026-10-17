import { describe, expect, it } from 'vitest';
import { pillLine, pillState } from './connection-pill';

describe('the connection pill (owner, 2026-10-17)', () => {
  it('says nothing while the stream is up, or where there is none', () => {
    expect(pillState('open', true, false)).toBeNull();
    expect(pillState('connecting', true, false)).toBeNull();
    // the browser gave up (a game gone from the registry): the watch retries, the page is quiet
    expect(pillState('closed', true, true)).toBeNull();
    // a waiting room has no stream, offline or not
    expect(pillState('idle', false, true)).toBeNull();
  });

  it('reconnects first, and is offline past a blip or when the browser says so', () => {
    expect(pillState('reconnecting', true, false)).toBe('reconnecting');
    expect(pillState('reconnecting', true, true)).toBe('offline');
    expect(pillState('reconnecting', false, false)).toBe('offline');
    // the browser knows before the stream does
    expect(pillState('open', false, false)).toBe('offline');
  });

  it('says whether the game waits or the seat’s clock runs', () => {
    expect(pillLine('reconnecting', 'solo')).toBe('Reconnecting… the game waits for you');
    expect(pillLine('reconnecting', 'room')).toBe(
      'Reconnecting… your seat’s clock is running',
    );
    expect(pillLine('offline', 'solo')).toBe('You’re offline. The game waits.');
    expect(pillLine('offline', 'room')).toBe(
      'You’re offline. Your seat’s clock is running.',
    );
    // a watcher has no seat to wait for, and no clock
    expect(pillLine('reconnecting', 'watching')).toBe('Reconnecting…');
    expect(pillLine('offline', 'watching')).toBe('You’re offline.');
  });
});
