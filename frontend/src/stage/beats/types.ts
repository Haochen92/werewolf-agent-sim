/**
 * A beat is the unit of time on the stage: one thing happening, with a name a viewer can
 * read ("A chip is counted") and a hold. The log's events are too fine (a turn is three or
 * four of them) and too coarse (one `night_result` is a whole morning told chip by chip), so
 * `beatsFor` cuts the log into these instead. The list is the source of truth for the replay's
 * transport, the live queue and the workbench alike; `docs/beat_sheet.md` is the same table in
 * prose, and the goldens next to this file hold them to each other.
 */

/** Who has the beat. Public is everyone; seat and faction are private live; xray is observer-tier. */
export type Tier = 'public' | 'seat' | 'faction' | 'xray';

export type SceneId =
  | 'station'
  | 'deal'
  | 'day'
  | 'vote'
  | 'lynch'
  | 'night'
  | 'room'
  | 'pack'
  | 'morning'
  | 'rnight'
  | 'over';

export type ChapterKind = 'day' | 'vote' | 'night' | 'morning' | 'over';

/** A mark on the seek bar; `n` is the day number (0 for game over). */
export interface Chapter {
  kind: ChapterKind;
  n: number;
}

/** The beat ids, with the line the transport shows for each. Ids are `scene.beat`. */
export const BEAT_LABELS = {
  // the waiting room, before the game: live only, from the status poll (no event anchors them)
  'station.waiting': 'Waiting on the platform',
  'station.locked': 'The room is locked',
  'station.departing': 'All aboard',

  'deal.table-seated': 'The table is seated',
  'deal.cards-dealt': 'The cards are dealt',
  'deal.your-card': 'Your card',
  'deal.your-pack': 'Your pack',
  'deal.face-up': 'The deal, face up',
  'deal.day-begins': 'The day begins',

  'day.turn-thinking': 'Thinking',
  'day.speech': 'Speaks',
  'day.pass': 'Passes',
  'day.your-turn': 'Your turn',

  'vote.opens': 'Voting opens',
  'vote.your-ballot': 'Your ballot',
  'vote.ballots-drop': 'The ballots drop',
  'vote.closes': 'Voting closes',
  'vote.count-begins': 'The count begins',
  'vote.chip-counted': 'A chip is counted',
  'vote.result': 'The result',
  'vote.table-down': 'The table goes down',

  'lynch.stand-returns': 'The stand returns',
  'lynch.named': 'Voted out',
  'lynch.drop': 'The drop',
  'lynch.card-up': 'The card comes up',
  'lynch.truth': 'The truth',
  'lynch.card-to-wing': 'The card goes to the wing',

  'night.hub': 'Night falls',
  'room.opens': 'Your act',
  'pack.your-line': 'Your line to the pack',
  'pack.line': 'The pack talks',
  'pack.vote': 'The pack votes',
  'pack.decided': 'The kill is decided',

  'rnight.hub': 'Night falls',
  'rnight.spoke': 'In the night',
  'rnight.whole': 'The night, whole',

  'morning.shutter-down': 'The morning',
  'morning.chip-attacked': 'Attacked in the night',
  'morning.chip-fell': 'Fell',
  'morning.card-down': 'The card comes down',
  'morning.chip-saved': 'Saved',
  'morning.quiet': 'A quiet night',
  'morning.only-you': 'What only you learn',
  'morning.carried-summary': 'What the day taught',
  'morning.day-begins': 'The day begins',

  'over.where-it-ended': 'Where it ended',
  'over.winners-hour': "The winner's hour",
  'over.verdict': 'The verdict',
  'over.winners-stand': 'The winners take the stand',
  'over.truth': 'The truth is everyone’s',
  'over.epilogue': 'What the game taught',
  'over.curtain': 'Curtain',
} as const satisfies Record<string, string>;

export type BeatId = keyof typeof BEAT_LABELS;

/** One step of one actor's branch in the X-ray night; ranks order the branches by their last event. */
export interface Spoke {
  /** A seat, or `pack` for the wolves together. */
  actor: string;
  rank: number;
  step: number;
  steps: number;
}

export interface SceneBeat {
  id: BeatId;
  scene: SceneId;
  label: string;
  day: number;
  /** The anchoring event's seq. */
  seq: number;
  /** `events.slice(0, end)` is the log this beat shows; folding it gives the beat's view. */
  end: number;
  sees: Tier;
  /** Whose beat, for seat and faction tiers. */
  seat?: string;
  /** The seat the beat is about: the chip that fell, the card, the actor. */
  subject?: string;
  /** The nth of a run: the nth chip counted. */
  ordinal?: number;
  spoke?: Spoke;
  /** At normal speed; 0 = hold until the viewer moves on (a turn, the epilogue, the curtain). */
  holdMs: number;
  chapter?: Chapter;
  /** A private beat the X-ray replay still plays, in aqua, as "Only seat n". */
  aqua?: boolean;
  /** Exists only while a game is being played: a prompt for the seated human. */
  liveOnly?: boolean;
  /**
   * The game ends here: no night follows this lynch, so the scene must not play "night falls".
   * Only the cutter can know it (the view at this beat has no `game_over` yet).
   */
  endsGame?: boolean;
}

export interface BeatOptions {
  /** Observer tier on: the X-ray's beats exist and private beats marked `aqua` play. */
  xray: boolean;
  /** The seated human, if any; never inferred from the log. */
  me?: string | null;
  /** A game in play: the seated human's prompts become beats. */
  live?: boolean;
}
