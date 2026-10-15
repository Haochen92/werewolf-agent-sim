/**
 * The score's cue sheet (owner, 2026-10-15): what plays under each moment of a game, as a pure
 * function of the beat on the stage. The music follows the stage, never the stream: the stage
 * plays at reading pace behind the server, and the music belongs to what the viewer sees.
 *
 * A bed is what plays underneath, kept until the next bed differs: one track looping, a list
 * played in turn (the lobby's three), or a list played once through whose last track loops (the
 * morning). A sting is a one-shot on a moment, played only when the beat arrives as it happens
 * (live, or a replay playing on), never on a refresh, a jump or a scrub; a bed waits for a
 * sting to finish before it comes in (the stings are in E, the beds after them are not).
 */
import type { SceneBeat } from '@/stage/beats/types';
import type { WinnerKey } from '@/stage/roles';

const track = (name: string) => `/music/${name}.v1.mp3`;

export const TRACKS = {
  lobby: [track('lobby-bossa'), track('lobby-groove'), track('lobby-original')],
  elders: track('elders-council'),
  dayOdd: track('day-parlour-suspicion'),
  dayEven: track('day-masked-accusations'),
  vote: track('vote-whodunit-lounge'),
  psalm: track('lynch-psalm'),
  deathSting: track('lynch-sting'),
  night: track('night-hide-and-seek'),
  dawn: track('dawn-extended'),
  dawnLoop: track('dawn-loop'),
  win: {
    villagers: track('win-town'),
    wolves: track('win-wolves'),
    serial_killer: track('win-lone-killer'),
    necromancer: track('win-lone-killer'),
    draw: track('win-draw'),
  } satisfies Record<WinnerKey, string>,
} as const;

export interface Bed {
  /** Two beds with one key are the same music: moving between them changes nothing. */
  key: string;
  tracks: readonly string[];
  /**
   * `loop`: the one track, looping. `cycle`: the tracks in turn from `start`, each into the
   * next. `sequence`: the tracks once through, the last one looping.
   */
  mode: 'loop' | 'cycle' | 'sequence';
  start?: number;
  /** Plays only for a viewer who turned the music on (the guide), not by default. */
  optIn?: boolean;
}

/** The moment the stage is at, as far as the music cares. */
export interface Moment {
  beat: Pick<SceneBeat, 'id' | 'scene' | 'day'> | null;
  /** The game's winner, once it is over. */
  winner: WinnerKey | null;
  /** The replay's Fast halves every hold: the lynch's psalm would be cut short. */
  fast: boolean;
}

const loop = (key: string, url: string): Bed => ({ key, tracks: [url], mode: 'loop' });

/** Day 1's discussion is the parlour's, day 2's the masked accusations', and so on. */
const discussion = (day: number): Bed =>
  day % 2 === 1 ? loop('day-odd', TRACKS.dayOdd) : loop('day-even', TRACKS.dayEven);

/** The waiting room: the lobby's three in turn, from one picked for this visit. */
export const lobbyBed = (start: number): Bed => ({
  key: 'lobby',
  tracks: TRACKS.lobby,
  mode: 'cycle',
  start,
});

/** The guide, for a reader who asked for music. */
export const GUIDE_BED: Bed = { ...loop('guide', TRACKS.elders), optIn: true };

/** What plays under a beat; null is silence (the lynch, and the ending before its sting). */
export function bedFor({ beat }: Moment): Bed | null {
  if (!beat) return null;
  switch (beat.scene) {
    case 'station':
      return null; // the container plays the lobby's own bed (`lobbyBed`)
    case 'deal':
      // the opening runs on into day 1
      return discussion(1);
    case 'day':
      return discussion(beat.day);
    case 'vote':
      return loop('vote', TRACKS.vote);
    case 'lynch':
      return null;
    case 'night':
    case 'room':
    case 'pack':
    case 'rnight':
      return loop('night', TRACKS.night);
    case 'morning':
      // the day's music comes in as the day begins
      if (beat.id === 'morning.day-begins') return discussion(beat.day);
      // each morning its own dawn, held low on the loop if the morning outlasts it
      return {
        key: `morning-${beat.day}`,
        tracks: [TRACKS.dawn, TRACKS.dawnLoop],
        mode: 'sequence',
      };
    case 'over':
      return beat.id === 'over.where-it-ended' ? null : loop('ending', TRACKS.elders);
  }
}

/** The one-shot a beat starts, if any, when it arrives as it happens. */
export function stingFor({ beat, winner, fast }: Moment): string | null {
  if (!beat) return null;
  // the psalm from the lynch's start, its hit on the truth; on Fast it would be cut short, so
  // the short sting on the name instead
  if (beat.id === 'lynch.stand-returns' && !fast) return TRACKS.psalm;
  if (beat.id === 'lynch.named' && fast) return TRACKS.deathSting;
  if (beat.id === 'over.winners-hour') return TRACKS.win[winner ?? 'draw'];
  return null;
}
