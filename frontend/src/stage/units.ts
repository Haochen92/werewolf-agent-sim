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
 * depends only on the box size, and the box size no longer changes, so it is evaluated once
 * here, at load, from the kit's formula: nothing on the stage recomputes it.
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
/**
 * The closest the stage's camera comes: the vote's count pushes in to 1.32 (`countShot` in
 * instruments/vote-geometry.ts), and nothing else scales the world up. A picture chosen for
 * the stage's size has to hold up at this magnification too (instruments/Backdrop.tsx).
 */
export const CAMERA_ZOOM_MAX = 1.32;

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

/**
 * The seat rail's width inside the world (HUD pass 2, owner 2026-09-29): two columns of seat
 * cards, 12% of the width (owner, 2026-09-29: 9% drew the desk's cards too thin). The kit's
 * wing was 5.5% (88 units), one column of small tiles. On a screen wider than 16:9 the rail
 * carries on out into the bleed (`railLayout`'s `reach`), so a phone's letterbox holds part of
 * it and the room keeps more of its width.
 */
export const WING_N = 192;

/**
 * StageKit.geometry(1600, 900, { hud, side }) in docs/design_2026-09-25/kits/stage-kit.js
 * (VERSION 2026-09-23), phone = false, with the wing at `WING_N` in place of the kit's 5.5%.
 * A pure function of fixed numbers, evaluated once below: nothing on the stage recomputes it.
 */
function kitGeometry(hud: Hud, side: boolean): StageGeometry {
  const W = STAGE_W,
    H = STAGE_H;
  const wingN = hud === 'none' ? 0 : WING_N,
    area = W - wingN,
    slotW = area * 0.42;
  const rail = hud === 'replay' ? 68 : 71;
  const railY = (rail / 100) * H,
    room = side ? area - slotW : area;
  let ph = (railY - 0.05 * H) / 0.925,
    pwid = (ph * 210) / 240;
  if (pwid > room * 0.96) {
    pwid = room * 0.96;
    ph = (pwid * 240) / 210;
  }
  const top = railY - 0.925 * ph,
    left = wingN + (room - pwid) / 2;
  return {
    hud,
    side,
    wingN,
    area,
    slotW,
    rail,
    railY,
    room,
    ph,
    pwid,
    top,
    left,
    cx: left + pwid / 2,
    u: pwid / 525,
    headTop: top + (49 / 240) * ph,
    headBot: top + (159 / 240) * ph,
    headC: top + (104 / 240) * ph,
  };
}

export const GEOMETRY: Record<Hud, { full: StageGeometry; side: StageGeometry }> = {
  none: { full: kitGeometry('none', false), side: kitGeometry('none', true) },
  live: { full: kitGeometry('live', false), side: kitGeometry('live', true) },
  replay: { full: kitGeometry('replay', false), side: kitGeometry('replay', true) },
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

/**
 * Where what stands on the band's top edge sits: `extra` units above the band. On a phone the
 * band grows so its buttons reach a thumb's 44 css px (`--band-grown`, set by the replay
 * theatre's stylesheet on the stage's box); everything on it rises with it. With no band (the
 * live HUD) it is the plain number, so a golden at full size is unchanged.
 */
export function bandFoot(hud: Hud, extra: number): number | string {
  const band = HUD_CHROME.band[hud];
  return band ? `calc(max(${band}px, var(--band-grown, 0px)) + ${extra}px)` : extra;
}

/**
 * How far the side slot grows past the world's right edge at most, on a screen wider than 16:9
 * (`--slot-reach` in Stage.module.css, the bleed shown there up to this): the rail's reach for
 * nine seats (its 310-unit target less its 192), so the wing and the pane stand alike on a
 * phone. The slot's left edge, and so the room beside it, never move.
 */
export const SLOT_REACH = 118;

/**
 * The side slot's rectangle, in units, for a HUD mode (the drawer and the film share it). Its
 * drawn width adds `var(--slot-reach)` (see SLOT_REACH).
 */
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
