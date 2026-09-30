import { describe, expect, it } from 'vitest';
import { fileTap, showFile, stripButtons } from './slot';

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
