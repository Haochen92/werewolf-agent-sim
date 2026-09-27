import { describe, expect, it } from 'vitest';
import { BEAT_LABELS } from '../beats/types';
import { DayScene } from '../scenes/DayScene';
import { DealScene } from '../scenes/DealScene';
import { GameOverScene } from '../scenes/GameOverScene';
import { LynchScene } from '../scenes/LynchScene';
import { MorningScene } from '../scenes/MorningScene';
import { NightLobbyScene } from '../scenes/NightLobbyScene';
import { ReplayNightScene } from '../scenes/ReplayNightScene';
import { StationScene } from '../scenes/StationScene';
import { VoteScene } from '../scenes/VoteScene';
import { anchorLine, workbenchFrame } from './frame';
import { SCENE_IDS, SCENES, isSceneId } from './registry';
import { DEFAULT_QUERY } from './url';

describe('the scene registry', () => {
  it('has an entry for every scene the beat sheet names, and no others', () => {
    const named = new Set(Object.keys(BEAT_LABELS).map((id) => id.split('.')[0]));
    expect(new Set(SCENE_IDS)).toEqual(named);
    for (const id of named) expect(isSceneId(id)).toBe(true);
    expect(isSceneId('paint')).toBe(false);
  });

  it('mounts the day scene for the day', () => {
    expect(SCENES.day).toBe(DayScene);
  });

  it('mounts the flies scenes: the deal, the night lobby, the morning', () => {
    expect(SCENES.deal).toBe(DealScene);
    expect(SCENES.night).toBe(NightLobbyScene);
    expect(SCENES.morning).toBe(MorningScene);
    expect(SCENES.rnight).toBe(ReplayNightScene);
  });

  it('mounts the trap scenes: the vote and the lynch', () => {
    expect(SCENES.vote).toBe(VoteScene);
    expect(SCENES.lynch).toBe(LynchScene);
  });

  it('mounts the ending', () => {
    expect(SCENES.over).toBe(GameOverScene);
  });

  it('mounts the platform first, before the deal', () => {
    expect(SCENES.station).toBe(StationScene);
    expect(SCENE_IDS[0]).toBe('station');
  });
});

describe('the platform on the workbench', () => {
  const at = (beat: number) => workbenchFrame('station', { ...DEFAULT_QUERY, beat });

  it('steps through its rooms: host, locked guest, watcher, departing, empty, guest', () => {
    const f = at(0);
    expect(f.beats.map((b) => b.id)).toEqual([
      'station.waiting',
      'station.locked',
      'station.waiting',
      'station.departing',
      'station.waiting',
      'station.waiting',
    ]);
    expect(f.beats.every((b) => b.scene === 'station' && b.liveOnly)).toBe(true);
    expect(f.situation?.label).toBe('the host, 3 aboard');
    expect(f.room).toMatchObject({ isHost: true, aboard: ['mira', 'kei', 'sol'], you: 0 });
    expect(f.room?.minAboard).toBe(1);
    expect(f.room?.link).toMatch(/\/games\/9369a5c1-/);
    expect(at(1).room).toMatchObject({ locked: true, isHost: false, seated: true });
    expect(at(1).room?.aboard).toHaveLength(5);
    expect(at(2).room).toMatchObject({ seated: false, you: null });
    expect(at(2).room?.aboard).toHaveLength(9);
    expect(at(3).beat?.id).toBe('station.departing');
    expect(at(4).room?.aboard).toEqual([]);
    expect(at(5).room).toMatchObject({
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
    expect(at(99).index).toBe(5);
  });
});

describe('a workbench frame on the fixture', () => {
  it('points at the scene’s own beats, folded to the beat', () => {
    const f = workbenchFrame('day', DEFAULT_QUERY);
    expect(f.beats.every((b) => b.scene === 'day')).toBe(true);
    // Day 1 opens with a pass everyone sees (a turn that ended with no speech).
    expect(f.beat?.id).toBe('day.pass');
    expect(anchorLine(f.beat!)).toBe('day.pass · seq 13 · public → player_1 · 4000 ms');
    // Folded up to, not including, the turn that resolved it.
    expect(f.view?.lastSeq).toBeLessThan(18);
    expect(f.presentation.cast).toHaveLength(9);
  });

  it('clamps the beat into range and re-cuts the list for the X-ray', () => {
    const pub = workbenchFrame('day', { ...DEFAULT_QUERY, beat: 999 });
    expect(pub.index).toBe(pub.beats.length - 1);
    const xray = workbenchFrame('day', { ...DEFAULT_QUERY, viewer: { kind: 'xray' } });
    // The X-ray swaps each derived pass for its pass_marker, so the day's count is the same.
    expect(xray.beats.length).toBeGreaterThanOrEqual(pub.beats.length);
    expect(xray.beat?.id).toBe('day.pass');
    expect(xray.beat?.sees).toBe('xray');
    expect(xray.presentation.xray).toBe(true);
  });

  it('seats the viewer it is given', () => {
    const f = workbenchFrame('day', {
      ...DEFAULT_QUERY,
      viewer: { kind: 'seat', seat: 'player_7' },
    });
    expect(f.me).toBe('player_7');
    expect(f.view?.me.seat).toBe('player_7');
  });
});
