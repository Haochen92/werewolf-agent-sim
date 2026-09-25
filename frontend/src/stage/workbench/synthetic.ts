/**
 * Situations for the scenes that exist only while a game is being played: the night rooms and
 * the seated human's ballot. Their beats are prompts to a seated human (`input_request`), and the fixture game had no
 * human in it, so the log never yields them. To draw them anyway, the workbench takes a real
 * moment of the fixture (a seat, a night, a point in the log), seats a human there, and puts
 * the prompt that seat would have been sent into the view: its candidates are the living
 * seats but the seat itself (and, for a wolf, but the pack), exactly as the server builds
 * them. Everything else on stage is the fixture's own truth at that moment.
 */
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { ActionKind, DurableGameEvent } from '@/types/contracts';
import { BEAT_LABELS, type BeatId, type SceneBeat, type SceneId } from '../beats/types';
import { seatify } from '../roles';
import type { TurnInput } from '../scenes/types';

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
}

/** The two minutes every human prompt gets (ux_journeys: the one timeout rule). */
export const TURN_MS = 120_000;

export interface SyntheticFrame {
  beat: SceneBeat;
  view: GameView;
  me: string;
  turn: TurnInput;
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

export function synthesise(
  s: Situation,
  events: readonly DurableGameEvent[],
): SyntheticFrame {
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
      clock: left === null ? null : { remainingMs: left * 1000, totalMs: TURN_MS },
      chosen: s.chosen ?? null,
      cardOpen: !!s.card,
      draft,
    },
  };
}

/** Every situation of a scene, synthesised. */
export function synthesiseAll(
  situations: readonly Situation[],
  events: readonly DurableGameEvent[],
): SyntheticFrame[] {
  return situations.map((s) => synthesise(s, events));
}
