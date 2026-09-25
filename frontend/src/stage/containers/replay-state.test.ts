import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '@/stage/beats/beatsFor';
import { createFoldCache } from './fold-cache';
import { initialReplayState, replayReducer, type ReplayState } from './replay-state';
import { still } from './transport';

const events = fixture.events as unknown as DurableGameEvent[];
const beats = {
  public: beatsFor(events, { xray: false }),
  xray: beatsFor(events, { xray: true }),
};
const reduce = replayReducer(beats);

describe('the fold cache', () => {
  it('folds only the events a step forward adds', () => {
    const cache = createFoldCache(events);
    const a = cache.at(200);
    expect(cache.folded).toBe(200);
    const b = cache.at(201);
    expect(cache.folded).toBe(201);
    expect(b).toEqual(foldEvents(events.slice(0, 201)));
    // stepping back, or seeking to a beat already seen, folds nothing
    expect(cache.at(200)).toBe(a);
    expect(cache.folded).toBe(201);
  });

  it('starts from the nearest fold before the one asked for', () => {
    const cache = createFoldCache(events);
    cache.at(100);
    cache.at(300);
    cache.at(150);
    expect(cache.folded).toBe(300 + 50);
    expect(cache.at(150)).toEqual(foldEvents(events.slice(0, 150)));
    expect(cache.at(events.length + 10)).toEqual(foldEvents(events));
  });
});

describe('the replay reducer', () => {
  const at = (index: number, rest: Partial<ReplayState> = {}): ReplayState => ({
    ...initialReplayState(),
    cursor: still(index),
    ...rest,
  });

  it('the X-ray keeps the cursor on the same beat', () => {
    const speech = beats.public.findIndex((b) => b.id === 'day.speech' && b.seq === 200);
    const on = reduce(at(speech), { type: 'xray' });
    expect(on.xray).toBe(true);
    expect(on.slot).toBe('film');
    const b = beats.xray[on.cursor.index];
    expect([b.id, b.seq]).toEqual(['day.speech', 200]);
    expect(on.cursor.animate).toBe(false);
    // the film up, X-ray again turns it off: back to the same speech in the public list
    const off = reduce(on, { type: 'xray' });
    expect(off.xray).toBe(false);
    expect(off.slot).toBe(null);
    expect(off.cursor.index).toBe(speech);
  });

  it('the X-ray with the drawer up brings the film and keeps the beat', () => {
    const s = reduce(reduce(at(40), { type: 'xray' }), { type: 'transcript' });
    expect([s.xray, s.slot]).toEqual([true, 'drawer']);
    const film = reduce(s, { type: 'xray' });
    expect([film.xray, film.slot, film.cursor.index]).toEqual([
      true,
      'film',
      s.cursor.index,
    ]);
  });

  it('plays forward moving, and stops at the end', () => {
    const s = reduce(at(3), { type: 'play' });
    expect(s.playing).toBe(true);
    const t = reduce(s, { type: 'tick' });
    expect(t.cursor).toEqual({ index: 4, animate: true });
    const last = beats.public.length - 1;
    const end = reduce(at(last - 1, { playing: true }), { type: 'tick' });
    expect(end.cursor.index).toBe(last);
    expect(end.playing).toBe(false);
    // play at the end starts again from the top
    expect(reduce(end, { type: 'play' }).cursor).toEqual(still(0));
  });

  it('a beat that waits for the viewer pauses the play', () => {
    const waits = beats.public.findIndex(
      (b, i) => b.holdMs === 0 && i < beats.public.length - 1,
    );
    expect(waits).toBeGreaterThan(0);
    const s = reduce(at(waits - 1, { playing: true }), { type: 'tick' });
    expect(s.cursor.index).toBe(waits);
    expect(s.playing).toBe(false);
    // play from it moves on at once
    const p = reduce(s, { type: 'play' });
    expect(p.cursor).toEqual({ index: waits + 1, animate: true });
  });

  it('steps and chapter jumps go through the transport', () => {
    expect(reduce(at(5), { type: 'step', dir: -1 }).cursor).toEqual(still(4));
    expect(reduce(at(5), { type: 'step', dir: 1 }).cursor).toEqual({
      index: 6,
      animate: true,
    });
    expect(reduce(at(0), { type: 'chapter', dir: 1 }).cursor).toEqual(still(2));
    expect(reduce(at(0), { type: 'seek', index: 32 }).cursor).toEqual(still(32));
  });
});
