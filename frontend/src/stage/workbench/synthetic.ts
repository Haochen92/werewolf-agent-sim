/**
 * Situations for the scenes that exist only while a game is being played: the night rooms and
 * the seated human's ballot. Their beats are prompts to a seated human (`input_request`), and the bundled games had no
 * human in them, so the log never yields them. To draw them anyway, the workbench takes a real
 * moment of a bundled game (a seat, a night, a point in the log), seats a human there, and puts
 * the prompt that seat would have been sent into the view: its candidates are the living
 * seats but the seat itself (and, for a wolf, but the pack), exactly as the server builds
 * them. Everything else on stage is that game's own truth at that moment.
 *
 * The waiting room (the platform) has no log at all: a room is only the status poll's roster,
 * so its situations are the room itself (`RoomSituation`), drawn over an empty view.
 */
import type { Character } from '@/assets/manifest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { ActionKind, DurableGameEvent } from '@/types/contracts';
import { BEAT_LABELS, type BeatId, type SceneBeat, type SceneId } from '../beats/types';
import { isPackRole, seatify } from '../roles';
import { nightUnits } from '../scenes/NightLobbyScene';
import { MIN_ABOARD, stationBeat, type StationBeatId } from '../scenes/station';
import type { RoomInput, TurnInput } from '../scenes/types';
import { castForGame } from '../cast/castForGame';
import {
  FIXTURE_CAST,
  FIXTURE_EVENTS,
  FIXTURE_GAME_ID,
  PHASE3_GAME,
  PHASE3_NECRO_GAME,
} from './fixture';

/** The games a situation may be drawn from instead of the workbench's (`Situation.game`). */
const GAMES = {
  phase3: PHASE3_GAME,
  'phase3-necro': PHASE3_NECRO_GAME,
  '9369a5c1': { id: FIXTURE_GAME_ID, events: FIXTURE_EVENTS, cast: FIXTURE_CAST },
} as const;

export interface Situation {
  /** What the stepper calls it: "healer, night 2". */
  label: string;
  /** The seat the human sits in. */
  me: string;
  /**
   * The game to draw it from, with that game's cast: a ten-seat game (the Phase 3 kinds:
   * ten-seat pass §2) or the nine-seat fixture; absent = the game the workbench was handed.
   */
  game?: keyof typeof GAMES;
  /** The night (its day number), or the day of the vote. */
  day: number;
  /** The request open on the seat; null for a beat with no prompt (a packmate's line). */
  actionKind: ActionKind | null;
  /** Fold the log up to and including this seq; default the night's (or the vote's) `phase_change`. */
  at?: number;
  /** The beat to draw; default from the request (`room.opens`, `pack.your-line`, `pack.vote`). */
  beat?: BeatId;
  /** A doll already chosen (or a side, or `conceal`). */
  chosen?: string;
  /** A necromancer's body already chosen. */
  body?: string;
  /** A fortune teller's role already named. */
  roleNamed?: string;
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

/** The invite the workbench's rooms show: the nine-seat fixture game's own address. */
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
  /** The cast of the game the situation was drawn from, when it is not the workbench's. */
  cast?: readonly Character[];
  /** That game's id, when it is not the workbench's. */
  gameId?: string;
}

function beatFor(kind: ActionKind | null): BeatId {
  if (kind === 'vote') return 'vote.your-ballot';
  if (kind === 'wolf_discuss') return 'pack.your-line';
  if (kind === 'wolf_vote' || kind === 'carrier_kill') return 'pack.vote';
  return 'room.opens';
}

/** The no-action word each kind lists after its seats (Agents/schemas/roles.py `no_action`). */
const NO_ACTION_OF: Partial<Record<ActionKind, string>> = {
  investigator_target: 'no_check',
  sentinel_target: 'no_watch',
  vigilante_target: 'hold_fire',
  sigil_target: 'keep_sigil',
  necromancer_target: 'stay_put',
};

/**
 * What the server would offer this seat (Agents/turn/action_space.py): the living seats but
 * itself, and for the pack's kill and a wolf's skill not the pack; a day vote also offers
 * `abstain`, a role with a no-action word lists it last (the nine-seat game listed only the
 * vigilante's), a fortune teller its own seat while it has a self-bet. The conceal and the
 * speculator's pick offer words, not seats.
 */
export function candidatesFor(
  view: GameView,
  me: string,
  kind: ActionKind | null = null,
): string[] {
  if (kind === 'vote') return [...view.alive.filter((s) => s !== me), 'abstain'];
  if (kind === 'conceal') return ['conceal', 'no_conceal'];
  if (kind === 'speculator_pick')
    return ['town', 'wolves', 'lone_killer', 'self', 'not_yet'];
  const pack = isPackRole(view.me.role?.role) ? view.packRoster : [];
  const seats = view.alive.filter((s) => s !== me && !pack.includes(s));
  if (kind === 'bet_target' && (view.me.role?.uses ?? 0) > 0) seats.push(me);
  // the nine-seat game listed only the vigilante's hold fire; the ten-seat one says its lineup
  const none =
    kind && (kind === 'vigilante_target' || view.lineup.length > 0)
      ? NO_ACTION_OF[kind]
      : null;
  return none ? [...seats, none] : seats;
}

/** A waiting room on the platform: no log, so an empty view under the room. */
export function synthesiseRoom(s: RoomSituation): SyntheticFrame {
  return {
    beat: stationBeat(s.beat),
    view: foldEvents([]),
    me: null,
    turn: {},
    room: { ...s.room, minAboard: MIN_ABOARD, link: ROOM_LINK },
    // one puppet per place, as the live platform casts the room's size (the fixture's nine first)
    cast: castForGame(FIXTURE_GAME_ID, s.room.places),
  };
}

export function synthesise(
  s: AnySituation,
  events: readonly DurableGameEvent[],
): SyntheticFrame {
  if (isRoomSituation(s)) return synthesiseRoom(s);
  if (s.game) events = GAMES[s.game].events;
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
        // a necromancer acts through the dead whose bodies were not concealed
        bodies:
          s.actionKind === 'necromancer_target'
            ? folded.dead.filter((d) => d.role !== null).map((d) => d.player)
            : [],
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
      body: s.body ?? null,
      roleNamed: s.roleNamed ?? null,
      cardOpen: !!s.card,
      draft,
      sent: s.sent ? 'you' : null,
      progress: s.acted === undefined ? undefined : { n: s.acted, total: nightUnits(view) },
      sendError: s.sendError ?? null,
    },
    ...(s.game ? { cast: GAMES[s.game].cast, gameId: GAMES[s.game].id } : {}),
  };
}

/** Every situation of a scene, synthesised. */
export function synthesiseAll(
  situations: readonly AnySituation[],
  events: readonly DurableGameEvent[],
): SyntheticFrame[] {
  return situations.map((s) => synthesise(s, events));
}
