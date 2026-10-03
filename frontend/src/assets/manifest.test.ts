import { describe, expect, it } from 'vitest';
import { LEGACY_CHARACTERS } from '@/stage/cast/castForGame';
import { BODY, CHARACTERS, HEAD_FRAME, REACH, SPRITES } from './manifest';

const DAY_STATES = ['base', 'talking', 'thinking', 'out', 'head'] as const;
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
  it('has all fifteen characters, the frozen eleven first', () => {
    expect(CHARACTERS).toHaveLength(15);
    expect(new Set(CHARACTERS).size).toBe(15);
    expect(CHARACTERS.slice(0, 11)).toEqual(LEGACY_CHARACTERS);
  });

  it('has every day state and head for every character', () => {
    expect(Object.keys(SPRITES.day).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) {
      expect(Object.keys(SPRITES.day[character]).sort()).toEqual([...DAY_STATES].sort());
      for (const state of DAY_STATES) hasSize(SPRITES.day[character][state]);
    }
  });

  it('has all eight kits and the wood', () => {
    expect(Object.keys(SPRITES.kits).sort()).toEqual([...KITS].sort());
    for (const kit of KITS) hasSize(SPRITES.kits[kit]);
    hasSize(SPRITES.wood);
  });

  it('has a night room for each acting role and the pack, cropped to the stage’s band', () => {
    expect(Object.keys(SPRITES.rooms).sort()).toEqual(
      ['healer', 'investigator', 'serial_killer', 'vigilante', 'wolf'].sort(),
    );
    for (const img of Object.values(SPRITES.rooms))
      expect([img.width, img.height]).toEqual([1536, 915]);
  });

  it('has a felt figure for every role, on one 3:4 canvas', () => {
    expect(Object.keys(SPRITES.roles).sort()).toEqual(
      ['healer', 'investigator', 'serial_killer', 'vigilante', 'villager', 'wolf'].sort(),
    );
    for (const img of Object.values(SPRITES.roles))
      expect([img.width, img.height]).toEqual([720, 960]);
  });

  it('has the dining car by day and by night, fitted to the stage', () => {
    expect(Object.keys(SPRITES.car).sort()).toEqual(['day', 'night']);
    for (const img of Object.values(SPRITES.car))
      expect([img.width, img.height]).toEqual([1600, 900]);
  });

  it('has the room’s surface textures', () => {
    expect(Object.keys(SPRITES.textures).sort()).toEqual([
      'boards',
      'cork',
      'ink',
      'velvet',
      'walnut',
    ]);
    for (const img of Object.values(SPRITES.textures)) hasSize(img);
  });

  it('has the painted props, the three late ones at their painted sizes', () => {
    expect(Object.keys(SPRITES.props).sort()).toEqual(
      ['jarGlass', 'jarLid', 'plate', 'shutter', 'stand', 'valance', 'voteTable'].sort(),
    );
    for (const img of Object.values(SPRITES.props)) hasSize(img);
    // the plate is squashed to ry = 0.3 rx; the valance spans the stage; the shutter is 8:3
    expect([SPRITES.props.plate.width, SPRITES.props.plate.height]).toEqual([900, 270]);
    expect([SPRITES.props.valance.width, SPRITES.props.valance.height]).toEqual([
      2000, 395,
    ]);
    expect([SPRITES.props.shutter.width, SPRITES.props.shutter.height]).toEqual([
      1640, 615,
    ]);
  });

  it('has the station’s pictures', () => {
    expect(Object.keys(SPRITES.station).sort()).toEqual(
      ['blind', 'floor', 'lamp', 'post', 'sky', 'train'].sort(),
    );
    for (const img of Object.values(SPRITES.station)) hasSize(img);
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

  it('has a reach and a cast shadow for every character, and the phone’s copies', () => {
    expect(Object.keys(REACH).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) {
      for (const state of ['base', 'talking', 'thinking', 'out'] as const) {
        hasSize(SPRITES.shadow.day[character][state]);
        hasSize(SPRITES.small.day[character][state]);
      }
    }
  });

  it('frames every head so its cut collar stays out of the circle', () => {
    expect(Object.keys(HEAD_FRAME).sort()).toEqual([...CHARACTERS].sort());
    for (const character of CHARACTERS) {
      const { s, y } = HEAD_FRAME[character];
      expect(s / 2 + y).toBeGreaterThanOrEqual(0.5);
    }
  });
});
