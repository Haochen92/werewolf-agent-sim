/**
 * The live stage, fed the fixture game one event at a time as a seat would receive it
 * (player_7, the vigilante): history lands still, news plays through the timer, prompts wait,
 * the X-ray at game over carries the stage across, and the ending runs to its curtain. Then the
 * answers: the turn's body per request kind, the draft's state, the clock.
 */
import { describe, expect, it } from 'vitest';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import type { SceneBeat } from '@/stage/beats/types';
import type { DurableGameEvent, EventType, InputRequest } from '@/types/contracts';
import {
  actSent,
  ALREADY_ANSWERED,
  DEFAULT_TURN_MS,
  DRAFT_FAILED,
  historyEnd,
  historyLanding,
  initialLiveState,
  initialTurnState,
  liveReducer,
  payloadFor,
  requestBefore,
  requestIsActive,
  turnClock,
  turnReducer,
  type LiveCtx,
  type LiveState,
  type TurnState,
} from './live-state';

const ALL = fixture.events as unknown as DurableGameEvent[];
const ME = 'player_7';

const OBSERVER: ReadonlySet<EventType> = new Set<EventType>([
  'roles_assigned',
  'pass_marker',
  'firing_reason',
  'addressed_targets',
  'strategy_update',
  'memory_consulted',
  'memory_extracted',
  'player_reads',
  'day_summary_structured',
  'night_action',
]);
const FACTION: ReadonlySet<EventType> = new Set<EventType>([
  'pack_roster_update',
  'wolf_message',
  'wolf_vote',
  'wolf_kill_decided',
]);
const SEAT: ReadonlySet<EventType> = new Set<EventType>([
  'role_assigned',
  'input_request',
  'investigation_result',
  'vigilante_confirmation',
  'bullets_remaining',
]);

/** What a villager-side seat receives while the game runs (the server's entitlement, live). */
function seen(e: DurableGameEvent): boolean {
  if (OBSERVER.has(e.type) || FACTION.has(e.type)) return false;
  if (SEAT.has(e.type)) return 'player' in e && e.player === ME;
  return true;
}
const MINE = ALL.filter(seen);
const upTo = (seq: number) => MINE.filter((e) => e.seq <= seq);

const request = (
  seq: number,
  kind: InputRequest['action_kind'],
  day = 3,
): InputRequest => ({
  seq,
  day,
  type: 'input_request',
  player: ME,
  action_kind: kind,
  candidates: kind === 'discuss' ? [] : ['player_1', 'player_2', 'abstain'],
  deadline: null,
});

const ctx = (over: Partial<LiveCtx> = {}): LiveCtx => ({
  me: ME,
  rolesLanded: false,
  openPrompt: null,
  ...over,
});

/**
 * A session as the theatre would drive it: the log grows, some of it as history, and each
 * change is a recut. `live` is the set of seqs that arrived as news.
 */
class Session {
  state: LiveState = initialLiveState();
  events: DurableGameEvent[] = [];
  live = new Set<number>();
  ctx = ctx();
  /** The status's last seq at connect: set, the theatre's deal rule is on (`historyLanding`). */
  connectedAt: number | null = null;
  /** The newest seq a reconnect caught up on (the store's `caughtUpTo`). */
  caughtUpTo = 0;

  beats(): SceneBeat[] {
    const xray = this.events.some((e) => e.type === 'game_over');
    return beatsFor(this.events, { xray, me: ME, live: true });
  }
  recut() {
    const end = historyEnd(this.events, this.live, this.caughtUpTo);
    this.state = liveReducer(this.state, {
      type: 'recut',
      beats: this.beats(),
      historyEnd: end,
      landing:
        this.connectedAt === null
          ? undefined
          : historyLanding(this.events, end, this.connectedAt),
      ctx: this.ctx,
    });
    return this;
  }
  /** Events arriving: as history (catch-up) or as news, one recut per event (one SSE frame each). */
  arrive(events: readonly DurableGameEvent[], asNews: boolean) {
    for (const e of events) {
      this.events = [...this.events, e].sort((a, b) => a.seq - b.seq);
      if (asNews) this.live.add(e.seq);
      this.recut();
    }
    return this;
  }
  /** The hold on stage runs out. */
  held() {
    this.state = liveReducer(this.state, {
      type: 'held',
      step: this.state.step,
      ctx: this.ctx,
    });
    return this;
  }
  set(over: Partial<LiveCtx>) {
    this.ctx = ctx(over);
    return this.recut();
  }
  get beat() {
    return this.state.beats[this.state.cursor.index];
  }
}

describe('the live stage: history and news', () => {
  it('lands history still on the latest beat and plays none of it', () => {
    const s = new Session();
    s.recut(); // hydrated with nothing
    expect(s.state.cursor.index).toBe(-1);
    for (const e of upTo(200)) {
      s.arrive([e], false);
      // at every step the stage is at the newest beat, at rest, and not holding
      expect(s.state.cursor.index).toBe(s.state.beats.length - 1);
      expect(s.state.cursor.animate).toBe(false);
      expect(s.state.holding).toBe(false);
    }
    expect(s.beat).toMatchObject({ id: 'day.speech', seq: 200 });
  });

  it('plays news one beat at a time, moving on only when the hold runs out', () => {
    const s = new Session();
    s.arrive(upTo(1), true); // game_started: two beats
    expect(s.beat.id).toBe('deal.table-seated');
    expect(s.state.cursor.animate).toBe(true);
    expect(s.state.holding).toBe(true);
    // more news arrives while the first beat holds: the stage does not move
    s.arrive(
      MINE.filter((e) => e.seq > 1 && e.seq <= 20),
      true,
    );
    expect(s.state.cursor.index).toBe(0);
    // the hold runs out: the next beat plays; still the deal, so at normal speed
    s.held();
    expect(s.state.cursor).toEqual({ index: 1, animate: true });
    expect(s.state.speed).toBe('normal');
    // a stale timer (an older step) does nothing
    const before = s.state;
    s.state = liveReducer(s.state, { type: 'held', step: s.state.step - 1, ctx: s.ctx });
    expect(s.state).toBe(before);
    // past the deal, a backlog of three or more drains fast
    while (s.beat.id.startsWith('deal.')) s.held();
    expect(s.state.beats.length - 1 - s.state.cursor.index).toBeGreaterThanOrEqual(2);
    expect(s.state.speed).toBe('fast');
    // drain to the end: the last queued beat plays at normal speed
    while (s.state.cursor.index < s.state.beats.length - 1) s.held();
    expect(s.state.speed).toBe('normal');
    s.held();
    expect(s.state.holding).toBe(false);
    expect(s.state.cursor.index).toBe(s.state.beats.length - 1);
  });

  it('a new beat after the stage has caught up plays at once', () => {
    const s = new Session().arrive(upTo(199), false);
    const at = s.state.cursor.index;
    s.arrive([ALL.find((e) => e.seq === 200)!], true);
    expect(s.state.cursor).toEqual({ index: at + 1, animate: true });
    expect(s.beat).toMatchObject({ id: 'day.speech', seq: 200 });
    expect(s.state.speed).toBe('normal');
  });
});

describe('the live stage: the deal on first connection, and a reconnect', () => {
  const deal = upTo(12); // up to "the day begins": the deal, and no turn yet

  it('a new game’s history plays from the first beat at normal speed', () => {
    const s = new Session();
    s.connectedAt = 12;
    // the history trickles in: until it is all in, nothing is decided
    s.arrive(upTo(1), false);
    expect(s.state.cursor.index).toBe(-1);
    s.arrive(deal.slice(1), false);
    expect(s.beat.id).toBe('deal.table-seated');
    expect(s.state.cursor.animate).toBe(true);
    expect(s.state.speed).toBe('normal');
    // the day's first turn arrives as news while the deal plays: the deal keeps its pace
    s.arrive(
      MINE.filter((e) => e.seq > 12 && e.seq <= 13),
      true,
    );
    expect(s.beat.id).toBe('deal.table-seated');
    const seen: string[] = [];
    while (s.beat.id.startsWith('deal.')) {
      expect(s.state.speed).toBe('normal');
      seen.push(s.beat.id);
      s.held();
    }
    expect(seen).toEqual([
      'deal.table-seated',
      'deal.cards-dealt',
      'deal.your-card',
      'deal.day-begins',
    ]);
    expect(s.beat.id).toBe('day.turn-thinking');
  });

  it('a deal that arrives as news, after the waiting room departs, keeps its pace', () => {
    // the page watched the platform: the stream opened with nothing in the log yet
    const s = new Session();
    s.connectedAt = 0;
    s.arrive(deal, true);
    expect(s.beat.id).toBe('deal.table-seated');
    // the day's first turn follows while the deal plays
    s.arrive(
      MINE.filter((e) => e.seq > 12 && e.seq <= 13),
      true,
    );
    const seen: string[] = [];
    while (s.beat.id.startsWith('deal.')) {
      expect(s.state.speed).toBe('normal');
      seen.push(s.beat.id);
      s.held();
    }
    expect(seen).toEqual([
      'deal.table-seated',
      'deal.cards-dealt',
      'deal.your-card',
      'deal.day-begins',
    ]);
    expect(s.beat.id).toBe('day.turn-thinking');
    // without the deal's rule (no connection reported), the deal still keeps its pace
    const q = new Session().arrive(deal, true);
    q.held();
    expect(q.state.speed).toBe('normal');
  });

  it('a history that holds a turn lands still, as before', () => {
    expect(historyLanding(upTo(13), upTo(13).length, 13)).toBe('still');
    const s = new Session();
    s.connectedAt = 200;
    s.arrive(upTo(200), false);
    expect(s.beat).toMatchObject({ id: 'day.speech', seq: 200 });
    expect(s.state.cursor.animate).toBe(false);
  });

  it('what a reconnect catches up on lands still; what comes after it plays', () => {
    const s = new Session().arrive(upTo(190), false);
    s.caughtUpTo = 190;
    s.arrive(
      MINE.filter((e) => e.seq > 190 && e.seq <= 195),
      true,
    );
    expect(s.state.holding).toBe(true);
    // dropped and back: the missed events arrive as catch-up, at the log's end
    const missed = MINE.filter((e) => e.seq > 195 && e.seq <= 200);
    s.caughtUpTo = 200;
    s.arrive(missed, false);
    expect(s.beat).toMatchObject({ id: 'day.speech', seq: 200 });
    expect(s.state.cursor.animate).toBe(false);
    expect(s.state.holding).toBe(false);
  });
});

describe('the live stage: the seated human’s prompt', () => {
  it('a prompt plays at once and waits while it is open', () => {
    const s = new Session().arrive(upTo(200), false);
    s.ctx = ctx({ openPrompt: 201 });
    s.arrive([request(201, 'discuss')], true);
    expect(s.beat).toMatchObject({ id: 'day.your-turn', seq: 201 });
    expect(s.state.cursor.animate).toBe(true);
    expect(s.state.holding).toBe(false); // a prompt has no hold: it waits
    // my line arrives while the stage still thinks the prompt is open: it waits
    const line: DurableGameEvent = {
      seq: 202,
      day: 3,
      type: 'speech',
      player: ME,
      message: 'Seat 8 is dodging.',
      channel_seq: 40,
    } as DurableGameEvent;
    s.arrive([line], true);
    expect(s.beat.id).toBe('day.your-turn');
    // answered (or gone): the stage moves on to my line
    s.set({ openPrompt: null });
    expect(s.beat).toMatchObject({ id: 'day.speech', seq: 202, subject: ME });
  });

  it('the dock never waits for the stage: the beat on stage is cut short, the rest drain fast', () => {
    const s = new Session().arrive(upTo(190), false);
    // three speeches arrive as news, then my request
    s.arrive(
      MINE.filter((e) => e.seq > 190 && e.seq <= 200),
      true,
    );
    const holding = s.state.cursor.index;
    expect(s.state.holding).toBe(true);
    s.ctx = ctx({ openPrompt: 201 });
    s.arrive([request(201, 'discuss')], true);
    // cut short once: the next beat is already on
    expect(s.state.cursor.index).toBe(holding + 1);
    expect(s.state.speed).toBe('fast');
    // a later recut does not cut the fast hold again
    const step = s.state.step;
    s.recut();
    expect(s.state.step).toBe(step);
    while (s.beat.id !== 'day.your-turn') s.held();
    expect(s.beat.seq).toBe(201);
  });
});

describe('the live stage: game over', () => {
  const beforeOver = upTo(405);
  const gameOver = ALL.find((e) => e.type === 'game_over')!;
  // the withheld backlog the server sends after game_over (older seqs: history to this page)
  const backlog = ALL.filter((e) => e.seq < gameOver.seq && !seen(e));
  const extracted = ALL.find((e) => e.type === 'memory_extracted')!;

  it('the X-ray carries the stage across when earlier beats are cut in', () => {
    const s = new Session().arrive(beforeOver, false);
    const was = s.beat;
    const at = s.state.cursor.index;
    s.arrive([gameOver], true);
    // game over turns the X-ray on: the deal's face-up and the passes are cut in before
    s.arrive(backlog, false);
    const now = s.state.beats.findIndex((b) => b.id === was.id && b.seq === was.seq);
    expect(now).toBeGreaterThan(at);
    // the stage went on from the same beat, not from its old position
    expect(s.state.beats.slice(0, now).some((b) => b.id === 'deal.face-up')).toBe(true);
    expect(s.state.cursor.index).toBeGreaterThan(now);
    expect(s.beat.id.startsWith('over.')).toBe(true);
  });

  it('holds the winners’ stand for the roles, then runs to the curtain; the epilogue waits for its close', () => {
    const s = new Session().arrive(beforeOver, false).arrive([gameOver], true);
    while (s.state.holding) s.held();
    // no roles yet: the verdict holds the stage
    expect(s.beat.id).toBe('over.verdict');
    s.arrive(backlog, false).set({ rolesLanded: true });
    expect(s.beat.id).toBe('over.winners-stand');
    while (s.state.holding) s.held();
    expect(s.beat.id).toBe('over.curtain');
    // the memory lands after the curtain is up: the sheet comes down over it
    s.arrive([extracted], true);
    expect(s.beat.id).toBe('over.epilogue');
    expect(s.state.cursor.animate).toBe(true);
    s.held();
    expect(s.beat.id).toBe('over.epilogue');
    s.state = liveReducer(s.state, { type: 'dismiss', ctx: s.ctx });
    expect(s.beat.id).toBe('over.curtain');
  });

  it('a finished game opened afterwards lands on the curtain, still', () => {
    const everything = [...ALL].sort((a, b) => a.seq - b.seq);
    const s = new Session().arrive(everything, false);
    expect(s.beat.id).toBe('over.curtain');
    expect(s.state.cursor.animate).toBe(false);
  });
});

describe('the live stage: the side slot', () => {
  it('Transcript brings the drawer or closes it; X-ray brings the film only once the game is over', () => {
    let st = initialLiveState(null);
    st = liveReducer(st, { type: 'transcript' });
    expect(st.slot).toBe('drawer');
    expect(liveReducer(st, { type: 'xray', xray: false }).slot).toBe('drawer');
    st = liveReducer(st, { type: 'xray', xray: true });
    expect(st.slot).toBe('film');
    expect(liveReducer(st, { type: 'transcript' }).slot).toBe('drawer');
    expect(liveReducer(st, { type: 'xray', xray: true }).slot).toBe(null);
  });
});

describe('the turn’s body, by request kind', () => {
  const ask = (kind: InputRequest['action_kind'], candidates: string[] = []) => ({
    actionKind: kind,
    candidates,
  });
  it('a line, or a pass, for the day’s turn', () => {
    expect(payloadFor(ask('discuss'), { say: '  Seat 8 is dodging. ' })).toEqual({
      message: 'Seat 8 is dodging.',
    });
    expect(payloadFor(ask('discuss'), { say: '   ' })).toBeNull();
    expect(payloadFor(ask('discuss'), { act: null })).toEqual({ pass_turn: true });
  });
  it('a line only for the pack', () => {
    expect(payloadFor(ask('wolf_discuss'), { say: 'Seat 4.' })).toEqual({
      message: 'Seat 4.',
    });
    expect(payloadFor(ask('wolf_discuss'), { act: null })).toBeNull();
  });
  it('a seat from the list for votes and acts; "no one" only as the listed sentinel', () => {
    const vote = ask('vote', ['player_1', 'player_2', 'abstain']);
    expect(payloadFor(vote, { act: 'player_2' })).toEqual({ target: 'player_2' });
    expect(payloadFor(vote, { act: null })).toEqual({ target: 'abstain' });
    expect(payloadFor(vote, { act: 'player_9' })).toBeNull();
    const shot = ask('vigilante_target', ['player_1', 'hold_fire']);
    expect(payloadFor(shot, { act: null })).toEqual({ target: 'hold_fire' });
    expect(payloadFor(ask('healer_target', ['player_1']), { act: null })).toBeNull();
    expect(payloadFor(ask('wolf_vote', ['player_4']), { act: 'player_4' })).toEqual({
      target: 'player_4',
    });
  });
  it('the agent can take any turn', () => {
    for (const kind of ['discuss', 'vote', 'wolf_discuss', 'serial_killer_target'] as const)
      expect(payloadFor(ask(kind), { delegate: true })).toEqual({ delegate: true });
  });
});

describe('the turn’s state: the line, the drafts, the answer', () => {
  const opened = turnReducer(initialTurnState, { type: 'open', seq: 201 });

  it('a draft lands in the box, counts down the drafts and brings the new deadline', () => {
    let t = turnReducer(opened, { type: 'notes', notes: '8 dodging' });
    t = turnReducer(t, { type: 'drafting', seq: 201 });
    expect(t.drafting).toBe(true);
    t = turnReducer(t, {
      type: 'drafted',
      seq: 201,
      draft: 'Seat 8 keeps dodging the question.',
      draftsLeft: 2,
      deadline: '2026-09-25T10:02:10Z',
    });
    expect(t).toMatchObject({
      drafting: false,
      text: 'Seat 8 keeps dodging the question.',
      notes: '8 dodging',
      draftsLeft: 2,
      deadline: '2026-09-25T10:02:10Z',
    });
  });

  it('a draft for an older request is dropped; a new request starts afresh but remembers the agent', () => {
    const t: TurnState = { ...opened, text: 'half a line', byAgent: [150] };
    expect(
      turnReducer(t, {
        type: 'drafted',
        seq: 150,
        draft: 'x',
        draftsLeft: 0,
        deadline: null,
      }),
    ).toBe(t);
    const next = turnReducer(t, { type: 'open', seq: 230 });
    expect(next).toMatchObject({ seq: 230, text: '', draftsLeft: 3, byAgent: [150] });
    expect(turnReducer(next, { type: 'open', seq: 230 })).toBe(next);
  });

  it('409 means no drafts left (in the server’s words); 503 or no helper means type it instead', () => {
    const gone = turnReducer(opened, {
      type: 'draft-failed',
      seq: 201,
      status: 409,
      message: 'no drafts left this turn: send what you have',
    });
    expect(gone).toMatchObject({
      draftsLeft: 0,
      error: 'no drafts left this turn: send what you have',
    });
    const failed = turnReducer(
      { ...opened, notes: 'keep me' },
      { type: 'draft-failed', seq: 201, status: 503, message: 'x' },
    );
    expect(failed).toMatchObject({ error: DRAFT_FAILED, notes: 'keep me', draftsLeft: 3 });
    // a server without the helper (404), or no network, reads the same
    expect(
      turnReducer(opened, {
        type: 'draft-failed',
        seq: 201,
        status: 404,
        message: 'Not Found',
      }).error,
    ).toBe(DRAFT_FAILED);
  });

  it('sending: accepted closes the turn; 409 is already answered; 422 says the engine’s words', () => {
    const sending = turnReducer(opened, { type: 'sending', seq: 201 });
    expect(sending.sending).toBe(true);
    expect(
      turnReducer(sending, { type: 'sent', seq: 201, delegated: false }),
    ).toMatchObject({
      answered: true,
      byAgent: [],
    });
    expect(
      turnReducer(sending, { type: 'sent', seq: 201, delegated: true }).byAgent,
    ).toEqual([201]);
    expect(
      turnReducer(sending, { type: 'send-failed', seq: 201, status: 409, message: 'x' }),
    ).toMatchObject({ answered: true, error: ALREADY_ANSWERED });
    expect(
      turnReducer(sending, {
        type: 'send-failed',
        seq: 201,
        status: 422,
        message: 'this turn cannot be passed',
      }),
    ).toMatchObject({
      answered: false,
      sending: false,
      error: 'this turn cannot be passed',
    });
  });

  it('run out unanswered: the seat’s agent answered it', () => {
    expect(turnReducer(opened, { type: 'expired', seq: 201 })).toMatchObject({
      answered: true,
      byAgent: [201],
    });
    const sent = turnReducer(opened, { type: 'sent', seq: 201, delegated: false });
    expect(turnReducer(sent, { type: 'expired', seq: 201 })).toBe(sent);
  });

  it('tells the night plate: sealed while sending and once in, open again with the words on a failure', () => {
    const sending = turnReducer(opened, { type: 'sending', seq: 201 });
    expect(actSent(opened)).toEqual({ sent: null, sendError: null });
    expect(actSent(sending)).toEqual({ sent: 'you', sendError: null });
    const act = (a: Parameters<typeof turnReducer>[1]) => actSent(turnReducer(sending, a));
    expect(act({ type: 'sent', seq: 201, delegated: false })).toEqual({
      sent: 'you',
      sendError: null,
    });
    expect(act({ type: 'sent', seq: 201, delegated: true }).sent).toBe('agent');
    expect(act({ type: 'send-failed', seq: 201, status: 409, message: 'x' })).toEqual({
      sent: 'closed',
      sendError: ALREADY_ANSWERED,
    });
    expect(act({ type: 'send-failed', seq: 201, status: 0, message: 'offline' })).toEqual({
      sent: null,
      sendError: 'offline',
    });
    expect(actSent(turnReducer(opened, { type: 'expired', seq: 201 })).sent).toBe('agent');
  });
});

describe('the turn’s clock and whose line it was', () => {
  it('counts from the arrival to the deadline, or two minutes when the arrival is unknown', () => {
    const end = Date.parse('2026-09-25T10:02:00Z');
    expect(turnClock(null, null, end)).toBeNull();
    expect(turnClock('2026-09-25T10:02:00Z', end - 90_000, end - 30_000)).toEqual({
      remainingMs: 30_000,
      totalMs: 90_000,
    });
    expect(turnClock('2026-09-25T10:02:00Z', null, end - 30_000)).toEqual({
      remainingMs: 30_000,
      totalMs: DEFAULT_TURN_MS,
    });
    expect(turnClock('2026-09-25T10:02:00Z', null, end + 5000)?.remainingMs).toBe(0);
  });

  it('is active while the status says so, or while the request is newer than the status', () => {
    const pending = {
      seq: 201,
      day: 3,
      actionKind: 'discuss' as const,
      candidates: [],
      deadline: null,
    };
    expect(requestIsActive(pending, ME, { pending_seats: [ME], last_seq: 250 })).toBe(true);
    expect(requestIsActive(pending, ME, { pending_seats: [], last_seq: 200 })).toBe(true);
    expect(requestIsActive(pending, ME, { pending_seats: [], last_seq: 201 })).toBe(false);
    expect(requestIsActive(null, ME, { pending_seats: [ME], last_seq: 0 })).toBe(false);
  });

  it('finds the request a line of mine answered', () => {
    const log = [
      ...upTo(200),
      request(201, 'discuss'),
      { seq: 202, day: 3, type: 'speech', player: ME, message: 'x', channel_seq: 40 },
      { seq: 203, day: 3, type: 'speech', player: ME, message: 'y', channel_seq: 41 },
    ] as DurableGameEvent[];
    expect(requestBefore(log, 202, ME)).toBe(201);
    expect(requestBefore(log, 203, ME)).toBeNull();
    expect(requestBefore(log, 200, ME)).toBeNull();
  });
});
