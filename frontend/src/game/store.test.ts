/**
 * Store tests — narrowly about the things the store owns that the reducer must not:
 * liveness flagging (ux_journeys §0, binding), reconnect de-duplication, and pacing
 * monotonicity. Fold correctness itself is covered in `foldEvents.test.ts`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { deathTold } from '@/lib/storage';
import { awayDeath, awayWords } from '@/stage/containers/live-state';
import { foldEvents } from './foldEvents';
import { useGameSession } from './store';
import fixture from './__fixtures__/seed-chunk-catalogue.json';
import liveGame from './__fixtures__/live-ab44887a-p3.json';

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

  it('remembers where a reconnect’s catch-up ends, but not a late insert behind the head', () => {
    const store = useGameSession.getState();
    for (const e of events.filter((x) => x.seq <= 50)) store.applyCatchUp(e);
    expect(useGameSession.getState().caughtUpTo).toBe(50);
    store.applyLive(events.find((e) => e.seq === 51)!);
    // the connection drops; what was missed comes back as catch-up at the log's end
    for (const e of events.filter((x) => x.seq > 51 && x.seq <= 60)) store.applyCatchUp(e);
    expect(useGameSession.getState().caughtUpTo).toBe(60);
    expect(useGameSession.getState().isLive(60)).toBe(false);
    // an older seq inserted behind the head (the backlog after game over) moves nothing
    const inserted = events.filter((x) => x.seq > 60 && x.seq <= 70);
    store.applyLive(inserted.at(-1)!);
    store.applyCatchUp(inserted[0]);
    expect(useGameSession.getState().caughtUpTo).toBe(60);
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

describe('the seat’s own death, told on return (live game ab44887a, seat 3)', () => {
  // seat 3 (the necromancer) as the server streamed it: night 2's result (seq 279) kills the
  // seat by the wolves and conceals the body, during a two-minute drop on a phone
  const seatEvents = liveGame.events as unknown as DurableGameEvent[];
  const GAME = 'ab44887a';
  const SEAT = 'player_3';
  const session = new Map<string, string>();
  beforeEach(() => {
    session.clear();
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: (k: string) => session.get(k) ?? null,
        setItem: (k: string, v: string) => void session.set(k, v),
      },
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  /** The question the theatre asks after each fold: anything to tell, not told in this tab? */
  const toTell = () => {
    const s = useGameSession.getState();
    return awayDeath(s.view, s.liveSeqs, deathTold.has(GAME, SEAT));
  };

  it('a catch-up that carries my death tells it, in the morning roll’s words', () => {
    const store = useGameSession.getState();
    store.hydrate([], { gameId: GAME, mySeat: SEAT });
    // live up to the night, then the drop: what the reopened stream sends is catch-up
    for (const e of seatEvents.filter((x) => x.seq <= 240)) store.applyLive(e);
    expect(toTell()).toBeNull();
    for (const e of seatEvents.filter((x) => x.seq > 240)) store.applyCatchUp(e);
    const death = toTell();
    expect(death).toMatchObject({ player: SEAT, day: 2, role: null, causes: ['wolves'] });
    expect(awayWords(death!)).toBe(
      'You were killed by the wolves on night 2. Your role was hidden. ' +
        'The game goes on without you: watch it to the end, or leave the table.',
    );
  });

  it('the first connection to a running game is a catch-up too', () => {
    const store = useGameSession.getState();
    store.hydrate([], { gameId: GAME, mySeat: SEAT });
    for (const e of seatEvents) store.applyCatchUp(e);
    expect(toTell()?.seq).toBe(279);
  });

  it('a death that arrived live is not told: its beats played it', () => {
    const store = useGameSession.getState();
    store.hydrate([], { gameId: GAME, mySeat: SEAT });
    for (const e of seatEvents) store.applyLive(e);
    expect(toTell()).toBeNull();
  });

  it('a second catch-up of the same death does not tell it again', () => {
    const store = useGameSession.getState();
    store.hydrate([], { gameId: GAME, mySeat: SEAT });
    for (const e of seatEvents) store.applyCatchUp(e);
    expect(toTell()).not.toBeNull();
    deathTold.mark(GAME, SEAT); // the notice, dismissed
    // a reload in the same tab: the whole log again, all of it history
    useGameSession.getState().hydrate([], { gameId: GAME, mySeat: SEAT });
    for (const e of seatEvents) useGameSession.getState().applyCatchUp(e);
    expect(awayDeath(useGameSession.getState().view, new Set())).not.toBeNull();
    expect(toTell()).toBeNull();
  });

  it('says a vote-out and a shown card in the table’s words; not a spectator’s, nor after the end', () => {
    const lynched = {
      player: SEAT,
      role: 'healer',
      day: 3,
      seq: 1,
      causes: ['lynch' as const],
    };
    expect(awayWords(lynched)).toMatch(
      /^You were voted out on day 3\. The table saw your card: Healer\. /,
    );
    const both = { ...lynched, causes: ['wolves' as const, 'serial_killer' as const] };
    expect(awayWords(both)).toMatch(
      /^You were attacked by the wolves and the serial killer on night 3, and fell\./,
    );
    const view = foldEvents(seatEvents, { mySeat: SEAT });
    expect(awayDeath(view, new Set())).not.toBeNull();
    expect(awayDeath({ ...view, me: { ...view.me, seat: null } }, new Set())).toBeNull();
    expect(awayDeath({ ...view, over: true }, new Set())).toBeNull();
  });
});
