/**
 * What every scene is given, and nothing else (docs/stage_architecture.md §2). A scene reads
 * the folded view for the beat it is on and draws; it never reaches into the store or the
 * stream, which is what lets the replay, the live game and the workbench all mount the same
 * component and differ only in how they choose the beat.
 */
import type { Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { SceneBeat } from '@/stage/beats/types';
import type { TurnClock } from '@/stage/countdown';
import type { DrawerFilters } from '@/stage/drawer/drawer-lines';
import type { DrawerScroll } from '@/stage/drawer/use-drawer-filters';
import type { FileChoice } from '@/stage/film/case-file';
import type { NoteEdit } from '@/stage/notebook';

export type MotionSpeed = 'normal' | 'fast';

export interface Presentation {
  /** Observer tier on: the case file exists and the wing wears the truth. */
  xray: boolean;
  /**
   * What the right side holds, one thing at a time: the transcript drawer, the X-ray's case
   * file (`film`, its old name), or nothing (null, the slot closed). While it holds something
   * every scene lays its room out narrower (`geometry(hud, true)`); the file exists only with
   * the X-ray on, so `film` with `xray` off reads as closed (see `slotOf` in slot.ts).
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
  /**
   * The game being played, handed down only by a live game's container: the seated player's
   * notebook (the seat rail's notes and suspect) is kept on this device under it. A replay has
   * none, so its cards are only shown.
   */
  game?: string;
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
  wayOut?: {
    /**
     * The replay, once it is filed; null until then (the run ends after the game does: with
     * memory on, after the lessons are written), and a plaque, "Winding the reels… come back
     * in a few minutes", stands where the link will be.
     */
    replay: string | null;
    lobby: string;
    /** While the replay is not filed: the seats' lessons are still being written. */
    lessons?: boolean;
  };
  /**
   * The replay (and the workbench): move the playhead to the first beat `find` accepts, as a
   * seek (arrived at, at rest). False when no beat does, so the caller can do something else.
   * The night hub's lamps use it to jump to an actor's spoke.
   */
  onSeek?: (find: (beat: SceneBeat) => boolean) => boolean;
  /** The replay's stops (the night hub, the ballots in, and the rooms between); see `StopInput`. */
  stop?: StopInput;
}

/**
 * The replay's stops (owner, 2026-09-30; containers/stops.ts): with the X-ray on the play
 * pauses at the night hub and with the ballots in, and the stage's notice offers the ways on.
 * Handed down by the replay's container (and the workbench); without it the stage draws no
 * stop notice and the hub's lit seats only seek.
 */
export interface StopInput {
  /** The actors (a seat, or `pack`) whose rooms the viewer has been in, this beat's night. */
  visited: readonly string[];
  /** A lit seat at the hub: the first beat `find` accepts (its room), played; its end returns to the hub. */
  onVisit: (find: (beat: SceneBeat) => boolean) => boolean;
  /** The stop's ▶: "Watch them all" at the hub, "Count the votes" with the ballots in. */
  onPlay: () => void;
  /** "End the night": on to the first beat after the night whole. */
  onEndNight: () => void;
  /** A room's "Back to the night": the hub. */
  onBack: () => void;
}

/**
 * The side slot's state that must outlive a beat, held by whoever mounts the scene (the
 * workbench, the replay, the live game): the drawer's filters, the case file's open tab and
 * the seat picked in its chooser (kept as the viewer steps through turns), and what the File
 * and Transcript tabs do. A scene only passes these on; without them the slot still draws,
 * with default filters.
 */
export interface SlotInput {
  filters?: DrawerFilters;
  onFilters?: (next: DrawerFilters) => void;
  /** The case file's open tab: `notes`, `reads`, `precedents` or `findings`. */
  filmTab?: string;
  onFilmTab?: (tab: string) => void;
  /** The seat picked in the case file's chooser (null: none, the beat's own). */
  fileSeat?: FileChoice | null;
  onFileSeat?: (choice: FileChoice | null) => void;
  /** Transcript: brings the drawer to the slot, or closes it. */
  onTranscript?: () => void;
  /** File: brings the film to the slot (only with the X-ray on), or closes it. */
  onFile?: () => void;
  /**
   * Opens one seat's case file in the pane at this beat (the pane switches to File): a tap on a
   * seat at a beat with no speaker, with the X-ray on. Without it the seats are only shown.
   */
  onOpenFile?: (seat: string) => void;
  /** The strip's Reveal switch (the X-ray's one switch): the replay's, which turns it on and off. */
  onReveal?: () => void;
  /**
   * Live: the Reveal switch is drawn but cannot be pressed: locked (true) until the game ends,
   * then shown on (false; the game's end is the switch). Absent with no `onReveal`: no switch.
   */
  revealLocked?: boolean;
  /**
   * Live, a seated player: the strip's door at its far right, which asks before leaving the
   * table (`LeaveConfirm`, held by the container so it outlives the beat). The replay has none.
   */
  onLeave?: () => void;
  /** Where the drawer was scrolled, and whether it follows the beat, kept across scenes. */
  drawerScroll?: DrawerScroll;
  /**
   * The seat notebook's editor: whose notes are open (`useNoteEditing`), held by the container
   * so the editor stays open while beats, scenes and recuts go by (the wing is remounted with
   * them). Without it the wing keeps the open seat itself, for as long as it is mounted.
   */
  notebook?: { editing: NoteEdit | null; onEdit: (edit: NoteEdit | null) => void };
  /**
   * Live only: the finished game's replay, which the closed case file points to after the
   * game ("watch the replay →"). The replay has none: it is the replay.
   */
  replayHref?: string;
  /** The replay's way out (to its list, or wherever the viewer came from), at the strip's
   *  left; live has none. */
  back?: { href: string; label: string };
  /**
   * The log folded a little past this beat (the replay: to the next beat, or the whole log).
   * The case file reads from it whether the game was played with memory (before the first
   * consult) and, at the end, what the game taught. Live has nothing more than the log so far.
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
  /**
   * The deadline and the whole allowance; null = no deadline (a solo game): no ring. The piece
   * that shows the count ticks it, not the scene.
   */
  clock?: TurnClock | null;
  /** A seat already chosen. */
  chosen?: string | null;
  /** The role card opened over the room. */
  cardOpen?: boolean;
  /**
   * Live: "your card" at the foot of the stage was pressed. The container opens the seat's card
   * over the stage and keeps it open across beats (scenes remount); without it the button is
   * only drawn.
   */
  onCard?: () => void;
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
 * The speaking turn's dock, live. The container keeps the words (so a draft can land in the
 * box) and talks to the server; the dock only draws them and reports the presses. "Send" and
 * "Pass" go out through `SceneProps.onSay` and `onAct(null)`. There is no hand-over on this
 * turn: the seat's agent speaks only when the clock runs out.
 */
export interface DockInput {
  /** The line in the box. */
  text: string;
  onText?: (text: string) => void;
  /** The player's optional steer for the seat's agent ("push on seat 5", "softer"). */
  notes?: string;
  onNotes?: (notes: string) => void;
  /**
   * Ask the seat's agent for a draft: its own line, steered by the notes if any; `current` is
   * the line in the box, which the notes revise. Without it there is no draft helper.
   */
  onDraft?: (notes: string, current: string) => void;
  /**
   * "Use my seat notes": whether a draft takes the seat notebook along. Handed in only when
   * the notebook holds a note or a suspect; absent, there is no box to tick.
   */
  notebook?: { shared: boolean; onShared: (shared: boolean) => void };
  /** Drafts left this turn (three per turn). */
  draftsLeft?: number;
  drafting?: boolean;
  /** The line (or the pass) is on its way. */
  sending?: boolean;
  /** What went wrong, in the words to show: the server's own for a refused line. */
  error?: string | null;
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
