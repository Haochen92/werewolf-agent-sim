import { describe, expect, it } from 'vitest';
import { BODY, CHARACTERS, SPRITES } from './manifest';

const DAY_STATES = ['base', 'talking', 'thinking', 'out', 'chip'] as const;
const KITS = [
  'healer',
  'investigator',
  'vigilante',
  'serial_killer',
  'wolf',
  'villager',
  'clock',
  'lamp',
] as const;

const hasSize = (img: { width: number; height: number }) =>
  expect(img.width > 0 && img.height > 0).toBe(true);

describe('sprite manifest', () => {
  it('has all eleven characters', () => {
    expect(CHARACTERS).toHaveLength(11);
    expect(new Set(CHARACTERS).size).toBe(11);
  });

  it('has every day state and chip for every character', () => {
    expect(Object.keys(SPRITES.day).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) {
      expect(Object.keys(SPRITES.day[character]).sort()).toEqual([...DAY_STATES].sort());
      for (const state of DAY_STATES) hasSize(SPRITES.day[character][state]);
    }
  });

  it('has a plush for every character, all eight kits and the wood', () => {
    expect(Object.keys(SPRITES.plush).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) hasSize(SPRITES.plush[character]);
    expect(Object.keys(SPRITES.kits).sort()).toEqual([...KITS].sort());
    for (const kit of KITS) hasSize(SPRITES.kits[kit]);
    hasSize(SPRITES.wood);
  });

  it('has a body measure for every character that fills the height', () => {
    expect(Object.keys(BODY).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) {
      const { top, body } = BODY[character];
      expect(top).toBeGreaterThan(0);
      expect(top).toBeLessThan(1);
      expect(top + body).toBeCloseTo(1, 3);
    }
  });
});
