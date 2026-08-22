/**
 * Store tests — narrowly about the things the store owns that the reducer must not:
 * liveness flagging (ux_journeys §0, binding), reconnect de-duplication, and pacing
 * monotonicity. Fold correctness itself is covered in `foldEvents.test.ts`.
 */
import { beforeEach, describe, expect, it } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { foldEvents } from './foldEvents';
import { useGameSession } from './store';
import fixture from './__fixtures__/seed-chunk-catalogue.json';

const events = (fixture as unknown as ReplayGame).events as DurableGameEvent[];

beforeEach(() => useGameSession.getState().reset());

describe('liveness flagging', () => {
  it('marks NOTHING live on hydrate — a refreshed session must be silent', () => {
    useGameSession.getState().hydrate(events, { gameId: 'seed-chunk-catalogue' });
    const s = useGameSession.getState();
    expect(s.view.lastSeq).toBe(593);
    expect(s.liveSeqs.size).toBe(0);
    expect(s.isLive(593)).toBe(false); // even the game_over that would fire D22
  });

  it('marks only events that arrived on the wire', () => {
    const store = useGameSession.getState();
    store.hydrate(events.filter((e) => e.seq <= 100));
    store.applyLive(events.find((e) => e.seq === 101)!);
    store.applyLive(events.find((e) => e.seq === 102)!);
    const s = useGameSession.getState();
    expect(s.isLive(100)).toBe(false);
    expect(s.isLive(101)).toBe(true);
    expect(s.isLive(102)).toBe(true);
    expect(s.liveSeqs.size).toBe(2);
  });

  it('clears live flags when re-hydrated — a reconnect re-fold is history again', () => {
    const store = useGameSession.getState();
    store.hydrate(events.filter((e) => e.seq <= 100));
    store.applyLive(events.find((e) => e.seq === 101)!);
    expect(useGameSession.getState().liveSeqs.size).toBe(1);
    useGameSession.getState().hydrate(events.filter((e) => e.seq <= 200));
    expect(useGameSession.getState().liveSeqs.size).toBe(0);
  });
});

describe('reconnect safety', () => {
  it('ignores a re-delivered seq instead of duplicating the transcript', () => {
    const store = useGameSession.getState();
    store.hydrate(events.filter((e) => e.seq <= 55));
    const speech = events.find((e) => e.seq === 56)!;
    store.applyLive(speech);
    const afterFirst = useGameSession.getState().view.days[2].slots.length;
    // Last-Event-ID replay hands us the same event again.
    useGameSession.getState().applyLive(speech);
    const afterRepeat = useGameSession.getState().view.days[2].slots.length;
    expect(afterRepeat).toBe(afterFirst);
    expect(useGameSession.getState().events).toHaveLength(56);
  });

  it('absorbs the exact R7 order: game_over first, then unseen lower-seq backlog', () => {
    const publicTypes = new Set([
      'game_started',
      'phase_change',
      'game_over',
      'turn_started',
      'speech',
      'day_summary',
      'vote_cast',
      'gm_message',
      'lynch_result',
      'roster_update',
      'night_result',
    ]);
    const publicEvents = events.filter((event) => publicTypes.has(event.type));
    const heldEvents = events.filter((event) => !publicTypes.has(event.type));
    const store = useGameSession.getState();

    for (const event of publicEvents) store.applyLive(event);
    expect(useGameSession.getState().view.winner).toBe('wolves');
    expect(useGameSession.getState().view.xray.available).toBe(false);

    // This is server/routes/games.py's R7 flush: the high game_over seq is already folded.
    for (const event of heldEvents) store.applyLive(event);

    const state = useGameSession.getState();
    expect(state.events).toHaveLength(events.length);
    expect(state.view).toEqual(foldEvents(events));
    expect(state.view.xray.available).toBe(true);
    expect(Object.keys(state.view.xray.roles)).toHaveLength(9);
    expect(state.isLive(593)).toBe(true);
  });
});

describe('pending input reconciliation', () => {
  const request = {
    seq: 1,
    day: 1,
    type: 'input_request',
    player: 'player_1',
    action_kind: 'vote',
    candidates: ['player_2'],
    deadline: '2026-08-21T12:00:00Z',
  } as DurableGameEvent;

  it('lets status clear a historical request and refresh its live deadline', () => {
    const store = useGameSession.getState();
    store.hydrate([request], { mySeat: 'player_1' });
    expect(useGameSession.getState().view.me.pending).not.toBeNull();

    store.syncPending('player_1', ['player_1'], {
      player_1: '2026-08-21T12:01:00Z',
    });
    expect(useGameSession.getState().view.me.pending?.deadline).toBe(
      '2026-08-21T12:01:00Z',
    );

    store.syncPending('player_1', []);
    expect(useGameSession.getState().view.me.pending).toBeNull();
  });

  it('does not let an older status response erase a newer SSE request', () => {
    const store = useGameSession.getState();
    store.applyLive(request);
    store.syncPending('player_1', [], {}, 0);
    expect(useGameSession.getState().view.me.pending?.seq).toBe(1);
  });
});

describe('pacing', () => {
  it('applies monotonic-max so the bar never walks backwards', () => {
    const store = useGameSession.getState();
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 3,
      total: 5,
    });
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 1,
      total: 5,
    });
    expect(useGameSession.getState().pacing['2:night'].done).toBe(3);
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 5,
      total: 5,
    });
    expect(useGameSession.getState().pacing['2:night'].done).toBe(5);
  });

  it('keys the two stages and the days apart', () => {
    const store = useGameSession.getState();
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 2,
      total: 5,
    });
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'day_vote',
      done: 4,
      total: 9,
    });
    store.applyPacing({
      type: 'phase_progress',
      day: 3,
      stage: 'night',
      done: 1,
      total: 5,
    });
    const { pacing } = useGameSession.getState();
    expect(pacing['2:night'].done).toBe(2);
    expect(pacing['2:day_vote'].done).toBe(4);
    expect(pacing['3:night'].done).toBe(1);
  });

  it('never enters the durable view — pacing is ephemeral by construction', () => {
    const store = useGameSession.getState();
    store.hydrate(events);
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 3,
      total: 5,
    });
    expect(useGameSession.getState().view.lastSeq).toBe(593);
    expect(JSON.stringify(useGameSession.getState().view)).not.toContain('phase_progress');
  });

  it('is cleared by hydrate so another game cannot inherit a completed strip', () => {
    const store = useGameSession.getState();
    store.applyPacing({
      type: 'phase_progress',
      day: 2,
      stage: 'night',
      done: 5,
      total: 5,
    });
    store.hydrate([]);
    expect(useGameSession.getState().pacing).toEqual({});
  });
});
