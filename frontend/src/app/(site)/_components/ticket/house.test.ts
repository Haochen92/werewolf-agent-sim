import { describe, expect, it } from 'vitest';
import type { ModelRow, ModelsMenu } from '@/types/contracts';
import { defaultRow, houseLine, modelGroups, needsKey } from './house';

const row = (over: Partial<ModelRow>): ModelRow => ({
  model: 'm',
  label: 'M',
  rescue_model: null,
  house_funded: false,
  is_default: false,
  needs_key: true,
  priced_games: 0,
  ...over,
});

const menu = (house: Partial<ModelsMenu['house']> = {}): ModelsMenu => ({
  models: [
    row({ model: 'lite', label: 'Lite', house_funded: true, needs_key: false }),
    row({
      model: 'house',
      label: 'House',
      house_funded: true,
      is_default: true,
      needs_key: false,
    }),
    row({ model: 'own', label: 'Own' }),
  ],
  house: {
    enabled: true,
    games_per_day: 20,
    remaining: 3,
    reset_at: '2026-09-27T00:00:00Z',
    ...house,
  },
});

describe('needsKey', () => {
  it('asks for nothing before the menu has loaded', () => {
    expect(needsKey(undefined, 'own')).toBe(false);
  });

  it("follows the chosen row's needs_key", () => {
    expect(needsKey(menu(), 'house')).toBe(false);
    expect(needsKey(menu(), 'own')).toBe(true);
  });

  it('reads a blank or unknown choice as the default row', () => {
    const empty = menu();
    empty.models[1].needs_key = true; // the purse is spent: the server flips the default row
    expect(needsKey(empty, '')).toBe(true);
    expect(needsKey(empty, 'retired-model')).toBe(true);
  });
});

describe('defaultRow', () => {
  it('is the row marked default, else the first', () => {
    expect(defaultRow(menu())?.model).toBe('house');
    const none = menu();
    none.models[1].is_default = false;
    expect(defaultRow(none)?.model).toBe('lite');
  });
});

describe('houseLine', () => {
  it('says how many house games are left when the purse covers the row', () => {
    expect(houseLine(menu(), 'house')).toBe(
      'The house pays for this model: 3 of 20 games left today. Your own key is optional.',
    );
  });

  it('asks for a key when the purse is spent, and says when it refills', () => {
    expect(houseLine(menu({ remaining: 0 }), 'house')).toMatch(
      /^The house has funded its 20 games for today \(more at .+\)\. Enter your key to play now\.$/,
    );
  });

  it('asks for a key when house funding is off', () => {
    expect(houseLine(menu({ enabled: false }), 'house')).toBe(
      'House funding is switched off for now. Enter your key to play.',
    );
  });

  it('says a key-only row runs on the player’s key', () => {
    expect(houseLine(menu(), 'own')).toBe('This model runs on your own key.');
  });

  it('says nothing about a row the menu does not list', () => {
    expect(houseLine(menu(), 'retired-model')).toBe('');
  });
});

describe('modelGroups', () => {
  it('puts house rows under Recommended with the default first, and leaves out an empty group', () => {
    const rows = [
      row({ model: 'a', label: 'A', house_funded: true }),
      row({ model: 'b', label: 'B', house_funded: true, is_default: true }),
      row({ model: 'c', label: 'C' }),
    ];
    expect(modelGroups(rows)).toEqual([
      {
        group: 'Recommended',
        items: [
          { value: 'b', label: 'B' },
          { value: 'a', label: 'A' },
        ],
      },
      { group: 'With your own key', items: [{ value: 'c', label: 'C' }] },
    ]);
    expect(modelGroups([rows[2]]).map((g) => g.group)).toEqual(['With your own key']);
  });
});
