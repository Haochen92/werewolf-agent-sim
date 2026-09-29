/**
 * What every scene is given, and nothing else (docs/stage_architecture.md §2). A scene reads
 * the folded view for the beat it is on and draws; it never reaches into the store or the
 * stream, which is what lets the replay, the live game and the workbench all mount the same
 * component and differ only in how they choose the beat.
 */
import type { Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { SceneBeat } from '@/stage/beats/types';
import type { DrawerFilters } from '@/stage/drawer/drawer-lines';

export type MotionSpeed = 'normal' | 'fast' | 'skip';

export interface Presentation {
  /** Observer tier on: the film's material exists and the wing wears the truth. */
  xray: boolean;
  /**
   * What the right side holds, one thing at a time: the transcript drawer, the X-ray film, or
   * nothing (null, the slot closed). While it holds something every scene lays its room out
   * narrower (`geometry(hud, true)`); the film exists only with the X-ray on, so `film` with
   * `xray` off reads as closed (see `slotOf` in slot.ts).
   */
  slot: 'drawer' | 'film' | null;
  motion: MotionSpeed;
  /** Which HUD geometry the stage is laid out for. */
  hud: 'live' | 'replay' | 'none';
  /**
   * Who plays which seat: `castForGame(gameId)`, index 0 = `player_1`. Nothing on the wire
   * says it (the log has no game id), so the container that knows the game hands it down.
   */
  cast: readonly Character[];
  /**
   * True when this render is playing forward from the previous beat and should move; false
   * when the viewer arrived here (a seek, a refresh, a reconnect) and the beat renders at rest.
   */
  animate: boolean;
}

export interface SceneProps {
  /** `fold(events.slice(0, beat.end))`: everything the beat may show. */
  view: GameView;
  beat: SceneBeat;
  /** The seated human's seat, or null for a spectator; the role is on `view.me`. */
  me: string | null;
  presentation: Presentation;
  /**
   * The seated human's answer to a prompt (a night act, the pack's vote): the chosen seat, or
   * null for an act that chooses no one (the vigilante's "Hold fire"). The scene only reports
   * it; the live container sends it to the server, the workbench logs it. The waiting room's
   * room reports its plates here too, as a `RoomAct` (`lock`, `unlock`, `close`, `depart`, `leave`).
   */
  onAct?: (target: string | null) => void;
  /** The seated human's line (the pack's chat): reported the same way as `onAct`. */
  onSay?: (text: string) => void;
  /**
   * A tap on the speech box: the viewer has read this page, move on (the replay steps forward,
   * a live game ends the beat's hold, the workbench steps its beat). Without it the box is
   * only read.
   */
  onNext?: () => void;
  /** What the container knows about the open prompt that the log does not; see `TurnInput`. */
  turn?: TurnInput;
  /** What the container holds for the side slot and its two buttons; see `SlotInput`. */
  slot?: SlotInput;
  /** The waiting room, for the platform (`station.*` beats) only; see `RoomInput`. */
  room?: RoomInput;
  /**
   * Live, at the curtain: where "Watch the replay" and "Back to the lobby" go. Without it the
   * two buttons are drawn but go nowhere (the workbench).
   */
  wayOut?: { replay: string; lobby: string };
}

/**
 * The side slot's state that must outlive a beat, held by whoever mounts the scene (the
 * workbench, the replay, the live game): the drawer's filters and the film's open tab (both
 * kept as the viewer steps through turns), and what the Transcript and X-ray buttons do. A
 * scene only passes these on; without them the slot still draws, with default filters.
 */
export interface SlotInput {
  filters?: DrawerFilters;
  onFilters?: (next: DrawerFilters) => void;
  /** The film's open tab: `note`, or a lesson `L1`–`L3`. */
  filmTab?: string;
  onFilmTab?: (tab: string) => void;
  /** Transcript: brings the drawer to the slot, or closes it. */
  onTranscript?: () => void;
  /** X-ray: turns the X-ray on and brings the film, or turns it off. */
  onXray?: () => void;
  /** The replay's way back to its list, a link at the strip's left; live has none. */
  back?: string;
  /**
   * The log folded a little past this beat (the replay: to the next beat, or the whole log).
   * A turn's note is written just after the turn, so the beat's own view never holds it; the
   * film reads it from here. Live has nothing ahead: the note shows once it has arrived.
   */
  ahead?: GameView | null;
}

/**
 * The live side of a prompt, handed in by whoever mounts the scene. The clock runs on real
 * time from the request's `deadline`, which only the container can read (the scene is a pure
 * function of its props); the rest seeds the scene's own choice so the workbench can show a
 * prompt mid-answer at rest.
 */
export interface TurnInput {
  /** Time left and the whole allowance, in ms; null = no deadline (a solo game): no ring. */
  clock?: { remainingMs: number; totalMs: number } | null;
  /** A seat already chosen. */
  chosen?: string | null;
  /** The role card opened over the room. */
  cardOpen?: boolean;
  /**
   * A night act or pack vote is in (the server takes one answer and refuses a second): sent
   * from here ('you'), taken by the seat's agent ('agent'), or refused as already answered
   * ('closed'). Unset: not sent, or the send failed and may be tried again.
   */
  sent?: 'you' | 'agent' | 'closed' | null;
  /** Why the last send failed, in the words to show under the plate. */
  sendError?: string | null;
  /** A line already written in the pack's chat box. */
  draft?: string;
  /**
   * How many are in so far and of how many ("Ballots in, 3 of 7"), from the ephemeral
   * `phase_progress` only the live stream carries; the log never holds it.
   */
  progress?: { n: number; total: number };
  /**
   * The seat's agent answered this seat's turn (the request ran out unanswered, or was handed
   * over), so the line on the stage is the agent's: said on this seat's own screen only.
   */
  agentSpoke?: boolean;
  /** The seated human's speaking turn (`day.your-turn`): what the dock holds and does. */
  dock?: DockInput;
}

/**
 * The speaking turn's dock, live. The container keeps the words (so a draft from notes can
 * land in the box) and talks to the server; the dock only draws them and reports the presses.
 * "Say it" and "Pass" go out through `SceneProps.onSay` and `onAct(null)`.
 */
export interface DockInput {
  /** The line in the box. */
  text: string;
  onText?: (text: string) => void;
  /** The rough notes the seat's agent phrases into a line. */
  notes?: string;
  onNotes?: (notes: string) => void;
  /** Ask for a draft from the notes; without it there is no draft helper. */
  onDraft?: (notes: string) => void;
  /** Drafts left this turn (three per turn). */
  draftsLeft?: number;
  drafting?: boolean;
  /** The line (or the pass) is on its way. */
  sending?: boolean;
  /** What went wrong, in the words to show: the server's own for a refused line. */
  error?: string | null;
  /** Hand the turn to the seat's agent. */
  onDelegate?: () => void;
  /** The turn is no longer this seat's to answer: sent, or run out. */
  closed?: boolean;
}

/**
 * What can be pressed on the waiting room's ledge, reported through `SceneProps.onAct`: the
 * host's lock, close and depart, and everyone else's leave.
 */
export type RoomAct = 'lock' | 'unlock' | 'close' | 'depart' | 'leave';

/**
 * The waiting room before the game, for the platform (`StationScene`). A room has no event log:
 * all of this is the status poll's (`GET /games/{id}` in the `waiting` state) plus what this
 * device holds (the host key, the seat token). The container that
 * polls builds it; the scene only draws it and reports the host's presses.
 */
export interface RoomInput {
  /** The room's name, on the station sign; "" = unnamed. */
  name: string;
  /**
   * The names aboard, in the order they joined (the server's public roster). Nobody has a seat
   * yet: seats and roles are dealt when the game starts, the empty places going to agents.
   */
  aboard: readonly string[];
  /** How many can board (the server's `max_seats`). */
  places: number;
  /** The name shown as the host (the server's: whoever boarded first), or null while nobody has. */
  host: string | null;
  /** Locked: the server admits nobody new, invite link included. */
  locked: boolean;
  /** This device holds the room's host key: the Lock and Depart plates are its. */
  isHost: boolean;
  /** This device holds a seat token for the room (it boarded). */
  seated: boolean;
  /** This viewer's index in `aboard`, as the server places their seat cookie; null without a seat. */
  you: number | null;
  /** The fewest aboard that Depart needs (see `MIN_ABOARD` in scenes/station.ts). */
  minAboard: number;
  /** The address that brings someone to this room, for the invite. */
  link: string;
  /** A press on its way to the server. */
  busy?: RoomAct | null;
  /** What the server said when a press failed, as it said it. */
  error?: string | null;
  /**
   * The hand-off to the deal (`LiveTheatre`): `closing`, the curtain falls over the empty
   * platform; `opening`, only the curtain is left, lifting off the deal's first beat below.
   */
  curtain?: 'closing' | 'opening' | null;
}
