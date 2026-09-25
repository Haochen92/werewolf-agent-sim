import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { actedAt, marksAt, nightBranchesOf } from './replay-night';

const beats = beatsFor(FIXTURE_EVENTS, { xray: true });
const viewAt = (end: number) => foldEvents(FIXTURE_EVENTS.slice(0, end));

describe('the X-ray night, read back from the view', () => {
  it('orders the branches exactly as the beat cutter does, on every spoke of the fixture', () => {
    const spokes = beats.filter((b) => b.id === 'rnight.spoke');
    expect(spokes.length).toBeGreaterThan(0);
    for (const b of spokes) {
      const branches = nightBranchesOf(viewAt(b.end), b.day);
      const br = branches[b.spoke!.rank];
      expect(br?.actor).toBe(b.spoke!.actor);
      expect(br.lines + (br.target ? 1 : 0)).toBe(b.spoke!.steps);
    }
  });

  it('puts the pack at the stand with its living wolves, and the lone wolf alone', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    expect(n2.map((b) => b.actor)).toEqual(['player_4', 'player_9', 'player_2', 'pack']);
    expect(n2[3].seats).toEqual(['player_3', 'player_8']);
    expect(n2[3].target).toBe('player_4');
    const n3 = nightBranchesOf(viewAt(269), 3);
    expect(n3.find((b) => b.actor === 'pack')?.seats).toEqual(['player_8']);
  });

  it('lands the marks of earlier branches, and this one only on its mark step', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    const line = marksAt(n2, { actor: 'pack', rank: 3, step: 1, steps: 5 });
    expect(line.map((m) => [m.seat, m.kind, m.landing])).toEqual([
      ['player_2', 'lens', false],
      ['player_1', 'plaster', false],
      ['player_3', 'knife', false],
    ]);
    const bite = marksAt(n2, { actor: 'pack', rank: 3, step: 4, steps: 5 });
    expect(bite.at(-1)).toEqual({ seat: 'player_4', kind: 'bite', rank: 3, landing: true });
    expect(marksAt(n2, null)).toHaveLength(4);
    expect(marksAt(n2, null).every((m) => !m.landing)).toBe(true);
  });

  it('counts the acts in as the spokes are told', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    expect(actedAt(n2, { actor: 'player_4', rank: 0, step: 0, steps: 1 }, 5)).toBe(1);
    expect(actedAt(n2, { actor: 'pack', rank: 3, step: 1, steps: 5 }, 5)).toBe(3);
    expect(actedAt(n2, null, 5)).toBe(5);
  });
});
