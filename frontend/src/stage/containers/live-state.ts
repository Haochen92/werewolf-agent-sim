/**
 * The live game's stage, the pure half: which beat is on the stage and whether it has had its
 * moment yet, and the seated human's open turn (what is typed, the drafts, what was sent). No
 * timers and no network here: the live theatre runs the clock and the requests and hands the
 * results in as actions, so a test can feed a game in one event at a time.
 *
 * How a beat gets on the stage (beat sheet §12, handoff §6):
 *
 * - History (whatever the log already held when the page connected) lands still, on the latest
 *   beat. Nothing plays; a refresh mid-game is silent. So is what a reconnect catches up on.
 * - Except the deal: a new game's first connection finds the deal already dealt (it happens
 *   before the page connects), so while the history holds no turn yet it plays from the first
 *   beat at normal speed, instead of landing on "the day begins". A page that watched its
 *   waiting room depart plays the deal from its first beat whatever the history holds, and the
 *   beats after it play on as a queue (2026-10-01): a solo game's agents are turns ahead by the
 *   time the curtain is down, and this viewer has seen none of it.
 * - News plays. Each new beat animates in and holds for its time at normal speed, then the next
 *   one plays, however many are waiting (live-queue.ts; the backlog drained fast until
 *   2026-10-01). The stage lags the server; that is the design.
 * - A beat that waits for someone holds the stage until the wait is over: a prompt until it is
 *   answered (or gone), the epilogue until its sheet is closed, the curtain for good.
 * - The dock never waits for the stage. When the seated human's prompt is open further down the
 *   queue, the beat on the stage is cut short once (unless it is the deal, which then keeps its
 *   hold and nothing is cut) and the rest play at normal speed up to it.
 * - What the seat lived through at its own prompt (its line to the pack) lands still when the
 *   log's copy of it arrives, and the stage moves on: it is not played a second time.
 * - The winners' stand waits for the roles, which arrive just after `game_over`.
 * - The X-ray is everyone's once the game is over, but the viewer sees it only when the stage
 *   has reached the ending (`seesXray`): the stage may still be playing the last night.
 *
 * The beat list is cut again every time the log grows (and when `game_over` turns the X-ray
 * on), so the stage is carried across by which beat it was on, not by its position.
 */
import { isTextTurn, type TurnPayload } from '@/lib/api';
import type { MeView } from '@/game/types';
import type { SceneBeat } from '@/stage/beats/types';
import type { Presentation } from '@/stage/scenes/types';
import { pressFile, pressTranscript, showFile } from '@/stage/slot';
import type { DurableGameEvent, GameStatus } from '@/types/contracts';
import { nextLiveStep, type LiveContext } from './live-queue';
import { carryAcross, holdFor, still, type Cursor } from './transport';

// --- the stage ----------------------------------------------------------------

export interface LiveCtx extends LiveContext {
  /** The seq of the seated human's request while it is theirs to answer, else null. */
  openPrompt: number | null;
  /** The requests the seat's agent answered for the seated human (`TurnState.byAgent`). */
  byAgent?: readonly number[];
}

export interface LiveState {
  /** The beat list the cursor points into (the last one the theatre handed in). */
  beats: readonly SceneBeat[];
  /** The beat on the stage; -1 before anything is. */
  cursor: Cursor;
  /** How the beat on the stage was played. */
  speed: 'normal' | 'fast';
  /** The beat on the stage is still having its moment (its hold has not run out). */
  holding: boolean;
  /** Counts every step, so the theatre's timer can tell a new hold from an old one. */
  step: number;
  /** The prompt the stage has already hurried toward (so it is hurried once). */
  hurried: number | null;
  slot: Presentation['slot'];
}

/**
 * How the history lands: still (the default), played from the deal (a new game's first
 * connection, or a page that watched its platform depart), or not yet (the history is still
 * arriving and holds no turn yet).
 */
export type Landing = 'still' | 'deal' | 'pending';

export type LiveAction =
  /** The log changed: a new beat list, and how much of the log is history. */
  | {
      type: 'recut';
      beats: readonly SceneBeat[];
      /** `events.slice(0, historyEnd)` arrived as history, not as news. */
      historyEnd: number;
      /** How that history lands; see `historyLanding`. Absent = still. */
      landing?: Landing;
      ctx: LiveCtx;
    }
  /** The hold of step `step` ran out. */
  | { type: 'held'; step: number; ctx: LiveCtx }
  /** The viewer closed the epilogue's sheet. */
  | { type: 'dismiss'; ctx: LiveCtx }
  | { type: 'transcript' }
  /** The strip's File tab. Live, the X-ray is everyone's after game over (the game's end is its
   *  switch), so only the film comes and goes, and only then. */
  | { type: 'file'; xray: boolean }
  /** A seat tapped on the stage after the game: its file comes to the pane. */
  | { type: 'show-file'; xray: boolean };

export function initialLiveState(slot: Presentation['slot'] = null): LiveState {
  return {
    beats: [],
    cursor: still(-1),
    speed: 'normal',
    holding: false,
    step: 0,
    hurried: null,
    slot,
  };
}

/**
 * How many events at the head of the log count as history: everything before the first news,
 * or, after a reconnect, everything up to the newest seq it caught up on (`caughtUpTo`, from
 * the store), since what was missed while away is not played either.
 */
export function historyEnd(
  events: readonly DurableGameEvent[],
  liveSeqs: ReadonlySet<number>,
  caughtUpTo = 0,
): number {
  const i = events.findIndex((e) => liveSeqs.has(e.seq));
  const firstNews = i === -1 ? events.length : i;
  const caught = events.findIndex((e) => e.seq > caughtUpTo);
  return Math.max(firstNews, caught === -1 ? events.length : caught);
}

/**
 * Whether the history is only the deal (beat sheet §12, "the deal on first connection"). The
 * history is all in once news has come after it or it reaches the seq the status reported at
 * connect (`connectedAt`); until then, with no turn in it yet, it is too early to say.
 *
 * A page that watched the platform depart (`departed`) plays from the deal whatever the
 * history holds (beat sheet §1a): the viewer saw none of it. Only what a reconnect later
 * catches up on (past `connectedAt`) lands still, as anywhere.
 */
export function historyLanding(
  events: readonly DurableGameEvent[],
  historyEnd: number,
  connectedAt: number,
  departed = false,
): Landing {
  const history = events.slice(0, historyEnd);
  if (departed && (history.at(-1)?.seq ?? 0) <= connectedAt) return 'deal';
  if (history.some((e) => e.type === 'turn_started')) return 'still';
  const allIn = historyEnd < events.length || (history.at(-1)?.seq ?? 0) >= connectedAt;
  return allIn ? 'deal' : 'pending';
}

/**
 * Whether the viewer sees the X-ray: the game is over (`over`, the log's `game_over`) and the
 * stage has reached its ending, the first `over.*` beat. Until then the Reveal switch stays
 * locked, the File tab shut and the wing without the truth, though the log already holds it:
 * `game_over` can land while the stage is still playing the last night (2026-10-01).
 */
export function seesXray(state: LiveState, over: boolean): boolean {
  if (!over) return false;
  const ending = state.beats.findIndex((b) => b.id.startsWith('over.'));
  return ending !== -1 && state.cursor.index >= ending;
}

function sameBeat(a: SceneBeat | undefined, b: SceneBeat | undefined): boolean {
  return (
    !!a &&
    !!b &&
    a.id === b.id &&
    a.seq === b.seq &&
    a.ordinal === b.ordinal &&
    a.subject === b.subject &&
    a.spoke?.actor === b.spoke?.actor &&
    a.spoke?.step === b.spoke?.step &&
    a.page?.index === b.page?.index
  );
}

/** Where the cursor lands in a new cut of the list, and whether it is still on the same beat. */
function carry(
  from: readonly SceneBeat[],
  to: readonly SceneBeat[],
  cursor: Cursor,
): { cursor: Cursor; same: boolean } {
  if (cursor.index < 0) return { cursor, same: true };
  const was = from[cursor.index];
  if (sameBeat(to[cursor.index], was)) return { cursor, same: true };
  const moved = carryAcross(cursor, from, to);
  return sameBeat(to[moved.index], was)
    ? { cursor: { index: moved.index, animate: cursor.animate }, same: true }
    : { cursor: moved, same: false };
}

/** A beat that holds the stage until something happens, rather than for a time. */
function waitsHere(beat: SceneBeat, ctx: LiveCtx): boolean {
  if (holdFor(beat, 'normal') !== null) return false;
  if (beat.liveOnly) return ctx.openPrompt === beat.seq; // answered or gone: on with the game
  return true; // the epilogue until its sheet is closed; the curtain
}

function promptAhead(state: LiveState, ctx: LiveCtx): boolean {
  if (ctx.openPrompt === null) return false;
  return state.beats.some(
    (b, i) =>
      i > state.cursor.index && b.liveOnly && b.seat === ctx.me && b.seq === ctx.openPrompt,
  );
}

/**
 * The seat's own line to the pack, written on this screen at its prompt (`pack.your-line`): the
 * seat lived it as it wrote it, so the log's copy of it lands still instead of playing again. A
 * line the seat's agent said for it (the prompt ran out, or was handed over) is news, and plays.
 */
function livedThrough(beats: readonly SceneBeat[], index: number, ctx: LiveCtx): boolean {
  const beat = beats[index];
  if (beat?.id !== 'pack.line' || !ctx.me || beat.subject !== ctx.me) return false;
  for (let i = index - 1; i >= 0; i--) {
    const b = beats[i];
    if (b.id === 'pack.line' && b.subject === ctx.me) return false; // that prompt's line came already
    if (b.id === 'pack.your-line' && b.seat === ctx.me)
      return !(ctx.byAgent ?? []).includes(b.seq);
  }
  return false;
}

function play(state: LiveState, index: number, speed: 'normal' | 'fast'): LiveState {
  const beat = state.beats[index];
  return {
    ...state,
    cursor: { index, animate: true },
    speed,
    holding: holdFor(beat, speed) !== null,
    step: state.step + 1,
  };
}

/** Move on if the beat on the stage has had its moment and nothing it waits for is pending. */
function advance(state: LiveState, ctx: LiveCtx): LiveState {
  // the dock never waits for the stage: the beat on the stage when my prompt is first seen
  // ahead is cut short, once per prompt (a deal beat keeps its hold, and nothing is cut)
  const current = state.beats[state.cursor.index];
  if (promptAhead(state, ctx) && state.hurried !== ctx.openPrompt) {
    const cut = state.holding && !current?.id.startsWith('deal.');
    state = { ...state, holding: cut ? false : state.holding, hurried: ctx.openPrompt };
  }
  if (state.holding) return state;
  if (current && waitsHere(current, ctx)) return state;
  const next = nextLiveStep(state.beats, state.cursor.index, ctx);
  if (!next) return state;
  // what the seat already lived through lands still, and the stage moves on
  if (livedThrough(state.beats, next.index, ctx))
    return advance(
      { ...state, cursor: still(next.index), holding: false, step: state.step + 1 },
      ctx,
    );
  return play(state, next.index, next.speed);
}

export function liveReducer(state: LiveState, action: LiveAction): LiveState {
  switch (action.type) {
    case 'recut': {
      const { beats, ctx } = action;
      const carried = carry(state.beats, beats, state.cursor);
      const landing = action.landing ?? 'still';
      let next: LiveState = {
        ...state,
        beats,
        cursor: carried.cursor,
        holding: carried.same ? state.holding : false,
      };
      // the epilogue lands after the curtain is up (memory is extracted after game over): play it
      const at = next.cursor.index;
      if (
        beats[at]?.id === 'over.curtain' &&
        beats[at - 1]?.id === 'over.epilogue' &&
        beats[at - 1].end > action.historyEnd &&
        !state.beats.some((b) => b.id === 'over.epilogue')
      ) {
        next = play(next, at - 1, 'normal');
      }
      // too early to say whether this is a new game's deal: wait for the rest of the history
      if (landing === 'pending') return next;
      // history lands still, on the latest beat it reaches; nothing of it plays (the deal, and
      // after a departure here what followed it, play from the first beat)
      let floor = -1;
      if (landing === 'still')
        for (let i = 0; i < beats.length; i++)
          if (beats[i].end <= action.historyEnd) floor = i;
      if (floor > next.cursor.index)
        next = { ...next, cursor: still(floor), holding: false, step: next.step + 1 };
      return advance(next, ctx);
    }
    case 'held':
      if (action.step !== state.step || !state.holding) return state;
      return advance({ ...state, holding: false }, action.ctx);
    case 'dismiss': {
      if (state.beats[state.cursor.index]?.id !== 'over.epilogue') return state;
      const next = nextLiveStep(state.beats, state.cursor.index, action.ctx);
      // the curtain was down under the sheet (it is usually up before the memory lands): it is
      // there when the sheet is closed, not played again
      return next
        ? { ...state, cursor: still(next.index), holding: false, step: state.step + 1 }
        : state;
    }
    case 'transcript':
      // the film only exists with the X-ray, so read the slot as the X-ray would
      return { ...state, slot: pressTranscript({ slot: state.slot, xray: true }).slot };
    case 'file':
      return { ...state, slot: pressFile({ slot: state.slot, xray: action.xray }).slot };
    case 'show-file':
      return { ...state, slot: showFile({ slot: state.slot, xray: action.xray }).slot };
  }
}

// --- the seated human's turn -----------------------------------------------------

/** The server's cap on drafts per turn (ux_journeys D25). */
export const DRAFTS_PER_TURN = 3;

export interface TurnState {
  /** The request all of this belongs to; a new request starts afresh. */
  seq: number | null;
  /** The line in the box. */
  text: string;
  /** The steer a draft is written with; empty = the agent writes its own line. */
  notes: string;
  /** Whether a draft takes the seat notebook along ("Use my seat notes"; ticked to start). */
  shareNotebook: boolean;
  draftsLeft: number;
  /** The deadline a draft came back with (the wait credited back); undefined = none yet. */
  deadline?: string | null;
  drafting: boolean;
  sending: boolean;
  /** What went wrong, in words the dock shows as they are. */
  error: string | null;
  /** This client answered the request, or learned it was already answered. */
  answered: boolean;
  /** Requests the seat's agent answered: run out unanswered, or handed over. Kept all game. */
  byAgent: readonly number[];
}

export type TurnAction =
  | { type: 'open'; seq: number }
  | { type: 'text'; text: string }
  | { type: 'notes'; notes: string }
  | { type: 'share-notebook'; share: boolean }
  | { type: 'drafting'; seq: number }
  | {
      type: 'drafted';
      seq: number;
      draft: string;
      draftsLeft: number;
      deadline: string | null;
    }
  | { type: 'draft-failed'; seq: number; status: number; message: string }
  | { type: 'sending'; seq: number }
  | { type: 'sent'; seq: number; delegated: boolean }
  | { type: 'send-failed'; seq: number; status: number; message: string }
  /** The request's deadline passed and this client had not answered it. */
  | { type: 'expired'; seq: number };

export const initialTurnState: TurnState = {
  seq: null,
  text: '',
  notes: '',
  shareNotebook: true,
  draftsLeft: DRAFTS_PER_TURN,
  drafting: false,
  sending: false,
  error: null,
  answered: false,
  byAgent: [],
};

export const ALREADY_ANSWERED = 'That turn was already answered.';
export const DRAFT_FAILED = 'Could not draft the line; type it instead.';
export const AGENT_WOULD_PASS = 'Your agent would pass here. Pass, or tell it what to say.';

export function turnReducer(state: TurnState, action: TurnAction): TurnState {
  if (action.type === 'open') {
    if (action.seq === state.seq) return state;
    return { ...initialTurnState, seq: action.seq, byAgent: state.byAgent };
  }
  if (action.type === 'text') return { ...state, text: action.text };
  if (action.type === 'notes') return { ...state, notes: action.notes };
  if (action.type === 'share-notebook') return { ...state, shareNotebook: action.share };
  // everything below answers a request: an answer to an older one is dropped
  if (action.seq !== state.seq) return state;
  switch (action.type) {
    case 'drafting':
      return { ...state, drafting: true, error: null };
    case 'drafted':
      // an empty draft: the agent would pass, and the box keeps what it had
      return {
        ...state,
        drafting: false,
        text: action.draft || state.text,
        draftsLeft: action.draftsLeft,
        deadline: action.deadline,
        error: action.draft ? null : AGENT_WOULD_PASS,
      };
    case 'draft-failed':
      // 409: the turn is gone or its drafts are used up; 422: the notes refused (too long).
      // The server's words say which. Anything else (503, no helper, no network): type it.
      return action.status === 409
        ? { ...state, drafting: false, draftsLeft: 0, error: action.message }
        : {
            ...state,
            drafting: false,
            error: action.status === 422 ? action.message : DRAFT_FAILED,
          };
    case 'sending':
      return { ...state, sending: true, error: null };
    case 'sent':
      return {
        ...state,
        sending: false,
        answered: true,
        byAgent: action.delegated ? [...state.byAgent, action.seq] : state.byAgent,
      };
    case 'send-failed':
      // 409: someone (the agent, on the deadline) already answered; 422: the engine's words
      return action.status === 409
        ? { ...state, sending: false, answered: true, error: ALREADY_ANSWERED }
        : { ...state, sending: false, error: action.message };
    case 'expired':
      if (state.answered || state.sending) return state;
      return { ...state, answered: true, byAgent: [...state.byAgent, action.seq] };
  }
}

/**
 * Where a night act or pack vote stands, for the plate: in (from here, or the seat's agent),
 * refused as already answered (409), or open with the last send's failure to show.
 */
export function actSent(t: TurnState): {
  sent: 'you' | 'agent' | 'closed' | null;
  sendError: string | null;
} {
  if (t.sending) return { sent: 'you', sendError: null };
  if (t.answered)
    return t.error
      ? { sent: 'closed', sendError: t.error }
      : { sent: t.byAgent.includes(t.seq ?? -1) ? 'agent' : 'you', sendError: null };
  return { sent: null, sendError: t.error };
}

// --- answering -------------------------------------------------------------------

/** What a scene reports: a line, a seat (null = the act that names no one), or the agent. */
export type Answer = { say: string } | { act: string | null } | { delegate: true };

/** The choices the server lists that are not seats (never guessed: only if listed). */
const SENTINELS = ['abstain', 'hold_fire', 'no_target'];

/**
 * The turn's body for the answer, by the request's kind (build_plan §5), or null when the
 * answer does not fit it (an empty line; a seat the server did not offer).
 *
 *   discuss      → `{message}`, or `{pass_turn: true}` for a pass
 *   wolf_discuss → `{message}` only
 *   the rest     → `{target}` from `candidates`; "no one" is the listed abstain or hold fire
 *   any kind     → `{delegate: true}`, the seat's agent answers
 */
export function payloadFor(
  pending: Pick<NonNullable<MeView['pending']>, 'actionKind' | 'candidates'>,
  answer: Answer,
): TurnPayload | null {
  if ('delegate' in answer) return { delegate: true };
  const kind = pending.actionKind;
  if ('say' in answer) {
    const message = answer.say.trim();
    return isTextTurn(kind) && message ? { message } : null;
  }
  if (kind === 'discuss') return answer.act === null ? { pass_turn: true } : null;
  if (kind === 'wolf_discuss') return null;
  if (answer.act === null) {
    const none = pending.candidates.find((c) => SENTINELS.includes(c));
    return none ? { target: none } : null;
  }
  return pending.candidates.includes(answer.act) ? { target: answer.act } : null;
}

/**
 * The v1 rule for whether the folded request is still this seat's to answer: the status says
 * so, or the request arrived after the status was taken (the poll has not caught up yet).
 */
export function requestIsActive(
  pending: MeView['pending'],
  me: string | null,
  status: Pick<GameStatus, 'pending_seats' | 'last_seq'> | undefined,
): boolean {
  return Boolean(
    pending &&
    me &&
    ((status?.pending_seats ?? []).includes(me) || pending.seq > (status?.last_seq ?? 0)),
  );
}

/** The allowance assumed when the request's arrival is unknown (it came as history). */
export const DEFAULT_TURN_MS = 120_000;

/**
 * The clock for a request: what is left of it and of how much, in server time. Null with no
 * deadline (a solo game: no ring). The whole is from the request's arrival to its deadline.
 */
export function turnClock(
  deadline: string | null,
  arrivedAt: number | null,
  now: number,
): { remainingMs: number; totalMs: number } | null {
  if (!deadline) return null;
  const end = Date.parse(deadline);
  if (Number.isNaN(end)) return null;
  const remainingMs = Math.max(0, end - now);
  const whole = arrivedAt !== null && end > arrivedAt ? end - arrivedAt : DEFAULT_TURN_MS;
  return { remainingMs, totalMs: Math.max(whole, remainingMs) };
}

/**
 * The request a line of mine answered: my last `input_request` before it, as long as no
 * earlier line of mine answered that one already. Null for a line nobody asked me for.
 */
export function requestBefore(
  events: readonly DurableGameEvent[],
  seq: number,
  me: string | null,
): number | null {
  if (!me) return null;
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    if (e.seq >= seq) continue;
    if (e.type === 'input_request' && e.player === me) return e.seq;
    if (e.type === 'speech' && e.player === me) return null;
  }
  return null;
}

/**
 * The curtain's way to the replay (beat sheet §10, 2026-10-01). The replay is filed when the
 * engine's run ends, which with memory on is after the lessons are written, a minute or more
 * after `game_over`; a link before then finds nothing. It is filed once the archive answers for
 * it (`answered`) or the status comes from the game's row (`archived`; a game leaves the live
 * registry only when nobody is watching it, so a page at the curtain learns it from the
 * archive). Until then there is no link but the plaque, and, while a memory-on game's lessons
 * have not come in, the line that says they are being written.
 */
export function curtainReplay(
  gameId: string,
  a: { archived: boolean; answered: boolean; memory: boolean; taught: boolean },
): { replay: string | null; lessons: boolean } {
  const filed = a.archived || a.answered;
  return {
    replay: filed ? `/replays/${gameId}` : null,
    lessons: !filed && a.memory && !a.taught,
  };
}
