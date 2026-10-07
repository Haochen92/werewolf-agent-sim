/**
 * Situations for the scenes that exist only while a game is being played: the night rooms and
 * the seated human's ballot. Their beats are prompts to a seated human (`input_request`), and the fixture game had no
 * human in it, so the log never yields them. To draw them anyway, the workbench takes a real
 * moment of the fixture (a seat, a night, a point in the log), seats a human there, and puts
 * the prompt that seat would have been sent into the view: its candidates are the living
 * seats but the seat itself (and, for a wolf, but the pack), exactly as the server builds
 * them. Everything else on stage is the fixture's own truth at that moment.
 *
 * The waiting room (the platform) has no log at all: a room is only the status poll's roster,
 * so its situations are the room itself (`RoomSituation`), drawn over an empty view.
 */
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { ActionKind, DurableGameEvent } from '@/types/contracts';
import { BEAT_LABELS, type BeatId, type SceneBeat, type SceneId } from '../beats/types';
import { seatify } from '../roles';
import { nightUnits } from '../scenes/NightLobbyScene';
import { MIN_ABOARD, stationBeat, type StationBeatId } from '../scenes/station';
import type { RoomInput, TurnInput } from '../scenes/types';

export interface Situation {
  /** What the stepper calls it: "healer, night 2". */
  label: string;
  /** The seat the human sits in. */
  me: string;
  /** The night (its day number), or the day of the vote. */
  day: number;
  /** The request open on the seat; null for a beat with no prompt (a packmate's line). */
  actionKind: ActionKind | null;
  /** Fold the log up to and including this seq; default the night's (or the vote's) `phase_change`. */
  at?: number;
  /** The beat to draw; default from the request (`room.opens`, `pack.your-line`, `pack.vote`). */
  beat?: BeatId;
  /** A doll already chosen. */
  chosen?: string;
  /** The role card open over the room. */
  card?: boolean;
  /** Seconds left of the two minutes (default 74, bench 70's "1:14"); null = no deadline. */
  left?: number | null;
  /** The act is in (the chosen doll, or none: the vigilante held fire). */
  sent?: boolean;
  /** The send failed with these words. */
  sendError?: string;
  /** How many have acted tonight (the live count, `phase_progress`); the pill shows once sent. */
  acted?: number;
}

/**
 * A waiting room, for the platform: which of its beats, and the room as the status poll and this
 * device would give it (the invite link and the minimum aboard are the workbench's own).
 */
export interface RoomSituation {
  label: string;
  beat: StationBeatId;
  room: Omit<RoomInput, 'minAboard' | 'link'>;
}

export type AnySituation = Situation | RoomSituation;

export function isRoomSituation(s: AnySituation): s is RoomSituation {
  return 'room' in s;
}

/** The invite the workbench's rooms show: the fixture game's own address. */
const ROOM_LINK = 'https://wolf.liuhaochen.com/games/9369a5c1-3c28-42ce-86a1-9d594dfa4804';

/** The two minutes every human prompt gets (ux_journeys: the one timeout rule). */
export const TURN_MS = 120_000;

/** The server time a frame's clock is held at: its count is still, `left` before its deadline. */
export const STILL_AT = Date.parse('2026-09-25T10:00:00Z');

export interface SyntheticFrame {
  beat: SceneBeat;
  view: GameView;
  /** The seated human; null on the platform (nobody has a seat before the deal). */
  me: string | null;
  turn: TurnInput;
  /** The waiting room, for the platform's situations. */
  room?: RoomInput;
}

function beatFor(kind: ActionKind | null): BeatId {
  if (kind === 'vote') return 'vote.your-ballot';
  if (kind === 'wolf_discuss') return 'pack.your-line';
  if (kind === 'wolf_vote') return 'pack.vote';
  return 'room.opens';
}

/**
 * The living seats the server would offer this seat: not itself, and for a wolf's night vote
 * not the pack. A day vote also offers `abstain` (Agents/turn/action_space.py).
 */
export function candidatesFor(
  view: GameView,
  me: string,
  kind: ActionKind | null = null,
): string[] {
  if (kind === 'vote') return [...view.alive.filter((s) => s !== me), 'abstain'];
  const pack = view.me.role?.role === 'wolf' ? view.packRoster : [];
  return view.alive.filter((s) => s !== me && !pack.includes(s));
}

/** A waiting room on the platform: no log, so an empty view under the room. */
export function synthesiseRoom(s: RoomSituation): SyntheticFrame {
  return {
    beat: stationBeat(s.beat),
    view: foldEvents([]),
    me: null,
    turn: {},
    room: { ...s.room, minAboard: MIN_ABOARD, link: ROOM_LINK },
  };
}

export function synthesise(
  s: AnySituation,
  events: readonly DurableGameEvent[],
): SyntheticFrame {
  if (isRoomSituation(s)) return synthesiseRoom(s);
  const phase = s.actionKind === 'vote' ? 'voting' : 'night';
  const nightStart = events.find(
    (e) => e.type === 'phase_change' && e.phase === phase && e.day === s.day,
  );
  const at = s.at ?? nightStart?.seq ?? 0;
  const end = events.findIndex((e) => e.seq > at);
  const cut = end < 0 ? events.length : end;
  const folded = foldEvents(events.slice(0, cut), { mySeat: s.me });
  const pending = s.actionKind
    ? {
        seq: at,
        day: s.day,
        actionKind: s.actionKind,
        candidates: candidatesFor(folded, s.me, s.actionKind),
        deadline: null,
        round: null,
      }
    : null;
  const view: GameView = { ...folded, me: { ...folded.me, pending } };

  const id = s.beat ?? beatFor(s.actionKind);
  const anchor = events[cut - 1];
  const subject =
    id === 'pack.line' && anchor?.type === 'wolf_message'
      ? anchor.wolf
      : id === 'pack.decided'
        ? (view.days[s.day]?.night?.wolfKill ?? undefined)
        : undefined;
  const beat: SceneBeat = {
    id,
    scene: id.split('.')[0] as SceneId,
    label: BEAT_LABELS[id],
    day: s.day,
    seq: at,
    end: cut,
    sees: id.startsWith('pack.') ? 'faction' : 'seat',
    seat: s.me,
    subject,
    holdMs: 0,
    liveOnly: true,
  };

  // a wolf's line to write: what the fixture's agent said next, as a person would type it
  let draft: string | undefined;
  if (s.actionKind === 'wolf_discuss') {
    const next = events
      .slice(cut)
      .find((e) => e.type === 'wolf_message' && e.wolf === s.me && e.day === s.day);
    if (next?.type === 'wolf_message') draft = seatify(next.message);
  }

  const left = s.left === undefined ? 74 : s.left;
  return {
    beat,
    view,
    me: s.me,
    turn: {
      clock:
        left === null
          ? null
          : {
              deadline: new Date(STILL_AT + left * 1000).toISOString(),
              totalMs: TURN_MS,
              at: STILL_AT,
            },
      chosen: s.chosen ?? null,
      cardOpen: !!s.card,
      draft,
      sent: s.sent ? 'you' : null,
      progress: s.acted === undefined ? undefined : { n: s.acted, total: nightUnits(view) },
      sendError: s.sendError ?? null,
    },
  };
}

/** Every situation of a scene, synthesised. */
export function synthesiseAll(
  situations: readonly AnySituation[],
  events: readonly DurableGameEvent[],
): SyntheticFrame[] {
  return situations.map((s) => synthesise(s, events));
}
