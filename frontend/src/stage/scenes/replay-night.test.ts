import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import type { DurableGameEvent } from '@/types/contracts';
import phase3 from '@/stage/fixtures/replay-phase3.json';
import necro from '@/stage/fixtures/replay-phase3-necro.json';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { actLine, actedAt, isHeld, marksAt, nightBranchesOf } from './replay-night';

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
      expect(br.lines + (br.target || isHeld(br) ? 1 : 0)).toBe(b.spoke!.steps);
    }
  });

  it('puts the pack at the stand with its living wolves, and the lone wolf alone', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    expect(n2.map((b) => b.actor)).toEqual([
      'player_4',
      'player_9',
      'player_7',
      'player_2',
      'pack',
    ]);
    expect(n2[4].seats).toEqual(['player_3', 'player_8']);
    expect(n2[4].target).toBe('player_4');
    const n3 = nightBranchesOf(viewAt(269), 3);
    expect(n3.find((b) => b.actor === 'pack')?.seats).toEqual(['player_8']);
  });

  it('lands the marks of earlier branches, and this one only on its mark step', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    const line = marksAt(n2, { actor: 'pack', rank: 4, step: 1, steps: 5 });
    expect(line.map((m) => [m.seat, m.kind, m.landing])).toEqual([
      ['player_2', 'lens', false],
      ['player_1', 'plaster', false],
      ['player_3', 'knife', false],
    ]);
    const bite = marksAt(n2, { actor: 'pack', rank: 4, step: 4, steps: 5 });
    expect(bite.at(-1)).toEqual({ seat: 'player_4', kind: 'bite', rank: 4, landing: true });
    expect(marksAt(n2, null)).toHaveLength(4);
    expect(marksAt(n2, null).every((m) => !m.landing)).toBe(true);
  });

  it('counts the acts in as the spokes are told', () => {
    const n2 = nightBranchesOf(viewAt(155), 2);
    expect(actedAt(n2, { actor: 'player_4', rank: 0, step: 0, steps: 1 }, 5)).toBe(1);
    expect(actedAt(n2, { actor: 'pack', rank: 4, step: 1, steps: 5 }, 5)).toBe(4);
    expect(actedAt(n2, null, 5)).toBe(5);
  });

  it('gives a seat that held (the vigilante holding its fire) a room with no mark', () => {
    // night 1: seat 7 consulted and read, and chose no one
    const n1 = nightBranchesOf(viewAt(57), 1);
    const held = n1.find((b) => b.actor === 'player_7')!;
    expect(held).toMatchObject({ role: 'vigilante', target: null, lines: 0 });
    expect(isHeld(held)).toBe(true);
    // one step, no mark on the wall; its step counts it in
    const rank = n1.indexOf(held);
    const spoke = { actor: 'player_7', rank, step: 0, steps: 1 };
    expect(marksAt(n1, spoke).some((m) => m.rank === rank)).toBe(false);
    expect(actedAt(n1, spoke, 5)).toBe(rank + 1);
    const cut = beats.find(
      (b) => b.id === 'rnight.spoke' && b.day === 1 && b.spoke?.actor === 'player_7',
    );
    expect(cut).toMatchObject({
      subject: 'player_7',
      holdMs: 4000,
      spoke: { step: 0, steps: 1 },
    });
    // night 4 the vigilante shot: no hold that night
    expect(
      isHeld(nightBranchesOf(viewAt(400), 4).find((b) => b.actor === 'player_7')),
    ).toBe(false);
  });
});

describe('the ten-seat X-ray night: the carrier’s kill is the pack’s', () => {
  const p3 = phase3.events as unknown as DurableGameEvent[];

  it('orders the branches exactly as the beat cutter does, on every spoke of both games', () => {
    for (const log of [p3, necro.events as unknown as DurableGameEvent[]]) {
      const spokes = beatsFor(log, { xray: true }).filter((b) => b.id === 'rnight.spoke');
      expect(spokes.length).toBeGreaterThan(0);
      for (const b of spokes) {
        const branches = nightBranchesOf(foldEvents(log.slice(0, b.end)), b.day);
        const br = branches[b.spoke!.rank];
        expect(br?.actor).toBe(b.spoke!.actor);
        expect(br.lines + (br.target || isHeld(br) ? 1 : 0)).toBe(b.spoke!.steps);
      }
    }
  });

  it('puts the kill (seq 91) in the pack’s branch and leaves the chanteuse her block (seq 94)', () => {
    const end = p3.findIndex((e) => e.type === 'night_result' && e.day === 1);
    const n1 = nightBranchesOf(foldEvents(p3.slice(0, end)), 1);
    const pack = n1.find((b) => b.actor === 'pack')!;
    expect(pack.target).toBe('player_7');
    expect(pack.lastSeq).toBeGreaterThanOrEqual(91);
    expect(n1.filter((b) => b.actor === 'player_5')).toEqual([
      expect.objectContaining({ role: 'chanteuse', target: 'player_1', lastSeq: 94 }),
    ]);
  });

  it('gives a carrier with no skill that night no branch of its own, and a conceal no mark', () => {
    const at = (day: number) =>
      foldEvents(
        p3.slice(
          0,
          p3.findIndex((e) => e.type === 'night_result' && e.day === day),
        ),
      );
    // night 3: the illusionist carried the kill (seq 326) and did nothing else
    expect(nightBranchesOf(at(3), 3).some((b) => b.actor === 'player_6')).toBe(false);
    // night 2: it carried the kill (216), then concealed the body (221, no target)
    const conceal = nightBranchesOf(at(2), 2).find((b) => b.actor === 'player_6')!;
    expect(conceal).toMatchObject({ role: 'illusionist', target: null, lastSeq: 221 });
    expect(isHeld(conceal)).toBe(true);
  });
});

describe('the spoke’s line, for every role in the pool', () => {
  it.each([
    ['healer', 'player_3', 'protects seat 3.'],
    ['investigator', 'player_6', 'checks seat 6.'],
    ['sentinel', 'player_5', 'watches seat 5.'],
    ['trailseer', 'player_5', 'follows seat 5.'],
    ['vigilante', 'player_6', 'shoots seat 6.'],
    ['sigilist', 'player_5', 'marks seat 5.'],
    ['chanteuse', 'player_1', 'blocks seat 1.'],
    ['serial_killer', 'player_2', 'kills seat 2.'],
    ['necromancer', 'player_1', 'acts on seat 1.'],
    ['fortune_teller', 'player_1', 'bets on seat 1.'],
    ['speculator', 'town', 'picks Town.'],
    ['speculator', 'wolves', 'picks the Wolves.'],
    ['speculator', 'lone_killer', 'picks the lone killer.'],
    ['speculator', 'self', 'picks itself.'],
    ['illusionist', null, 'conceals the body.'],
  ])('%s on %s: "%s"', (role, target, line) => {
    expect(actLine(role, target)).toBe(line);
  });

  it.each([
    ['vigilante', 'holds its fire.'],
    ['investigator', 'keeps its checks.'],
    ['sentinel', 'keeps its watches.'],
    ['sigilist', 'keeps its sigils.'],
    ['necromancer', 'stays put.'],
    ['speculator', 'waits.'],
  ])('%s holding: "%s"', (role, line) => {
    expect(actLine(role, null)).toBe(line);
  });

  it('says the conceal on the fixture’s night 2 (an act with no target)', () => {
    const p3 = phase3.events as unknown as DurableGameEvent[];
    const end = p3.findIndex((e) => e.type === 'night_result' && e.day === 2);
    const b = nightBranchesOf(foldEvents(p3.slice(0, end)), 2).find(
      (x) => x.actor === 'player_6',
    )!;
    expect(actLine(b.role, b.target)).toBe('conceals the body.');
  });
});
