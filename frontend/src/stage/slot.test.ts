import { describe, expect, it } from 'vitest';
import {
  fileTap,
  packNightSlot,
  packNightStep,
  pressFile,
  pressXray,
  showFile,
  showRecord,
  slotOf,
  stripButtons,
} from './slot';

describe('the strip’s Reveal switch', () => {
  it('is drawn only when the container has one: the replay’s to press, live’s locked', () => {
    expect(stripButtons({ slot: null, xray: false }).reveal).toBeUndefined();
    const press = () => {};
    expect(stripButtons({ slot: null, xray: true }, { onReveal: press }).reveal).toEqual({
      on: true,
      onPress: press,
      locked: false,
    });
    // live before the game ends: locked, off; after it: on, nothing to press
    expect(
      stripButtons({ slot: null, xray: false }, { revealLocked: true }).reveal,
    ).toEqual({
      on: false,
      onPress: undefined,
      locked: true,
    });
    expect(
      stripButtons({ slot: null, xray: true }, { revealLocked: false }).reveal,
    ).toEqual({
      on: true,
      onPress: undefined,
      locked: false,
    });
  });
});

describe('a seat tapped for its file', () => {
  const open = () => {};
  it('opens only with the X-ray on, where nobody speaks, and when the container can', () => {
    expect(fileTap({ xray: true }, { onOpenFile: open }, true)).toBe(open);
    expect(fileTap({ xray: false }, { onOpenFile: open }, true)).toBeNull();
    expect(fileTap({ xray: true }, { onOpenFile: open }, false)).toBeNull();
    expect(fileTap({ xray: true }, {}, true)).toBeNull();
  });

  it('brings the file to the pane from anywhere, and never without the X-ray', () => {
    for (const slot of [null, 'drawer', 'film'] as const)
      expect(showFile({ slot, xray: true })).toEqual({ xray: true, slot: 'film' });
    expect(showFile({ slot: 'drawer', xray: false })).toEqual({
      xray: false,
      slot: 'drawer',
    });
  });
});

describe('the case file without the X-ray (the Record)', () => {
  it('opens and closes from the File tab, X-ray or not', () => {
    for (const xray of [false, true]) {
      expect(pressFile({ slot: 'drawer', xray })).toEqual({ xray, slot: 'film' });
      expect(pressFile({ slot: null, xray })).toEqual({ xray, slot: 'film' });
      expect(pressFile({ slot: 'film', xray })).toEqual({ xray, slot: null });
    }
    // the file is in the slot whatever the X-ray says
    expect(slotOf({ slot: 'film' })).toBe('film');
    expect(stripButtons({ slot: 'film', xray: false }).file).toBe(true);
  });

  it('stays in the slot when Reveal is switched, going to the Record when it goes off', () => {
    expect(pressXray({ slot: 'film', xray: true })).toEqual({ xray: false, slot: 'film' });
    expect(pressXray({ slot: 'film', xray: false })).toEqual({ xray: true, slot: 'film' });
    expect(pressXray({ slot: 'drawer', xray: true })).toEqual({
      xray: false,
      slot: 'drawer',
    });
  });

  it('comes to the pane from the transcript’s pointer, from anywhere', () => {
    for (const slot of [null, 'drawer', 'film'] as const)
      for (const xray of [false, true])
        expect(showRecord({ slot, xray })).toEqual({ xray, slot: 'film' });
  });
});

describe('the wolves’ night in the transcript (owner, 2026-10-17)', () => {
  const at = (scene: string, day: number) =>
    ({ scene, day }) as Parameters<typeof packNightStep>[0];

  it('opens once a night, when the pack’s room first comes on stage, for a wolf only', () => {
    expect(packNightStep(at('pack', 2), true, null)).toBe('open');
    expect(packNightStep(at('pack', 2), false, null)).toBeNull();
    // opened for this night already: a reader who shut it keeps it shut
    expect(packNightStep(at('pack', 2), true, 2)).toBeNull();
    expect(packNightStep(at('pack', 3), true, 2)).toBe('open');
  });

  it('stays through the night’s other rooms and closes when the night is over', () => {
    for (const scene of ['night', 'room', 'pack'])
      expect(packNightStep(at(scene, 2), true, 2)).toBeNull();
    expect(packNightStep(at('morning', 2), true, 2)).toBe('close');
    expect(packNightStep(at('over', 2), true, 2)).toBe('close');
    // a night it did not open has nothing to close
    expect(packNightStep(at('morning', 2), true, null)).toBeNull();
  });

  it('brings the transcript, and at dawn takes only the transcript away', () => {
    for (const slot of [null, 'drawer', 'film'] as const)
      expect(packNightSlot({ slot, xray: false }, true).slot).toBe('drawer');
    expect(packNightSlot({ slot: 'drawer', xray: false }, false).slot).toBeNull();
    expect(packNightSlot({ slot: 'film', xray: false }, false).slot).toBe('film');
  });
});
