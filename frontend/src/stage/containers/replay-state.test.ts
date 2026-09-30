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

  it('the X-ray keeps the cursor on the same beat, and the pane where it was', () => {
    const speech = beats.public.findIndex((b) => b.id === 'day.speech' && b.seq === 200);
    const on = reduce(at(speech, { slot: 'drawer' }), { type: 'xray' });
    expect(on.xray).toBe(true);
    expect(on.slot).toBe('drawer');
    const b = beats.xray[on.cursor.index];
    expect([b.id, b.seq]).toEqual(['day.speech', 200]);
    expect(on.cursor.animate).toBe(false);
    // off again: back to the same speech in the public list
    const off = reduce(on, { type: 'xray' });
    expect(off.xray).toBe(false);
    expect(off.slot).toBe('drawer');
    expect(off.cursor.index).toBe(speech);
  });

  it('File and Transcript only choose the pane; File needs the X-ray', () => {
    // no X-ray: File does nothing
    expect(reduce(at(40, { slot: 'drawer' }), { type: 'file' }).slot).toBe('drawer');
    const on = reduce(at(40, { slot: 'drawer' }), { type: 'xray' });
    const file = reduce(on, { type: 'file' });
    expect([file.xray, file.slot, file.cursor.index]).toEqual([
      true,
      'film',
      on.cursor.index,
    ]);
    expect(reduce(file, { type: 'transcript' }).slot).toBe('drawer');
    // pressed again, the pane closes
    expect(reduce(file, { type: 'file' }).slot).toBe(null);
    // the X-ray off with the file up: the pane falls back to the transcript
    const off = reduce(file, { type: 'xray' });
    expect([off.xray, off.slot]).toEqual([false, 'drawer']);
  });

  it('a seat tapped on the stage brings its file, only with the X-ray', () => {
    expect(reduce(at(40, { slot: null }), { type: 'show-file' }).slot).toBe(null);
    const on = reduce(at(40, { slot: 'drawer' }), { type: 'xray' });
    const shown = reduce(on, { type: 'show-file' });
    expect([shown.slot, shown.cursor.index]).toEqual(['film', on.cursor.index]);
    // already up, it stays up (unlike the File tab, which closes it)
    expect(reduce(shown, { type: 'show-file' }).slot).toBe('film');
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

describe('the stops (the X-ray on)', () => {
  const x = beats.xray;
  const find = (id: string, day: number, actor?: string) =>
    x.findIndex(
      (b) => b.id === id && b.day === day && (!actor || b.spoke?.actor === actor),
    );
  const hub = find('rnight.hub', 2);
  const whole = find('rnight.whole', 2);
  const ballotsIn = find('vote.closes', 3);
  const on = (index: number, rest: Partial<ReplayState> = {}): ReplayState => ({
    ...initialReplayState(),
    xray: true,
    cursor: still(index),
    ...rest,
  });

  it('the play pauses on arriving at the night hub, normal and fast alike', () => {
    for (const speed of ['normal', 'fast'] as const) {
      const s = reduce(on(hub - 1, { playing: true, speed }), { type: 'tick' });
      expect(s.cursor).toEqual({ index: hub, animate: true });
      expect(s.playing).toBe(false);
    }
    // arrived at by a seek or a chapter jump while playing, it pauses too
    expect(reduce(on(3, { playing: true }), { type: 'seek', index: hub }).playing).toBe(
      false,
    );
    const jump = reduce(on(hub - 2, { playing: true }), { type: 'chapter', dir: 1 });
    expect([jump.cursor.index, jump.playing]).toEqual([hub, false]);
    // without the X-ray there is no stop: the public hub plays on
    const pub = beats.public.findIndex((b) => b.id === 'night.hub' && b.day === 2);
    const p = reduce(
      { ...initialReplayState(), cursor: still(pub - 1), playing: true },
      {
        type: 'tick',
      },
    );
    expect([p.cursor.index, p.playing]).toEqual([pub, true]);
  });

  it('the vote pauses with the ballots in, before the count; ▶ counts them', () => {
    const s = reduce(on(ballotsIn - 1, { playing: true }), { type: 'tick' });
    expect([s.cursor.index, s.playing]).toEqual([ballotsIn, false]);
    expect(x[ballotsIn - 1].id).toBe('vote.ballots-drop');
    const count = reduce(s, { type: 'play' });
    expect(count.cursor).toEqual({ index: ballotsIn + 1, animate: true });
    expect(x[count.cursor.index].id).toBe('vote.count-begins');
    expect(count.playing).toBe(true);
  });

  it('“Watch them all” plays the rooms in order, then the whole, then on', () => {
    let s = reduce(on(hub), { type: 'play' });
    expect(s.cursor).toEqual({ index: hub + 1, animate: true });
    while (s.playing && s.cursor.index <= whole) s = reduce(s, { type: 'tick' });
    // no return to the hub on the way: the whole, then the morning
    expect(x[s.cursor.index].id).toBe('morning.shutter-down');
    expect(s.playing).toBe(true);
    // and every room it passed through is remembered as visited
    expect(s.visited).toEqual(
      expect.arrayContaining(['2:player_4', '2:player_9', '2:player_2', '2:pack']),
    );
  });

  it('a lit seat tapped plays its room; the room’s end returns to the hub', () => {
    const inv = find('rnight.spoke', 2, 'player_4');
    const v = reduce(on(hub), { type: 'visit', index: inv });
    expect(v.cursor).toEqual({ index: inv, animate: true });
    expect([v.playing, v.visit, v.visited]).toEqual([true, '2:player_4', ['2:player_4']]);
    const back = reduce(v, { type: 'tick' });
    expect(back.cursor).toEqual(still(hub));
    expect([back.playing, back.visit]).toEqual([false, null]);
    expect(back.visited).toEqual(['2:player_4']);
    // the pack's room has five steps: it plays them all before returning
    const pack = find('rnight.spoke', 2, 'pack');
    let p = reduce(back, { type: 'visit', index: pack });
    for (let k = 1; k < 5; k++) {
      p = reduce(p, { type: 'tick' });
      expect(p.cursor).toEqual({ index: pack + k, animate: true });
    }
    p = reduce(p, { type: 'tick' });
    expect(p.cursor).toEqual(still(hub));
  });

  it('the arrows step through the rooms linearly, and a room reached so plays on', () => {
    const inv = find('rnight.spoke', 2, 'player_4');
    const v = reduce(on(hub), { type: 'visit', index: inv });
    // a step out of the visited room ends the visit
    const next = reduce(v, { type: 'step', dir: 1 });
    expect(next.cursor).toEqual({ index: inv + 1, animate: true });
    expect(next.visit).toBeNull();
    expect(reduce(next, { type: 'tick' }).cursor).toEqual({
      index: inv + 2,
      animate: true,
    });
    // from the hub, the arrow goes to the first room, not back to the hub
    expect(reduce(on(hub), { type: 'step', dir: 1 }).cursor.index).toBe(hub + 1);
  });

  it('“End the night” goes to the first beat after the whole, playing', () => {
    const s = reduce(on(hub), { type: 'end-night' });
    expect(s.cursor).toEqual(still(whole + 1));
    expect(x[s.cursor.index]).toMatchObject({ id: 'morning.shutter-down', day: 2 });
    expect(s.playing).toBe(true);
  });

  it('“Back to the night” returns from a room to its hub, paused', () => {
    const pack = find('rnight.spoke', 2, 'pack');
    const s = reduce(on(pack + 2, { playing: true }), { type: 'to-hub' });
    expect([s.cursor, s.playing]).toEqual([still(hub), false]);
  });

  it('Reveal off inside a room lands on that night’s public hub', () => {
    const pack = find('rnight.spoke', 2, 'pack');
    const off = reduce(on(pack + 1, { slot: 'film' }), { type: 'xray' });
    expect(beats.public[off.cursor.index]).toMatchObject({ id: 'night.hub', day: 2 });
  });
});
