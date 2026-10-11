import { describe, expect, it } from 'vitest';
import type { ReplaySummary } from '@/types/contracts';
import { endedLabel, formatDate } from './format';
import {
  NO_FILTERS,
  activeFilters,
  applyFilters,
  distinctModels,
  sortReplays,
  type ReplayFilters,
} from './replay-filters';

function row(over: Partial<ReplaySummary> & { game_id: string }): ReplaySummary {
  return {
    finished_at: '2026-09-01T12:00:00Z',
    winner: 'villagers',
    days: 4,
    ended_phase: 'day',
    n_events: 300,
    n_humans: 0,
    cast_role_counts: {},
    model: 'gemini-3.5-flash-lite',
    memory: false,
    ...over,
  };
}

const ROWS: ReplaySummary[] = [
  row({
    game_id: 'aaaa1111',
    winner: 'wolves',
    days: 4,
    ended_phase: 'night',
    finished_at: '2026-09-17T08:58:24Z',
    memory: true,
  }),
  row({
    game_id: 'bbbb2222',
    winner: 'villagers',
    days: 3,
    ended_phase: 'voting',
    finished_at: '2026-09-24T10:00:00Z',
    model: 'gemini-3.6-flash',
    n_humans: 1,
  }),
  row({
    game_id: 'cccc3333',
    winner: 'serial_killer',
    days: 6,
    ended_phase: 'night',
    finished_at: '2026-09-20T10:00:00Z',
    model: 'gemini-3.6-flash',
    n_humans: 3,
  }),
  row({
    game_id: 'dddd4444',
    winner: 'wolves',
    days: 5,
    ended_phase: null,
    finished_at: '2026-08-21T10:00:00Z',
    model: '',
  }),
];

const ids = (rows: ReplaySummary[]) => rows.map((r) => r.game_id);
const none = new Set<string>();
const run = (f: Partial<ReplayFilters>, mine: ReadonlySet<string> = none) =>
  ids(applyFilters(ROWS, { ...NO_FILTERS, ...f }, 'new', mine));

describe('archive filters', () => {
  it('no filters keeps every row, newest first', () => {
    expect(run({})).toEqual(['bbbb2222', 'cccc3333', 'aaaa1111', 'dddd4444']);
  });

  it('winner: any of the chosen factions', () => {
    expect(run({ winners: ['wolves'] })).toEqual(['aaaa1111', 'dddd4444']);
    expect(run({ winners: ['villagers', 'serial_killer'] })).toEqual([
      'bbbb2222',
      'cccc3333',
    ]);
  });

  it('ending phase: exact, and an unrecorded phase matches only "any"', () => {
    expect(run({ ended: 'night' })).toEqual(['cccc3333', 'aaaa1111']);
    expect(run({ ended: 'voting' })).toEqual(['bbbb2222']);
    expect(run({ ended: 'day' })).toEqual([]);
  });

  it('model: an id, or "" for the unrecorded ones', () => {
    expect(run({ model: 'gemini-3.6-flash' })).toEqual(['bbbb2222', 'cccc3333']);
    expect(run({ model: '' })).toEqual(['dddd4444']);
  });

  it('played on this device: only ids holding a seat token', () => {
    expect(run({ mine: true }, new Set(['cccc3333', 'not-in-archive']))).toEqual([
      'cccc3333',
    ]);
    expect(run({ mine: true })).toEqual([]);
  });

  it('memory, the table, the id search and the dates combine', () => {
    expect(run({ memory: 'on' })).toEqual(['aaaa1111']);
    expect(run({ table: 'agents' })).toEqual(['aaaa1111', 'dddd4444']);
    expect(run({ table: 'people', winners: ['serial_killer'] })).toEqual(['cccc3333']);
    expect(run({ q: '  BBBB ' })).toEqual(['bbbb2222']);
    expect(run({ from: '2026-09-17', to: '2026-09-20' })).toEqual(['cccc3333', 'aaaa1111']);
  });

  it('sorts by date and by length, ties newest first', () => {
    expect(ids(sortReplays(ROWS, 'old'))).toEqual([
      'dddd4444',
      'aaaa1111',
      'cccc3333',
      'bbbb2222',
    ]);
    expect(ids(sortReplays(ROWS, 'long'))).toEqual([
      'cccc3333',
      'dddd4444',
      'aaaa1111',
      'bbbb2222',
    ]);
    expect(ids(sortReplays(ROWS, 'short'))).toEqual([
      'bbbb2222',
      'aaaa1111',
      'dddd4444',
      'cccc3333',
    ]);
    const tie = [
      row({ game_id: 'x', days: 4, finished_at: '2026-01-01T00:00:00Z' }),
      row({ game_id: 'y', days: 4, finished_at: '2026-02-01T00:00:00Z' }),
    ];
    expect(ids(sortReplays(tie, 'long'))).toEqual(['y', 'x']);
    // sorting never reorders the caller's array
    expect(ids(ROWS)[0]).toBe('aaaa1111');
  });

  it('lists the distinct models, unrecorded last', () => {
    expect(distinctModels(ROWS)).toEqual(['gemini-3.5-flash-lite', 'gemini-3.6-flash', '']);
  });

  it('names each active filter and removes just that one', () => {
    const f: ReplayFilters = {
      ...NO_FILTERS,
      winners: ['wolves', 'villagers'],
      model: 'gemini-3.6-flash',
      ended: 'night',
    };
    const chips = activeFilters(f, (id) => `label:${id}`);
    expect(chips.map((c) => c.label)).toEqual([
      'Won by the wolves',
      'Won by the town',
      'Ended at night',
      'label:gemini-3.6-flash',
    ]);
    expect(chips[0].without.winners).toEqual(['villagers']);
    expect(chips[3].without.model).toBeNull();
    expect(activeFilters(NO_FILTERS, String)).toEqual([]);
  });
});

describe('slate formatting', () => {
  it('says where the game ended', () => {
    expect(endedLabel('night', 5)).toBe('Night 5');
    expect(endedLabel('day', 3)).toBe('Day 3');
    expect(endedLabel('voting', 4)).toBe('Day 4 vote');
    expect(endedLabel(null, 4)).toBeNull();
  });

  it('prints the finishing day in UTC', () => {
    expect(formatDate('2026-09-17T23:58:24Z')).toBe('17 Sep 2026');
    expect(formatDate('2026-01-01T00:30:00+01:00')).toBe('31 Dec 2025');
    expect(formatDate(null)).toBe('');
    expect(formatDate('nope')).toBe('');
  });
});
