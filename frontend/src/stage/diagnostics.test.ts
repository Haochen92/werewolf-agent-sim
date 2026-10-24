import { beforeEach, expect, it, vi } from 'vitest';
import type { BackdropSpec } from './set';

beforeEach(() => vi.resetModules());

const spec: BackdropSpec = {
  phase: 'day',
  hud: 'live',
  side: true,
  from: null,
  fadeDelay: 1.2,
  ahead: null,
  k: 1,
};
const frame = {
  gameId: 'game',
  beat: 'day.speech',
  seq: 620,
  slot: 'film',
  revealed: false,
  serverOver: true,
  fileTab: 'notes',
  fileSeat: 'player_3',
};

it('keeps the lagging playhead and a bounded history of backdrop changes and withdrawals', async () => {
  const d = await import('./diagnostics');
  d.recordLiveFrame(frame);
  for (let i = 0; i < 30; i++) d.recordBackdrop({ ...spec, fadeDelay: i });
  d.recordBackdrop(null);
  const snapshot = d.stageDiagnostics();
  expect(snapshot.live).toEqual(frame);
  expect(snapshot.backdrops).toHaveLength(16);
  expect(snapshot.backdrops[0].spec?.fadeDelay).toBe(15);
  expect(snapshot.backdrops.at(-1)?.spec).toBeNull();
});

it('copies snapshots and drops the previous game when a new game is displayed', async () => {
  const d = await import('./diagnostics');
  const input = { ...spec };
  d.recordLiveFrame(frame);
  d.recordBackdrop(input);
  input.phase = 'night';
  const snapshot = d.stageDiagnostics();
  expect(snapshot.backdrops[0].spec?.phase).toBe('day');
  snapshot.backdrops[0].spec!.phase = 'dusk';
  expect(d.stageDiagnostics().backdrops[0].spec?.phase).toBe('day');
  d.recordLiveFrame({ ...frame, gameId: 'next-game' });
  expect(d.stageDiagnostics().backdrops).toEqual([]);
  expect(snapshot.live?.gameId).toBe('game');
});
