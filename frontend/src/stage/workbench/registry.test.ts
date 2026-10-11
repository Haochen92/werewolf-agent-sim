import { describe, expect, it } from 'vitest';
import { BEAT_LABELS } from '../beats/types';
import { CarScene } from '../scenes';
import { PackScene } from '../scenes/PackScene';
import { ShelfRoomScene } from '../scenes/ShelfRoomScene';
import { StationScene } from '../scenes/StationScene';
import { anchorLine, workbenchFrame } from './frame';
import { SCENE_IDS, SCENES, SYNTHETIC, isSceneId } from './registry';
import { DEFAULT_QUERY } from './url';

describe('the scene registry', () => {
  it('has an entry for every scene the beat sheet names, and no others', () => {
    const named = new Set(Object.keys(BEAT_LABELS).map((id) => id.split('.')[0]));
    expect(new Set(SCENE_IDS)).toEqual(named);
    for (const id of named) expect(isSceneId(id)).toBe(true);
    expect(isSceneId('paint')).toBe(false);
  });

  it('plays every scene set in the dining car through the one car host, so its set stays up', () => {
    for (const id of [
      'deal',
      'day',
      'vote',
      'lynch',
      'night',
      'morning',
      'rnight',
      'over',
    ] as const)
      expect(SCENES[id]).toBe(CarScene);
  });

  it('keeps the live night rooms as places of their own', () => {
    expect(SCENES.room).toBe(ShelfRoomScene);
    expect(SCENES.pack).toBe(PackScene);
  });

  it('mounts the platform first, before the deal', () => {
    expect(SCENES.station).toBe(StationScene);
    expect(SCENE_IDS[0]).toBe('station');
  });
});

describe('the platform on the workbench', () => {
  const at = (beat: number) => workbenchFrame('station', { ...DEFAULT_QUERY, beat });
  const labelled = (label: string) =>
    at(SYNTHETIC.station!.findIndex((s) => s.label === label));

  it('steps through its rooms: two of ten places, then the nine-place host, locked guest, watcher, departing, empty, guest', () => {
    const f = at(0);
    expect(f.beats.map((b) => b.id)).toEqual([
      'station.waiting',
      'station.waiting',
      'station.waiting',
      'station.locked',
      'station.waiting',
      'station.departing',
      'station.waiting',
      'station.waiting',
    ]);
    expect(f.beats.every((b) => b.scene === 'station' && b.liveOnly)).toBe(true);
    // the ten-seat game is the default: its rooms come first
    expect(f.situation?.label).toBe('a guest, 4 aboard');
    expect(f.room).toMatchObject({ places: 10, isHost: false, seated: true, you: 3 });
    expect(f.room?.minAboard).toBe(1);
    expect(f.room?.link).toMatch(/\/games\/9369a5c1-/);
    expect(at(1).room).toMatchObject({ places: 10, seated: false, you: null });
    expect(at(1).room?.aboard).toHaveLength(10);
    const host = labelled('nine seats: the host, 3 aboard');
    expect(host.room).toMatchObject({
      isHost: true,
      aboard: ['mira', 'kei', 'sol'],
      you: 0,
    });
    expect(host.room?.places).toBe(9);
    const locked = labelled('nine seats: a guest, 5 aboard, locked');
    expect(locked.room).toMatchObject({ locked: true, isHost: false, seated: true });
    expect(locked.room?.aboard).toHaveLength(5);
    const full = labelled('nine seats: watching, all 9 aboard');
    expect(full.room).toMatchObject({ seated: false, you: null });
    expect(full.room?.aboard).toHaveLength(9);
    expect(labelled('nine seats: departing, 3 aboard').beat?.id).toBe('station.departing');
    expect(labelled('nine seats: the host, nobody aboard yet').room?.aboard).toEqual([]);
    expect(labelled('nine seats: a guest, 4 aboard').room).toMatchObject({
      places: 9,
      locked: false,
      isHost: false,
      seated: true,
      you: 3,
    });
  });

  it('has nobody seated, an empty view, and ignores the viewer control', () => {
    const f = workbenchFrame('station', {
      ...DEFAULT_QUERY,
      viewer: { kind: 'seat', seat: 'player_1' },
    });
    expect(f.me).toBeNull();
    expect(f.view?.lastSeq).toBe(0);
    expect(f.presentation.xray).toBe(false);
    expect(at(99).index).toBe(7);
    expect(at(7).room).toMatchObject({ places: 9 });
  });
});

describe('the workbench’s default game', () => {
  it('is the ten-seat game, with its ten-seat cast', () => {
    const f = workbenchFrame('day', DEFAULT_QUERY);
    expect(f.presentation.cast).toHaveLength(10);
    expect(f.view?.seats).toHaveLength(10);
    // its day 1 opens with the opening round being written
    expect(f.beat?.id).toBe('day.opening-prepares');
    expect(workbenchFrame('day', { ...DEFAULT_QUERY, game: 'phase3' }).beats).toEqual(
      f.beats,
    );
  });

  it('draws the nine-seat fixture for `game=9369a5c1`, and for a redraw of it', () => {
    for (const q of [
      { game: '9369a5c1' as const },
      { memoryOff: true },
      { memoryFields: true },
      { summaryV4: true },
    ]) {
      const f = workbenchFrame('day', { ...DEFAULT_QUERY, ...q });
      expect(f.presentation.cast, JSON.stringify(q)).toHaveLength(9);
      expect(f.beat?.id).toBe('day.pass');
    }
    // the v4 redraw's synthetic ledger belongs to the fixture alone
    expect(
      workbenchFrame('day', { ...DEFAULT_QUERY, summaryV4: true }).ledger,
    ).not.toBeNull();
    expect(
      workbenchFrame('day', { ...DEFAULT_QUERY, summaryV4: true, game: 'phase3' }).ledger,
    ).toBeNull();
  });
});

describe('a workbench frame on the nine-seat fixture', () => {
  const NINE = { ...DEFAULT_QUERY, game: '9369a5c1' as const };

  it('points at the scene’s own beats, folded to the beat', () => {
    const f = workbenchFrame('day', NINE);
    expect(f.beats.every((b) => b.scene === 'day')).toBe(true);
    // Day 1 opens with a pass everyone sees (a turn that ended with no speech).
    expect(f.beat?.id).toBe('day.pass');
    expect(anchorLine(f.beat!)).toBe('day.pass · seq 13 · public → player_1 · 4000 ms');
    // Folded up to, not including, the turn that resolved it.
    expect(f.view?.lastSeq).toBeLessThan(18);
    expect(f.presentation.cast).toHaveLength(9);
  });

  it('clamps the beat into range and re-cuts the list for the X-ray', () => {
    const pub = workbenchFrame('day', { ...NINE, beat: 999 });
    expect(pub.index).toBe(pub.beats.length - 1);
    const xray = workbenchFrame('day', { ...NINE, viewer: { kind: 'xray' } });
    // The X-ray swaps each derived pass for its pass_marker, so the day's count is the same.
    expect(xray.beats.length).toBeGreaterThanOrEqual(pub.beats.length);
    expect(xray.beat?.id).toBe('day.pass');
    expect(xray.beat?.sees).toBe('xray');
    expect(xray.presentation.xray).toBe(true);
  });

  it('seats the viewer it is given', () => {
    const f = workbenchFrame('day', {
      ...NINE,
      viewer: { kind: 'seat', seat: 'player_7' },
    });
    expect(f.me).toBe('player_7');
    expect(f.view?.me.seat).toBe('player_7');
  });
});
