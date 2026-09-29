import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import type { SceneBeat } from '@/stage/beats/types';
import { featuredWindow } from './featured-window';

const events = fixture.events as unknown as DurableGameEvent[];
const beats = beatsFor(events, { xray: false });

/** A made-up beat list: only the fields the finder reads matter. */
const cut = (...spec: [SceneBeat['id'], number][]): SceneBeat[] =>
  spec.map(([id, day], i) => ({
    id,
    day,
    scene: 'vote',
    label: id,
    seq: i,
    end: i,
    sees: 'public',
    holdMs: 1000,
  }));

describe('the featured window', () => {
  it('is day 3’s vote through the lynched card going to the wing, in the fixture', () => {
    const w = featuredWindow(beats);
    // the public golden (beats/__goldens__/9369a5c1.public.txt): lines 53 and 71
    expect(w).toEqual({ from: 53, to: 71, day: 3 });
    expect([beats[w.from].id, beats[w.from].day]).toEqual(['vote.opens', 3]);
    expect([beats[w.to].id, beats[w.to].day]).toEqual(['lynch.card-to-wing', 3]);
  });

  it('falls back to the first vote when the game has no day-3 vote', () => {
    const b = cut(
      ['deal.table-seated', 1],
      ['day.speech', 1],
      ['vote.opens', 2],
      ['vote.result', 2],
      ['vote.table-down', 2],
      ['lynch.named', 2],
      ['lynch.card-to-wing', 2],
      ['night.hub', 2],
    );
    expect(featuredWindow(b)).toEqual({ from: 2, to: 6, day: 2 });
  });

  it('ends a tied vote at the table going down', () => {
    const b = cut(
      ['vote.opens', 3],
      ['vote.result', 3],
      ['vote.table-down', 3],
      ['night.hub', 3],
    );
    expect(featuredWindow(b)).toEqual({ from: 0, to: 2, day: 3 });
  });

  it('plays the opening when there is no vote at all', () => {
    const short = cut(['deal.table-seated', 1], ['deal.cards-dealt', 1], ['day.pass', 1]);
    expect(featuredWindow(short)).toEqual({ from: 0, to: 2, day: null });
    const long = cut(
      ...Array.from({ length: 50 }, () => ['day.pass', 1] as [SceneBeat['id'], number]),
    );
    expect(featuredWindow(long)).toEqual({ from: 0, to: 30, day: null });
    expect(featuredWindow([])).toEqual({ from: 0, to: 0, day: null });
  });
});
