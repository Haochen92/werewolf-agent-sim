/**
 * Store tests — narrowly about the things the store owns that the reducer must not:
 * liveness flagging (ux_journeys §0, binding), reconnect de-duplication, and pacing
 * monotonicity. Fold correctness itself is covered in `foldEvents.test.ts`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { awayTold, liveSeen } from '@/lib/storage';
import {
  agentLine,
  awayNotice,
  chapterLine,
  deathWords,
  GOES_ON,
  lateSpan,
  missedEvents,
  YOUR_TURN,
} from '@/stage/containers/live-state';
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

describe('what went by while the viewer was away (live game ab44887a, seat 3)', () => {
  // seat 3 (the necromancer) as the server streamed it: day 2's vote (205–232), night 2 (233),
  // whose result (279) kills the seat by the wolves and conceals the body, then day 3 (296). A
  // solo game: its requests carry no deadline. As a room's, the same requests are on the clock
  // that hands a turn to the seat's agent.
  const solo = liveGame.events as unknown as DurableGameEvent[];
  const room: DurableGameEvent[] = solo.map((e) =>
    e.type === 'input_request' ? { ...e, deadline: '2026-10-11T10:00:00Z' } : e,
  );
  let seatEvents = room;
  const GAME = 'ab44887a';
  const SEAT = 'player_3';
  const session = new Map<string, string>();
  beforeEach(() => {
    session.clear();
    seatEvents = room;
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: (k: string) => session.get(k) ?? null,
        setItem: (k: string, v: string) => void session.set(k, v),
      },
    });
  });
  afterEach(() => vi.unstubAllGlobals());

  /** A connection (the page opened, reloaded, or its stream reopened after a reload). */
  const connect = (seat: string | null = SEAT) =>
    useGameSession.getState().hydrate([], { gameId: GAME, mySeat: seat });
  const live = (from: number, to: number) => {
    for (const e of seatEvents.filter((x) => x.seq >= from && x.seq <= to))
      useGameSession.getState().applyLive(e);
  };
  const caughtUp = (from: number, to = Infinity) => {
    for (const e of seatEvents.filter((x) => x.seq >= from && x.seq <= to))
      useGameSession.getState().applyCatchUp(e);
  };
  /** What the theatre asks after each fold: what was missed, and what the notice says of it. */
  const told = (turnOpen = false) => {
    const s = useGameSession.getState();
    const missed = missedEvents(s.events, s.liveSeqs, {
      liveBefore: s.liveBefore,
      seated: s.view.me.seat !== null,
      told: awayTold.get(GAME),
    });
    const late = lateSpan(missed, s.liveSeqs, s.liveBefore);
    return awayNotice(s.view, s.events, missed, { turnOpen, late });
  };

  it('a drop in the night: the death leads, then the chapters, then that the game goes on', () => {
    connect();
    live(1, 240);
    expect(told()).toBeNull();
    caughtUp(241); // the reopened stream: what it sends is catch-up
    const notice = told();
    expect(notice).toMatchObject({ first: 278, last: 297 });
    expect(notice!.death).toMatchObject({
      player: SEAT,
      day: 2,
      role: null,
      causes: ['wolves'],
    });
    expect(notice!.lines).toEqual([
      { text: 'You were killed by the wolves on night 2.', quiet: 'Your role was hidden.' },
      { text: 'Night 2 and day 3 went by while you were away.' },
      { text: GOES_ON },
    ]);
  });

  it('a reload in the same tab: the span from the last seq seen live; told once', () => {
    connect();
    live(1, 240);
    expect(liveSeen.get(GAME)).toBe(233);
    // the reload: the whole log again, all of it catch-up, the store reading what the tab saw
    connect();
    expect(useGameSession.getState().liveBefore).toBe(233);
    caughtUp(1);
    const notice = told()!;
    expect(notice.first).toBe(278);
    awayTold.mark(GAME, notice.last); // "Carry on", or "See what happened"
    expect(told()).toBeNull();
    connect();
    caughtUp(1);
    expect(told()).toBeNull();
  });

  it('a blip that missed nothing shows nothing', () => {
    connect();
    live(1, 240);
    caughtUp(200, 240); // the reopen resends what the page already holds
    expect(told()).toBeNull();
  });

  it('a death watched live is not told: only what came in as catch-up', () => {
    connect();
    live(1, 300);
    expect(told()).toBeNull();
    connect();
    caughtUp(1);
    expect(told()).toBeNull();
  });

  it('a new tab on a running game: a seat’s whole history went by; a spectator’s did not', () => {
    connect();
    caughtUp(1);
    expect(told()!.lines).toEqual([
      { text: 'You were killed by the wolves on night 2.', quiet: 'Your role was hidden.' },
      { text: 'Day 1, night 1 and more went by while you were away.' },
      { text: GOES_ON },
    ]);
    session.clear();
    connect(null);
    caughtUp(1);
    expect(told()).toBeNull(); // D23 "late link": zero drama
    // until a drop later costs the spectator something it was watching
    useGameSession.getState().reset();
    connect(null);
    caughtUp(1, 140);
    live(141, 240);
    caughtUp(241);
    expect(told()!.lines).toEqual([
      { text: 'Night 2 and day 3 went by while you were away.' },
    ]);
  });

  it('a new tab whose history is only the deal: the deal plays, nothing went by', () => {
    connect();
    caughtUp(1, 12);
    expect(told()).toBeNull();
    live(13, 40);
    expect(told()).toBeNull();
    // a span that touched no chapter yet names none
    expect(chapterLine([], seatEvents.slice(0, 3))).toBeNull();
  });

  it('a page that watched its platform depart: what followed played from the deal', () => {
    connect();
    caughtUp(1, 140);
    const s = useGameSession.getState();
    const o = { seated: true, told: 0, departed: true };
    expect(missedEvents(s.events, s.liveSeqs, { ...o, liveBefore: null })).toEqual([]);
    expect(missedEvents(s.events, s.liveSeqs, { ...o, liveBefore: 0 })).toEqual([]);
    live(141, 240);
    caughtUp(241);
    const after = useGameSession.getState();
    expect(
      missedEvents(after.events, after.liveSeqs, { ...o, liveBefore: null })[0].seq,
    ).toBe(278);
  });

  it('a spectator who dropped: the chapters alone, no death, no turn', () => {
    connect(null);
    live(1, 240);
    caughtUp(241);
    expect(told(true)!.lines).toEqual([
      { text: 'Night 2 and day 3 went by while you were away.' },
    ]);
  });

  it('back on a turn of the seat’s own: the discussion went on, and it is your turn', () => {
    connect();
    live(1, 112);
    caughtUp(113, 113);
    expect(told(true)!.lines).toEqual([
      { text: 'Day 2’s discussion went on while you were away.' },
      { text: YOUR_TURN },
    ]);
  });

  it('back after the vote: it was held, and the seat’s agent cast its ballot', () => {
    connect();
    live(1, 210);
    caughtUp(211, 232);
    expect(told()!.lines).toEqual([
      { text: 'The vote on day 2 was held while you were away.' },
    ]);
    useGameSession.getState().reset();
    session.clear();
    connect();
    live(1, 204);
    caughtUp(205, 240);
    expect(told()!.lines).toEqual([
      { text: 'Day 2 and night 2 went by while you were away.' },
      { text: 'Your agent played your turn: it abstained on day 2.' },
    ]);
  });

  it('more than two chapters: two named, and more; several turns the agent played', () => {
    connect();
    live(1, 140);
    caughtUp(141);
    expect(told()!.lines).toEqual([
      { text: 'You were killed by the wolves on night 2.', quiet: 'Your role was hidden.' },
      { text: 'Day 2, night 2 and more went by while you were away.' },
      { text: 'Your agent played 3 of your turns.' },
      { text: GOES_ON },
    ]);
    // a solo game's turns wait for their player: no agent played them
    useGameSession.getState().reset();
    session.clear();
    seatEvents = solo;
    connect();
    live(1, 140);
    caughtUp(141);
    expect(told()!.lines).not.toContainEqual({
      text: 'Your agent played 3 of your turns.',
    });
  });

  it('nothing after the game is over: its ending tells everything', () => {
    const view = foldEvents(seatEvents, { mySeat: SEAT });
    expect(awayNotice(view, seatEvents, seatEvents)).not.toBeNull();
    expect(awayNotice({ ...view, over: true }, seatEvents, seatEvents)).toBeNull();
    expect(awayNotice(view, seatEvents, [])).toBeNull();
  });

  it('says a vote-out and a shown card in the table’s words', () => {
    const lynched = {
      player: SEAT,
      role: 'healer',
      day: 3,
      seq: 1,
      causes: ['lynch' as const],
    };
    expect(deathWords(lynched)).toEqual({
      text: 'You were voted out on day 3.',
      quiet: 'The table saw your card: Healer.',
    });
    const both = { ...lynched, causes: ['wolves' as const, 'serial_killer' as const] };
    expect(deathWords(both).text).toBe(
      'You were attacked by the wolves and the serial killer on night 3, and fell.',
    );
  });

  it('says the turn its agent played in the dock’s and the plates’ words', () => {
    const ME = 'player_2';
    const ask = (
      seq: number,
      day: number,
      action_kind: string,
      deadline: string | null = 'x',
    ) =>
      ({
        seq,
        day,
        type: 'input_request',
        player: ME,
        action_kind,
        deadline,
      }) as DurableGameEvent;
    const e = (o: Record<string, unknown>) => o as unknown as DurableGameEvent;
    const one = (log: DurableGameEvent[]) => agentLine(log, log, ME);
    expect(
      one([ask(1, 3, 'discuss'), e({ seq: 2, day: 3, type: 'speech', player: ME })]),
    ).toBe('Your agent played your turn: it spoke for you on day 3.');
    expect(one([ask(1, 3, 'discuss'), e({ seq: 2, day: 3, type: 'phase_change' })])).toBe(
      'Your agent played your turn: it passed on day 3.',
    );
    expect(
      one([
        ask(1, 3, 'vote'),
        e({ seq: 2, day: 3, type: 'vote_cast', voter: ME, votee: 'player_4' }),
      ]),
    ).toBe('Your agent played your turn: it voted seat 4 on day 3.');
    expect(
      one([
        ask(1, 2, 'wolf_vote'),
        e({ seq: 2, day: 2, type: 'wolf_vote', wolf: ME, votee: 'player_4' }),
      ]),
    ).toBe('Your agent played your turn: you vote seat 4 on night 2.');
    expect(
      one([ask(1, 2, 'healer_target'), e({ seq: 2, day: 3, type: 'phase_change' })]),
    ).toBe('Your agent played your turn: it took your night’s act on night 2.');
    // still open (nothing since), or a solo game's (no clock): not played by the agent
    expect(one([ask(1, 3, 'discuss')])).toBeNull();
    expect(
      one([ask(1, 3, 'discuss', null), e({ seq: 2, day: 3, type: 'speech', player: ME })]),
    ).toBeNull();
  });

  it('names a day that ran into its vote, and a night still going', () => {
    const timeline = [
      { day: 3, phase: 'day' as const, seq: 10 },
      { day: 3, phase: 'voting' as const, seq: 20 },
    ];
    const ev = (seq: number, type: string) => ({ seq, day: 3, type }) as DurableGameEvent;
    expect(chapterLine(timeline, [ev(15, 'speech'), ev(20, 'phase_change')])).toBe(
      'Day 3’s discussion went by and the vote began while you were away.',
    );
    expect(
      chapterLine(timeline, [
        ev(15, 'speech'),
        ev(20, 'phase_change'),
        ev(25, 'lynch_result'),
      ]),
    ).toBe('Day 3’s discussion and vote went by while you were away.');
    const night = [{ day: 2, phase: 'night' as const, seq: 5 }];
    expect(chapterLine(night, [ev(7, 'gm_message')])).toBe(
      'Night 2 went on while you were away.',
    );
  });
});
