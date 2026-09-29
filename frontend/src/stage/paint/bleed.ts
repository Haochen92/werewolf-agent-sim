/**
 * The bleed: the room carried on past the world's left and right edges, for a screen wider
 * than 16:9 (stage_architecture.md §3). Two strips, each BLEED units wide, the room's floor and
 * sky continued at the same heights in the same colours, darkening outwards to the house's dark
 * by BLEED_DARK units out, so the sides read as the theatre's dark around the stage rather than
 * as more room. The stage's outer box clips them to the screen.
 *
 * Each strip starts as dark as the room is at its own edge, so the seam never shows: the
 * station darkens its own sides (station.ts, `stationFront`), so its strips start near that
 * dark. The painted rooms (the dining car, the night compartments) cannot be carried on; their
 * sides sink into the dark instead (instruments/Bleed.tsx, `PaintedBleed`).
 */
import { BLEED, BLEED_DARK, STAGE_H, STAGE_W } from '../units';
import { STATION } from './materials';

export interface BleedOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  /** Which room carries on: the waiting room's platform. */
  room: 'station';
}

/** How dark each room already is at the world's edge, where its strips start. */
const EDGE: Record<BleedOpts['room'], number> = { station: 0.85 };

/* the platform between x0 and x1: the sky, the track bed, the paving and its edge, the beam */
function station(x0: number, x1: number): string {
  const H = STAGE_H,
    w = x1 - x0,
    floorY = 0.66 * H,
    beamH = 0.052 * H;
  return (
    `<rect x="${x0}" y="0" width="${w}" height="${0.45 * H}" fill="${STATION.sky}"/>` +
    `<rect x="${x0}" y="${0.45 * H}" width="${w}" height="${floorY - 0.45 * H}" fill="#0b0a09"/>` +
    `<rect x="${x0}" y="${floorY}" width="${w}" height="${H - floorY}" fill="${STATION.floor}"/>` +
    `<rect x="${x0}" y="${floorY}" width="${w}" height="${0.038 * H}" fill="${STATION.edge}"/>` +
    `<rect x="${x0}" y="0" width="${w}" height="${beamH}" fill="${STATION.beam}"/>` +
    `<rect x="${x0}" y="${beamH - 4.05}" width="${w}" height="4.05" fill="${STATION.trim}"/>`
  );
}

/** Both strips, as SVG markup in the world's own coordinates (drawn past its viewBox). */
export function bleed(o: BleedOpts): string {
  const W = STAGE_W,
    H = STAGE_H,
    b = BLEED,
    P = o.id + '-',
    e = EDGE[o.room];
  let d = station(-b, 0) + station(W, W + b);
  // the darkening: from the room's own edge value at the seam to the house's dark
  const at = (x: number) => ((x + b) / (W + 2 * b)).toFixed(4);
  const stop = (x: number, a: number) =>
    `<stop offset="${at(x)}" stop-color="#0c0a07" stop-opacity="${a}"/>`;
  d += `<defs><linearGradient id="${P}bdark" gradientUnits="userSpaceOnUse" x1="${-b}" y1="0" x2="${W + b}" y2="0">${stop(-BLEED_DARK, 1)}${stop(0, e)}${stop(W, e)}${stop(W + BLEED_DARK, 1)}</linearGradient></defs>`;
  d += `<rect x="${-b}" y="0" width="${b}" height="${H}" fill="url(#${P}bdark)"/><rect x="${W}" y="0" width="${b}" height="${H}" fill="url(#${P}bdark)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${d}</svg>`;
}
