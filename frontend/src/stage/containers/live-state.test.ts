/**
 * The live stage, fed the fixture game one event at a time as a seat would receive it
 * (player_7, the vigilante): history lands still, news plays through the timer at normal speed,
 * prompts wait, game over cuts nothing in before the ending and the X-ray waits for the stage to
 * reach it, and the ending runs to its curtain. Then the answers: the turn's body per request
 * kind, the draft's state, the clock.
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
  seesXray,
  turnClock,
  turnReducer,
  type LiveCtx,
  type LiveState,
  type TurnState,
} from './live-state';
import { nextLiveStep } from './live-queue';

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
  ctx: LiveCtx;
  /** Checks every move of the stage, when set (see `Watch`). */
  watch?: Watch;
  /** The status's last seq at connect: set, the theatre's deal rule is on (`historyLanding`). */
  connectedAt: number | null = null;
  /** The newest seq a reconnect caught up on (the store's `caughtUpTo`). */
  caughtUpTo = 0;
  /** The page watched its platform depart (the theatre's `departedHere`). */
  departed = false;

  constructor(readonly me = ME) {
    this.ctx = ctx({ me });
  }

  beats(): SceneBeat[] {
    const xray = this.events.some((e) => e.type === 'game_over');
    return beatsFor(this.events, { xray, me: this.me, live: true });
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
          : historyLanding(this.events, end, this.connectedAt, this.departed),
      ctx: this.ctx,
    });
    this.watch?.see(this.state);
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
    this.watch?.see(this.state);
    return this;
  }
  /** Time passes: every hold runs out. */
  drain() {
    while (this.state.holding) this.held();
    return this;
  }
  set(over: Partial<LiveCtx>) {
    this.ctx = ctx({ me: this.me, ...over });
    return this.recut();
  }
  get beat() {
    return this.state.beats[this.state.cursor.index];
  }
}

/** A beat's identity: the same beat in any cut of the list. */
const idOf = (b: SceneBeat | undefined): string =>
  b
    ? [b.id, b.seq, b.page?.index, b.subject, b.ordinal, b.spoke?.actor, b.spoke?.step]
        .map((x) => x ?? '')
        .join('|')
    : '';

/**
 * Watches the stage as it moves: a beat played (animated in) is never one played before, and a
 * change that leaves the stage on the beat it is on does not play that beat again.
 */
class Watch {
  played: string[] = [];
  /** Where the stage landed without playing (history, or what the seat lived through). */
  landed: string[] = [];
  private on = '';
  private step = 0;
  see(state: LiveState) {
    const id = idOf(state.beats[state.cursor.index]);
    if (id === this.on) {
      expect(state.step, `${id} played again`).toBe(this.step);
    } else if (state.step !== this.step) {
      if (state.cursor.animate) {
        expect(this.played, `${id} played twice`).not.toContain(id);
        this.played.push(id);
      } else this.landed.push(id);
    }
    this.on = id;
    this.step = state.step;
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
    // past the deal, a backlog of any length plays at normal speed, one beat per hold
    // (2026-10-01; it drained fast from three queued until then)
    while (s.beat.id.startsWith('deal.')) s.held();
    expect(s.state.beats.length - 1 - s.state.cursor.index).toBeGreaterThanOrEqual(2);
    while (s.state.cursor.index < s.state.beats.length - 1) {
      expect(s.state.speed).toBe('normal');
      expect(s.state.holding).toBe(true);
      const at = s.state.cursor.index;
      s.held();
      expect(s.state.cursor).toEqual({ index: at + 1, animate: true });
    }
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

  it('a page that watched its platform depart plays the deal and what followed it, however much the log held (2026-10-01)', () => {
    // a solo game: the agents are well into day 1 by the time the curtain is down
    const s = new Session();
    s.connectedAt = 30;
    s.departed = true;
    expect(upTo(30).some((e) => e.type === 'turn_started')).toBe(true);
    s.arrive(upTo(30), false);
    expect(s.beat.id).toBe('deal.table-seated');
    expect(s.state.cursor.animate).toBe(true);
    const played: string[] = [];
    while (s.state.holding) {
      expect(s.state.speed).toBe('normal');
      played.push(s.beat.id);
      s.held();
    }
    // the deal from its first beat, then every beat after it, in order, none skipped
    expect(played.slice(0, 4)).toEqual([
      'deal.table-seated',
      'deal.cards-dealt',
      'deal.your-card',
      'deal.day-begins',
    ]);
    expect(played).toEqual(s.state.beats.slice(0, played.length).map((b) => b.id));
    expect(s.state.cursor.index).toBe(s.state.beats.length - 1);
    // day 1's first turns: each seat on the stand, thinking, then passing
    expect(played.filter((id) => id === 'day.turn-thinking').length).toBe(3);
    expect(played.filter((id) => id === 'day.pass').length).toBe(2);
    // without the departure the same history lands still on its latest beat
    const q = new Session();
    q.connectedAt = 30;
    q.arrive(upTo(30), false);
    expect(q.state.cursor).toEqual({ index: q.state.beats.length - 1, animate: false });
    // a reconnect later catches up past the connect: that lands still, as anywhere
    s.caughtUpTo = 60;
    s.arrive(
      MINE.filter((e) => e.seq > 30 && e.seq <= 60),
      false,
    );
    expect(s.state.cursor).toEqual({ index: s.state.beats.length - 1, animate: false });
    expect(s.state.holding).toBe(false);
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

  it('the dock never waits for the stage: the beat on stage is cut short once, the rest keep their pace', () => {
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
    // cut short once: the next beat is already on, at normal speed (2026-10-01; fast until then)
    expect(s.state.cursor.index).toBe(holding + 1);
    expect(s.state.speed).toBe('normal');
    expect(s.state.holding).toBe(true);
    // a later recut does not cut its hold again
    const step = s.state.step;
    s.recut();
    expect(s.state.step).toBe(step);
    expect(s.state.holding).toBe(true);
    while (s.beat.id !== 'day.your-turn') {
      expect(s.state.speed).toBe('normal');
      s.held();
    }
    expect(s.beat.seq).toBe(201);
  });

  it('a prompt first seen while the deal is on the stage cuts nothing', () => {
    const s = new Session();
    s.connectedAt = 12;
    s.arrive(upTo(12), false);
    expect(s.beat.id).toBe('deal.table-seated');
    // the first turn is mine, and it is open while the deal plays
    s.ctx = ctx({ openPrompt: 14 });
    s.arrive(
      [...MINE.filter((e) => e.seq === 13), { ...request(14, 'discuss'), day: 1 }],
      true,
    );
    expect(s.beat.id).toBe('deal.table-seated');
    expect(s.state.holding).toBe(true);
    // the deal plays on, beat by beat, and so does what comes after it: no hold is cut
    const before = s.state.step;
    let holds = 0;
    while (s.state.holding) {
      expect(s.state.speed).toBe('normal');
      s.held();
      holds++;
      s.recut(); // later cuts of the list do not cut either
    }
    expect(s.beat).toMatchObject({ id: 'day.your-turn', seq: 14 });
    expect(s.state.step - before).toBe(holds);
  });
});

describe('the live stage: a speech told in pages', () => {
  const page = (seq: number, index: number, count: number): SceneBeat => ({
    id: 'day.speech',
    scene: 'day',
    label: 'Speaks',
    day: 3,
    seq,
    end: seq + 1,
    sees: 'public',
    subject: 'player_2',
    holdMs: 3000,
    ...(count > 1 ? { page: { index, count } } : {}),
  });
  const quiet = { me: null, rolesLanded: false };

  it('plays its pages, and the speeches queued after them, at normal speed', () => {
    // on the stage: a speech's first page; queued: its two more pages and one more speech
    const beats = [page(163, 0, 3), page(163, 1, 3), page(163, 2, 3), page(169, 0, 1)];
    expect(nextLiveStep(beats, 0, quiet)).toEqual({ index: 1, speed: 'normal' });
    // more speeches queued are no backlog to hurry (2026-10-01)
    const more = [...beats, page(176, 0, 2), page(176, 1, 2), page(180, 0, 1)];
    expect(nextLiveStep(more, 0, quiet)?.speed).toBe('normal');
  });

  it('keeps normal speed with my prompt waiting, pages and all', () => {
    const prompt: SceneBeat = {
      ...page(201, 0, 1),
      id: 'day.your-turn',
      seat: ME,
      sees: 'seat',
      liveOnly: true,
      holdMs: 0,
    };
    const beats = [page(163, 0, 2), page(163, 1, 2), prompt];
    expect(nextLiveStep(beats, 0, { me: ME, rolesLanded: false })?.speed).toBe('normal');
  });
});

describe('the live stage: game over', () => {
  const beforeOver = upTo(405);
  const gameOver = ALL.find((e) => e.type === 'game_over')!;
  // the withheld backlog the server sends after game_over (older seqs: history to this page)
  const backlog = ALL.filter((e) => e.seq < gameOver.seq && !seen(e));
  const extracted = ALL.find((e) => e.type === 'memory_extracted')!;

  it('game over cuts nothing in before the ending: the stage goes on from the beat it was on', () => {
    const s = new Session().arrive(beforeOver, false);
    const played = s.state.beats.map(idOf);
    const at = s.state.cursor.index;
    s.arrive([gameOver], true);
    // the X-ray is on, and the withheld backlog lands, but the list up to the ending is the
    // one the viewer played (no face-up deal, no X-ray passes, no other seat's "Only seat n")
    s.arrive(backlog, false);
    const ending = s.state.beats.findIndex((b) => b.id.startsWith('over.'));
    expect(s.state.beats.slice(0, ending).map(idOf)).toEqual(played);
    expect(s.state.beats.some((b) => b.sees === 'xray' || b.aqua)).toBe(false);
    expect(s.state.cursor.index).toBeGreaterThan(at);
    expect(s.beat.id.startsWith('over.')).toBe(true);
  });

  it('the viewer has the X-ray only once the stage reaches the ending (2026-10-01)', () => {
    // night 4 falls as news while the stage is on the lynch; game over lands behind the
    // morning's roll, the stage still in the night
    const s = new Session().arrive(upTo(386), false);
    s.arrive(
      MINE.filter((e) => e.seq > 386 && e.seq < gameOver.seq),
      true,
    );
    s.arrive([gameOver], true).arrive(backlog, false).set({ rolesLanded: true });
    expect(s.beat.id).toBe('night.hub');
    // what the theatre hands the presentation: the X-ray is not the viewer's yet
    expect(seesXray(s.state, true)).toBe(false);
    while (!s.beat.id.startsWith('over.')) {
      expect(seesXray(s.state, true)).toBe(false);
      s.held();
    }
    expect(s.beat.id).toBe('over.where-it-ended');
    expect(seesXray(s.state, true)).toBe(true);
    while (s.beat.id !== 'over.verdict') s.held();
    expect(seesXray(s.state, true)).toBe(true);
    // never without game over, wherever the stage is
    expect(seesXray(s.state, false)).toBe(false);
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

/** What a seat receives while the game runs, as the server entitles it (any seat, not only 7). */
function entitled(me: string) {
  const wolf = ALL.some((e) => e.type === 'role_assigned' && e.player === me && !!e.pack);
  return (e: DurableGameEvent) => {
    if (OBSERVER.has(e.type)) return false;
    if (FACTION.has(e.type)) return wolf;
    if (SEAT.has(e.type)) return 'player' in e && e.player === me;
    return true;
  };
}

describe('the live stage: a beat plays once', () => {
  const gameOver = ALL.find((e) => e.type === 'game_over')!;
  const extracted = ALL.find((e) => e.type === 'memory_extracted')!;

  // an AI seat's line lands, then the next seat's turn while the stage is still reading it: a
  // new cut of the list for every event, and the same beat on the stage through each of them
  it.each([
    ['seat 7', 'player_7'],
    ['a wolf', 'player_3'],
  ])('fed the game one event at a time (%s), no beat is played twice', (_, me) => {
    const mine = ALL.filter(entitled(me));
    // how many holds run out between two events: none (the stage falls behind), a few, all
    for (const holds of [0, 1, 3, Infinity]) {
      const s = new Session(me);
      s.watch = new Watch();
      s.arrive(
        mine.filter((e) => e.seq <= 12),
        false,
      );
      for (const e of mine.filter((e) => e.seq > 12 && e.seq < gameOver.seq)) {
        s.arrive([e], true);
        for (let h = 0; h < holds && s.state.holding; h++) s.held();
      }
      // the ending: game over as news, the withheld backlog, the roles, then the memory
      s.arrive([gameOver], true);
      s.arrive(
        ALL.filter((e) => e.seq < gameOver.seq && !entitled(me)(e)),
        false,
      );
      s.set({ rolesLanded: true }).drain();
      s.arrive([extracted], true).drain();
      s.state = liveReducer(s.state, { type: 'dismiss', ctx: s.ctx });
      s.watch.see(s.state);
      expect(s.beat.id).toBe('over.curtain');
      // every speech was told, page by page, once
      const pages = s.state.beats.filter((b) => b.id === 'day.speech' && b.seq > 12);
      expect(s.watch.played.filter((id) => id.startsWith('day.speech|'))).toHaveLength(
        pages.length,
      );
    }
  });
});

describe('the live stage: what the seat lived through', () => {
  // the fixture with room between its seqs, so a seated human's requests can be put in
  const SPACED = ALL.map((e) => ({ ...e, seq: e.seq * 10 }) as DurableGameEvent);
  const over = SPACED.find((e) => e.type === 'game_over')!;

  /**
   * A seated human's night, as it happens: the log up to `from` as history, then each event
   * as news, the stage reading everything between two events. A request opens the prompt and
   * is answered as soon as the stage is on it (by the seat's agent, for `agent`); `to` is where
   * the news stops, or, past game over, the ending runs to its curtain. With `burst`, the last
   * answer's response is still out while the rest of the night lands at once, the stage not yet
   * moved: the kill, the morning, game over (which closes the prompt).
   */
  function night(
    me: string,
    from: number,
    to: number,
    asks: { seq: number; kind: InputRequest['action_kind']; agent?: boolean }[],
    burst = false,
  ) {
    const s = new Session(me);
    s.watch = new Watch();
    const mine = SPACED.filter(entitled(me));
    s.arrive(
      mine.filter((e) => e.seq <= from),
      false,
    );
    const news = [
      ...mine.filter((e) => e.seq > from && e.seq <= Math.min(to, over.seq)),
      ...asks.map((a) => ({ ...request(a.seq, a.kind), player: me })),
    ].sort((a, b) => a.seq - b.seq);
    const byAgent: number[] = [];
    let waiting = false;
    for (const e of news) {
      const ask = asks.find((a) => a.seq === e.seq);
      if (ask) {
        s.ctx = ctx({ me, openPrompt: ask.seq, byAgent });
        s.arrive([{ ...e, day: s.events.at(-1)!.day }], true).drain();
        expect(s.beat.seq).toBe(ask.seq); // the stage is on the prompt, waiting
        if (ask.agent) byAgent.push(ask.seq);
        if (burst && ask === asks.at(-1)) waiting = true;
        else s.set({ openPrompt: null, byAgent: [...byAgent] });
      } else {
        // game over closes a prompt still open: nothing is asked any more
        if (e.type === 'game_over') s.ctx = ctx({ me, byAgent });
        s.arrive([e], true);
        if (!waiting) s.drain();
      }
    }
    if (to >= over.seq) {
      s.arrive(
        SPACED.filter((e) => e.seq < over.seq && !entitled(me)(e)),
        false,
      );
      s.set({ rolesLanded: true, byAgent }).drain();
    }
    return s;
  }
  const idsOf = (ids: string[], scene: string) =>
    ids
      .filter((id) => id.startsWith(`${scene}.`))
      .map((id) => id.split('|').slice(0, 2).join(' '));

  it('a wolf’s own lines to the pack land still; the packmate’s lines and the kill play, once', () => {
    // night 2, seat 3 at the keyboard: two rounds of talk, then the vote
    const s = night('player_3', 1200, 1590, [
      { seq: 1215, kind: 'wolf_discuss' },
      { seq: 1425, kind: 'wolf_discuss' },
      { seq: 1515, kind: 'wolf_vote' },
    ]);
    expect(idsOf(s.watch!.played, 'pack')).toEqual([
      'pack.your-line 1215',
      'pack.line 1400', // seat 8
      'pack.your-line 1425',
      'pack.line 1460', // seat 8
      'pack.vote 1515',
      'pack.decided 1540',
    ]);
    // the seat's own lines came as the log's copies of what it wrote: at rest, then on
    const news = s.watch!.landed.filter((id) => Number(id.split('|')[1]) > 1200);
    expect(idsOf(news, 'pack')).toEqual(['pack.line 1220', 'pack.line 1430']);
    expect(s.beat.id).toBe('morning.day-begins');
  });

  it('a line the seat’s agent said for it is news: it plays', () => {
    const s = night('player_3', 1200, 1300, [
      { seq: 1215, kind: 'wolf_discuss', agent: true },
    ]);
    expect(idsOf(s.watch!.played, 'pack')).toEqual([
      'pack.your-line 1215',
      'pack.line 1220',
    ]);
  });

  it('the last night: after the kill vote the morning and the ending play; the pack’s night is not told again', () => {
    // night 4, seat 8 hunting alone: the vote, then the kill, the morning and game over at once
    const s = night('player_8', 3870, over.seq, [{ seq: 3935, kind: 'wolf_vote' }], true);
    // game over turned the X-ray on, but a game in play keeps the nights it played
    expect(s.state.beats.some((b) => b.scene === 'rnight')).toBe(false);
    const after = s.watch!.played.map((id) => id.split('|')[0]);
    expect(after.slice(after.indexOf('pack.vote'), after.indexOf('pack.vote') + 3)).toEqual(
      ['pack.vote', 'pack.decided', 'morning.shutter-down'],
    );
    expect(after.filter((id) => id.startsWith('pack.')).length).toBe(2);
    expect(s.beat.id).toBe('over.curtain');
  });

  it('the last night in a room of one’s own: the act plays once, then the morning', () => {
    // night 4, seat 9 the healer at the keyboard
    const s = night(
      'player_9',
      3870,
      over.seq,
      [{ seq: 3885, kind: 'healer_target' }],
      true,
    );
    expect(s.state.beats.some((b) => b.scene === 'rnight')).toBe(false);
    const after = s.watch!.played.map((id) => id.split('|')[0]);
    expect(
      after.slice(after.indexOf('room.opens'), after.indexOf('room.opens') + 2),
    ).toEqual(['room.opens', 'morning.shutter-down']);
    expect(s.beat.id).toBe('over.curtain');
  });
});

describe('the live stage: the side slot', () => {
  it('Transcript brings the drawer or closes it; File brings the film only once the game is over', () => {
    let st = initialLiveState(null);
    st = liveReducer(st, { type: 'transcript' });
    expect(st.slot).toBe('drawer');
    expect(liveReducer(st, { type: 'file', xray: false }).slot).toBe('drawer');
    st = liveReducer(st, { type: 'file', xray: true });
    expect(st.slot).toBe('film');
    expect(liveReducer(st, { type: 'transcript' }).slot).toBe('drawer');
    expect(liveReducer(st, { type: 'file', xray: true }).slot).toBe(null);
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
