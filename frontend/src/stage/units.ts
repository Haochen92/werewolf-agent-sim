/**
 * The stage's coordinate space: a fixed 1600×900 box, measured in units.
 *
 * Every position, size and path on the stage is written in units of this box, never in
 * screen pixels. The stage then scales the whole box once to fit whatever it is shown in
 * (see Stage.tsx), so a phone is just a smaller scale of the same picture, not a new
 * layout. That keeps sprite placement, beat timings and the HUD geometry identical on
 * every screen, and it means a number here can be checked against a bench by eye.
 *
 * The HUD geometry below was computed by the design kit at run time on every resize. It
 * depends only on the box size, and the box size no longer changes, so it is frozen here
 * as plain numbers: nothing on the stage recomputes it.
 */
import type { CSSProperties } from 'react';

export const STAGE_W = 1600;
export const STAGE_H = 900;
/**
 * How far the picture carries on past each side of the world, in units, for a screen wider
 * than 16:9 (stage_architecture.md §3 "The bleed"). Fixed: nothing redraws on resize. A 21:9
 * screen, where the bars return, shows 250 of it, and the camera never pulls back past 1, so
 * 300 is never exhausted; wider strips made headless Chromium rasterise the world's layer a
 * few levels differently (found at 600, 2026-09-25).
 */
export const BLEED = 300;
/** How far out the bleed reaches the house's full dark: the whole of what a 21:9 screen shows. */
export const BLEED_DARK = 250;

export type Hud = 'none' | 'live' | 'replay';

export interface StageGeometry {
  hud: Hud;
  /** The side slot (drawer or film) is open, so the room is narrower. */
  side: boolean;
  /** Width of the seat wing down the left edge (0 with no HUD). */
  wingN: number;
  /** Everything right of the wing. */
  area: number;
  /** Width of the side slot when it is open. */
  slotW: number;
  /** The rail (the stand's top edge) as a percentage of the height, and in units. */
  rail: number;
  railY: number;
  /** Width of the room the puppet is centred in (area minus the open slot). */
  room: number;
  /** The puppet box: height, width, top, left and centre line. */
  ph: number;
  pwid: number;
  top: number;
  left: number;
  cx: number;
  /** One puppet-kit unit (the puppet box is 525 of these wide); the stand is drawn in it. */
  u: number;
  /** Where the puppet's head sits, for lighting and speech anchors. */
  headTop: number;
  headBot: number;
  headC: number;
}

// Evaluated from StageKit.geometry(1600, 900, { hud, side }) in docs/design_2026-09-25/kits/
// stage-kit.js (VERSION 2026-09-23), with phone = false, in node on 2026-09-25.
export const GEOMETRY: Record<Hud, { full: StageGeometry; side: StageGeometry }> = {
  none: {
    full: {
      hud: 'none',
      side: false,
      wingN: 0,
      area: 1600,
      slotW: 672,
      rail: 71,
      railY: 639,
      room: 1600,
      ph: 642.1621621621621,
      pwid: 561.8918918918918,
      top: 45,
      left: 519.0540540540542,
      cx: 800,
      u: 1.07027027027027,
      headTop: 176.1081081081081,
      headBot: 470.43243243243234,
      headC: 323.27027027027026,
    },
    side: {
      hud: 'none',
      side: true,
      wingN: 0,
      area: 1600,
      slotW: 672,
      rail: 71,
      railY: 639,
      room: 928,
      ph: 642.1621621621621,
      pwid: 561.8918918918918,
      top: 45,
      left: 183.05405405405412,
      cx: 464,
      u: 1.07027027027027,
      headTop: 176.1081081081081,
      headBot: 470.43243243243234,
      headC: 323.27027027027026,
    },
  },
  live: {
    full: {
      hud: 'live',
      side: false,
      wingN: 88,
      area: 1512,
      slotW: 635.04,
      rail: 71,
      railY: 639,
      room: 1512,
      ph: 642.1621621621621,
      pwid: 561.8918918918918,
      top: 45,
      left: 563.0540540540542,
      cx: 844,
      u: 1.07027027027027,
      headTop: 176.1081081081081,
      headBot: 470.43243243243234,
      headC: 323.27027027027026,
    },
    side: {
      hud: 'live',
      side: true,
      wingN: 88,
      area: 1512,
      slotW: 635.04,
      rail: 71,
      railY: 639,
      room: 876.96,
      ph: 642.1621621621621,
      pwid: 561.8918918918918,
      top: 45,
      left: 245.53405405405414,
      cx: 526.48,
      u: 1.07027027027027,
      headTop: 176.1081081081081,
      headBot: 470.43243243243234,
      headC: 323.27027027027026,
    },
  },
  replay: {
    full: {
      hud: 'replay',
      side: false,
      wingN: 88,
      area: 1512,
      slotW: 635.04,
      rail: 68,
      railY: 612,
      room: 1512,
      ph: 612.9729729729729,
      pwid: 536.3513513513512,
      top: 45,
      left: 575.8243243243244,
      cx: 844,
      u: 1.0216216216216214,
      headTop: 170.14864864864865,
      headBot: 451.0945945945945,
      headC: 310.6216216216216,
    },
    side: {
      hud: 'replay',
      side: true,
      wingN: 88,
      area: 1512,
      slotW: 635.04,
      rail: 68,
      railY: 612,
      room: 876.96,
      ph: 612.9729729729729,
      pwid: 536.3513513513512,
      top: 45,
      left: 258.3043243243244,
      cx: 526.48,
      u: 1.0216216216216214,
      headTop: 170.14864864864865,
      headBot: 451.0945945945945,
      headC: 310.6216216216216,
    },
  },
};

/** The frozen geometry for a HUD mode, with or without the side slot open. */
export function geometry(hud: Hud = 'live', side = false): StageGeometry {
  return GEOMETRY[hud][side ? 'side' : 'full'];
}

// The HUD chrome the benches placed in CSS container units (1cqw = 16 units at 1600 wide),
// converted once: the top strip's height, the side slot's inset, the replay's transport band.
export const HUD_CHROME = {
  /** The side slot starts below the top strip (the bench's `top: 4.9cqw`). */
  topStrip: 78.4,
  /** The side slot's gap from the right edge and from the rail (`.8cqw`). */
  slotInset: 12.8,
  /** The replay's transport band along the bottom (`max(26px, 2.5cqw) + 1.2cqw`); live has none. */
  band: { none: 0, live: 0, replay: 59.2 } as Record<Hud, number>,
} as const;

/** The side slot's rectangle, in units, for a HUD mode (the drawer and the film share it). */
export function sideSlot(hud: Hud) {
  const g = geometry(hud, true);
  const x = STAGE_W - HUD_CHROME.slotInset - (g.slotW - 2 * HUD_CHROME.slotInset);
  return {
    x,
    y: HUD_CHROME.topStrip,
    w: g.slotW - 2 * HUD_CHROME.slotInset,
    h: g.railY - HUD_CHROME.topStrip - HUD_CHROME.slotInset,
  };
}

/**
 * The own stand's box, from the kit's `stand()`: 605 puppet units wide, centred on the
 * puppet, its top on the rail. The Stand instrument draws in these numbers.
 */
export function standBox(g: StageGeometry) {
  return { x: g.cx - 302.5 * g.u, y: g.railY, w: 605 * g.u, h: STAGE_H - g.railY };
}

/** Absolute placement in units. Inside the stage every px is a unit, so this is plain CSS. */
export function at(x: number, y: number, w?: number, h?: number): CSSProperties {
  return { position: 'absolute', left: x, top: y, width: w, height: h };
}
