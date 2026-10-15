import { describe, expect, it } from 'vitest';
import type { MemoryExtracted } from '@/types/contracts';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { byPhase, ledgerTabs, stripVerdict, verdictKind } from './ledger';

const extracted = FIXTURE_EVENTS.find(
  (e) => e.type === 'memory_extracted',
) as MemoryExtracted;
const roles = {
  player_1: 'villager',
  player_2: 'serial_killer',
  player_3: 'wolf',
  player_4: 'investigator',
  player_5: 'villager',
  player_6: 'villager',
  player_7: 'vigilante',
  player_8: 'wolf',
  player_9: 'healer',
};

describe('the ledger on the fixture’s extraction', () => {
  const tabs = ledgerTabs(extracted, roles);

  it('has one tab per role, in the cast’s order, with the seats that held it', () => {
    expect(tabs.map((t) => t.role)).toEqual([
      'villager',
      'healer',
      'investigator',
      'vigilante',
      'wolf',
      'serial_killer',
    ]);
    expect(tabs[0].seats).toEqual(['player_1', 'player_5', 'player_6']);
    expect(tabs.find((t) => t.role === 'wolf')?.seats).toEqual(['player_3', 'player_8']);
    expect(tabs.reduce((n, t) => n + t.rows.length, 0)).toBe(51);
  });

  it('tallies each tab’s verdicts, and its pips read the tally in order', () => {
    const wolf = tabs.find((t) => t.role === 'wolf')!;
    expect(wolf.tally).toEqual({ worked: 9, cost: 2, mixed: 1, unclear: 0 });
    expect(wolf.pips.join(' ')).toBe(
      'worked worked worked worked worked worked worked worked worked mixed cost cost',
    );
    const inv = tabs.find((t) => t.role === 'investigator')!;
    expect(inv.tally).toEqual({ worked: 0, cost: 3, mixed: 0, unclear: 0 });
    for (const t of tabs) expect(t.pips).toHaveLength(t.rows.length);
  });

  it('groups a tab’s rows by phase: the discussion, the vote, the night', () => {
    const wolf = tabs.find((t) => t.role === 'wolf')!;
    const groups = byPhase(wolf.rows);
    expect(groups.map((g) => [g.phase, g.rows.length])).toEqual([
      ['day_discussion', 2],
      ['day_vote', 4],
      ['night_action', 6],
    ]);
    const inv = byPhase(tabs.find((t) => t.role === 'investigator')!.rows);
    expect(inv.map((g) => g.phase)).toEqual(['day_discussion', 'day_vote', 'night_action']);
  });

  it('names the verdicts as the patches do, and drops the verdict word from the outcome', () => {
    expect(['positive', 'negative', 'mixed', 'unclear', 'odd'].map(verdictKind)).toEqual([
      'worked',
      'cost',
      'mixed',
      'unclear',
      'unclear',
    ]);
    expect(stripVerdict('Negative. The village lost.')).toBe('The village lost.');
  });

  it('keeps no lessons from this game', () => {
    expect(extracted.strategy_points).toEqual([]);
  });
});
