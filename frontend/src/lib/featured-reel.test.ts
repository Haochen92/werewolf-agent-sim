import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-e45eda20.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import type { SceneBeat } from '@/stage/beats/types';
import { FEATURED, featuredReel } from './featured-reel';

const events = fixture.events as unknown as DurableGameEvent[];
const beats = beatsFor(events, { xray: true });

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

const idsOf = (reel: number[]) => reel.map((i) => beats[i].id);

describe('the featured reel', () => {
  it('plays the deal dealt, the pack’s night, its morning, the lines and day 3’s vote, in order', () => {
    const { reel, day } = featuredReel(beats, FEATURED);
    expect(day).toBe(3);
    expect(reel).toEqual([...reel].sort((a, b) => a - b));
    const ids = idsOf(reel);
    // the deal arrived at done, its cards face up, and straight on to the night
    expect(ids.slice(0, 2)).toEqual(['deal.face-up', 'rnight.hub']);
    // the pack's room, every line of its chat and the kill
    const pack = reel.filter((i) => beats[i].spoke?.actor === 'pack');
    expect(pack).toHaveLength(beats[pack[0]].spoke!.steps);
    expect(reel.filter((i) => beats[i].scene === 'rnight')).toHaveLength(pack.length + 1);
    // the morning's two bodies, without its roll
    expect(ids.filter((id) => id === 'morning.card-down')).toHaveLength(2);
    expect(ids).not.toContain('morning.roll');
    // seat 10's line and seat 1's answer, every page of each, and no other speech
    const said = reel.filter((i) => beats[i].id === 'day.speech');
    expect(new Set(said.map((i) => beats[i].seq))).toEqual(new Set(FEATURED.lines));
    expect(said.map((i) => beats[i].subject)).toEqual([
      ...Array(4).fill('player_10'),
      ...Array(3).fill('player_1'),
    ]);
    // the vote through the real Investigator's card going to the wing, and nothing after
    const opens = beats.findIndex((b) => b.id === 'vote.opens' && b.day === 3);
    const wing = beats.findIndex((b) => b.id === 'lynch.card-to-wing' && b.day === 3);
    expect(reel.slice(-(wing - opens + 1))).toEqual(
      Array.from({ length: wing - opens + 1 }, (_, i) => opens + i),
    );
    expect(beats[wing].subject).toBe('player_1');
  });

  it('without the featured lines (the fallback game) plays the first vote', () => {
    const { reel, day } = featuredReel(beats);
    expect(day).toBe(2);
    expect(reel.some((i) => beats[i].id === 'day.speech')).toBe(false);
    expect(beats[reel.at(-1)!]).toMatchObject({ id: 'lynch.card-to-wing', day: 2 });
  });

  it('falls back to the first vote when the featured day has none', () => {
    const b = cut(
      ['deal.table-seated', 1],
      ['deal.face-up', 1],
      ['day.speech', 1],
      ['vote.opens', 2],
      ['vote.result', 2],
      ['vote.table-down', 2],
      ['lynch.named', 2],
      ['lynch.card-to-wing', 2],
      ['night.hub', 2],
    );
    expect(featuredReel(b, { day: 3, lines: [] })).toEqual({
      reel: [1, 3, 4, 5, 6, 7],
      day: 2,
    });
  });

  it('ends a tied vote at the table going down', () => {
    const b = cut(
      ['vote.opens', 3],
      ['vote.result', 3],
      ['vote.table-down', 3],
      ['night.hub', 3],
    );
    expect(featuredReel(b)).toEqual({ reel: [0, 1, 2], day: 3 });
  });

  it('plays the opening when it finds none of its parts', () => {
    const short = cut(['station.waiting', 1], ['day.pass', 1], ['day.pass', 1]);
    expect(featuredReel(short)).toEqual({ reel: [0, 1, 2], day: null });
    const long = cut(
      ...Array.from({ length: 50 }, () => ['day.pass', 1] as [SceneBeat['id'], number]),
    );
    expect(featuredReel(long).reel).toHaveLength(31);
    expect(featuredReel([])).toEqual({ reel: [], day: null });
  });
});
