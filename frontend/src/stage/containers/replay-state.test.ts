import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '@/stage/beats/beatsFor';
import { createFoldCache } from './fold-cache';
import {
  initialLoopState,
  initialReplayState,
  replayReducer,
  type ReplayState,
} from './replay-state';
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

describe('the loop window (a preview)', () => {
  const opens = beats.public.findIndex((b) => b.id === 'vote.opens' && b.day === 3);
  const wing = beats.public.findIndex((b) => b.id === 'lynch.card-to-wing' && b.day === 3);
  const loop = (index: number, rest: Partial<ReplayState> = {}): ReplayState => ({
    ...initialLoopState(
      beats.public,
      { from: opens, to: wing },
      {
        playing: true,
        speed: 'fast',
      },
    ),
    cursor: still(index),
    ...rest,
  });

  it('starts still on the window’s first beat, public, with no slot', () => {
    const s = initialLoopState(
      beats.public,
      { from: opens, to: wing },
      {
        playing: false,
        speed: 'fast',
      },
    );
    expect(s.cursor).toEqual(still(opens));
    expect([s.playing, s.speed, s.xray, s.slot]).toEqual([false, 'fast', false, null]);
    expect(s.loop).toEqual({ from: opens, to: wing });
  });

  it('clamps a window that runs past the list', () => {
    const last = beats.public.length - 1;
    const s = initialLoopState(
      beats.public,
      { from: last + 5, to: last + 40 },
      {
        playing: true,
        speed: 'fast',
      },
    );
    expect(s.loop).toEqual({ from: last, to: last });
    expect(s.cursor).toEqual(still(last));
  });

  it('plays forward moving inside the window', () => {
    expect(reduce(loop(opens), { type: 'tick' }).cursor).toEqual({
      index: opens + 1,
      animate: true,
    });
  });

  it('goes round from the last beat to the first, still, and keeps playing', () => {
    const s = reduce(loop(wing), { type: 'tick' });
    expect(s.cursor).toEqual(still(opens));
    expect(s.playing).toBe(true);
  });

  it('plays past a beat that waits for the viewer instead of stopping', () => {
    // the public cut's two waits are its last two beats: the epilogue and the curtain
    const waits = beats.public.findIndex((b) => b.holdMs === 0);
    const last = beats.public.length - 1;
    expect([waits, beats.public[last].holdMs]).toEqual([last - 1, 0]);
    const before = waits - 1;
    // both waits are played past, and the window goes round to its first beat, still
    const s = reduce(loop(before, { loop: { from: before, to: last } }), { type: 'tick' });
    expect(s.cursor).toEqual(still(before));
    expect(s.playing).toBe(true);
    // short of the waits it plays forward as ever, moving
    const t = reduce(loop(before - 1, { loop: { from: before - 1, to: last } }), {
      type: 'tick',
    });
    expect(t.cursor).toEqual({ index: before, animate: true });
  });

  it('stops only when nothing in the window would ever move', () => {
    const last = beats.public.length - 1;
    const s = reduce(
      loop(last - 1, { loop: { from: last - 1, to: last }, playing: false }),
      { type: 'play' },
    );
    expect(s.playing).toBe(false);
  });

  it('play and pause leave the cursor in the window; play from outside it starts over', () => {
    const paused = reduce(loop(opens + 3), { type: 'pause' });
    expect([paused.playing, paused.cursor.index]).toEqual([false, opens + 3]);
    const again = reduce(paused, { type: 'play' });
    expect([again.playing, again.cursor.index]).toEqual([true, opens + 3]);
    const outside = reduce(loop(2, { playing: false }), { type: 'play' });
    expect(outside.cursor).toEqual(still(opens));
  });

  it('its buttons stay inside the window', () => {
    expect(reduce(loop(opens), { type: 'step', dir: -1 }).cursor).toEqual(still(opens));
    expect(reduce(loop(opens + 2), { type: 'seek', index: 0 }).cursor).toEqual(
      still(opens),
    );
    expect(reduce(loop(opens + 2), { type: 'seek', index: 9999 }).cursor).toEqual(
      still(wing),
    );
    const next = reduce(loop(opens + 2), { type: 'chapter', dir: 1 }).cursor.index;
    expect(next).toBeGreaterThan(opens + 2);
    expect(next).toBeLessThanOrEqual(wing);
  });

  it('the X-ray carries the window to the X-ray’s list, and back', () => {
    const on = reduce(loop(opens, { playing: false }), { type: 'xray' });
    expect(on.xray).toBe(true);
    const x = beats.xray;
    expect(x[on.loop!.from]).toMatchObject({ id: 'vote.opens', day: 3 });
    expect(x[on.loop!.to]).toMatchObject({ id: 'lynch.card-to-wing', day: 3 });
    expect(on.cursor).toEqual(still(on.loop!.from));
    const off = reduce(on, { type: 'xray' });
    expect([off.xray, off.loop]).toEqual([false, { from: opens, to: wing }]);
  });

  it('the whole-log replay never loops: its state has no window', () => {
    expect(initialReplayState().loop).toBeNull();
    const last = beats.public.length - 1;
    const end = reduce(at0(last - 1), { type: 'tick' });
    expect([end.cursor.index, end.playing]).toEqual([last, false]);
  });
});

function at0(index: number): ReplayState {
  return { ...initialReplayState(), cursor: still(index), playing: true };
}
