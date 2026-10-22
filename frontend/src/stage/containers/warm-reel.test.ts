import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-e45eda20.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import { FEATURED, featuredReel } from '@/lib/featured-reel';
import { warmBeats } from './warm-reel';

const beats = beatsFor(fixture.events as unknown as DurableGameEvent[], { xray: true });
const { reel } = featuredReel(beats, FEATURED);

describe('the beats a preview warms', () => {
  const visits = warmBeats(reel, beats);

  it('visits the last of each run and each change of scene in its first 50 s, never the first beat', () => {
    expect(visits.map((i) => beats[i].id)).toEqual([
      'deal.face-up',
      'rnight.hub',
      'rnight.spoke',
      'rnight.spoke',
      'morning.shutter-down',
    ]);
    // with no horizon, the whole reel's
    expect(
      warmBeats(reel, beats, 'fast', Infinity)
        .map((i) => beats[i].id)
        .slice(5),
    ).toEqual([
      'morning.card-down',
      'day.speech',
      'day.speech',
      'vote.opens',
      'lynch.stand-returns',
      'lynch.card-to-wing',
    ]);
    expect(visits).not.toContain(reel[0]);
    expect(visits.every((i) => reel.includes(i))).toBe(true);
  });

  it('has nothing to visit on a reel of one run in one scene', () => {
    const opens = beats.findIndex((b) => b.id === 'vote.opens' && b.day === 3);
    expect(warmBeats([opens, opens + 1, opens + 2], beats)).toEqual([opens + 2]);
    expect(warmBeats([opens], beats)).toEqual([]);
  });
});
