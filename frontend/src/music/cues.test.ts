import { describe, expect, it } from 'vitest';
import type { SceneBeat } from '@/stage/beats/types';
import { GUIDE_BED, TRACKS, bedFor, lobbyBed, stingFor, type Moment } from './cues';

const at = (
  id: SceneBeat['id'],
  scene: SceneBeat['scene'],
  day = 1,
  more: Partial<Moment> = {},
): Moment => ({ beat: { id, scene, day }, winner: null, fast: false, ...more });

describe('the bed under each beat', () => {
  it('alternates the discussion by day, from the deal into day 1', () => {
    expect(bedFor(at('deal.cards-dealt', 'deal'))?.tracks).toEqual([TRACKS.dayOdd]);
    expect(bedFor(at('day.speech', 'day', 1))?.key).toBe(
      bedFor(at('deal.face-up', 'deal'))?.key,
    );
    expect(bedFor(at('day.speech', 'day', 2))?.tracks).toEqual([TRACKS.dayEven]);
    expect(bedFor(at('day.speech', 'day', 3))?.tracks).toEqual([TRACKS.dayOdd]);
  });

  it('plays the vote, rests through the lynch, and plays the night in every night scene', () => {
    expect(bedFor(at('vote.opens', 'vote', 2))?.tracks).toEqual([TRACKS.vote]);
    expect(bedFor(at('lynch.drop', 'lynch', 2))).toBeNull();
    for (const scene of ['night', 'room', 'pack', 'rnight'] as const)
      expect(bedFor(at('night.hub', scene, 2))?.tracks).toEqual([TRACKS.night]);
  });

  it("gives each morning its own dawn, then the day's music as the day begins", () => {
    const morning = bedFor(at('morning.shutter-down', 'morning', 2));
    expect(morning).toMatchObject({
      mode: 'sequence',
      tracks: [TRACKS.dawn, TRACKS.dawnLoop],
    });
    expect(bedFor(at('morning.roll', 'morning', 2))?.key).toBe(morning?.key);
    expect(bedFor(at('morning.shutter-down', 'morning', 3))?.key).not.toBe(morning?.key);
    // "the day begins" carries the new day: day 3's discussion is the parlour's
    expect(bedFor(at('morning.day-begins', 'morning', 3))?.tracks).toEqual([TRACKS.dayOdd]);
  });

  it("is silent where the ending starts, then the elders' music from the winner's hour", () => {
    expect(bedFor(at('over.where-it-ended', 'over', 3))).toBeNull();
    expect(bedFor(at('over.winners-hour', 'over', 3))?.tracks).toEqual([TRACKS.elders]);
    expect(bedFor(at('over.curtain', 'over', 3))?.key).toBe('ending');
  });

  it('leaves the platform to the container, plays the lobby in turn, and the guide only by choice', () => {
    expect(bedFor(at('station.waiting', 'station'))).toBeNull();
    expect(lobbyBed(2)).toMatchObject({ mode: 'cycle', start: 2, tracks: TRACKS.lobby });
    expect(GUIDE_BED.optIn).toBe(true);
    expect(bedFor({ beat: null, winner: null, fast: false })).toBeNull();
  });
});

describe('the moments that start a one-shot', () => {
  it("plays the psalm from the lynch's start, and the short sting on the name on Fast", () => {
    expect(stingFor(at('lynch.stand-returns', 'lynch', 2))).toBe(TRACKS.psalm);
    expect(stingFor(at('lynch.named', 'lynch', 2))).toBeNull();
    const fast = { fast: true };
    expect(stingFor(at('lynch.stand-returns', 'lynch', 2, fast))).toBeNull();
    expect(stingFor(at('lynch.named', 'lynch', 2, fast))).toBe(TRACKS.deathSting);
  });

  it("plays the winner's sting on their hour: the lone killers share one, a draw has its own", () => {
    const hour = (winner: Moment['winner']) =>
      stingFor(at('over.winners-hour', 'over', 3, { winner }));
    expect(hour('villagers')).toBe(TRACKS.win.villagers);
    expect(hour('wolves')).toBe(TRACKS.win.wolves);
    expect(hour('serial_killer')).toBe(hour('necromancer'));
    expect(hour('draw')).toBe(TRACKS.win.draw);
    expect(stingFor(at('over.verdict', 'over', 3, { winner: 'wolves' }))).toBeNull();
  });
});
