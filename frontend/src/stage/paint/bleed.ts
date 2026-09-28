/**
 * The bleed: the room carried on past the world's left and right edges, for a screen wider
 * than 16:9 (stage_architecture.md §3). Two strips, each BLEED units wide, the room's wall and
 * floor continued at the same heights in the same materials and the hour's tint, darkening
 * outwards to the house's dark by BLEED_DARK units out, so the sides read as the theatre's dark
 * around the stage rather than as more room. The stage's outer box clips them to the screen.
 *
 * Each strip starts as dark as the room is at its own edge, so the seam never shows: the
 * dining car fades its wall and apron into the dark at both ends (the kit's `qfade`, the
 * Apron's fade), so its strips start there and are near-black; the station darkens its own
 * sides (station.ts, `stationFront`), so its strips start near that dark. The night rooms are
 * paintings and carry their own edges (instruments/Compartment.tsx).
 *
 * The car's back flat is re-drawn here from its materials, not by calling the car: the car is
 * held byte-for-byte to the design kit (paint.test.ts), so it cannot be split into parts.
 * Given `wood`, the car's strips take its textures, laid on the same world grid as its own
 * (paint/texture.ts), so the grain runs on across the seam.
 */
import { BLEED, BLEED_DARK, STAGE_H, STAGE_W, geometry, type Hud } from '../units';
import { K2 } from './draw';
import { BOARD, BOARD2, CAR, ROOMLIGHT, STATION, type Phase } from './materials';
import { boards, DARKER, veneer, walnutAcross, walnutImage, type Wood } from './texture';
import { carLines } from './window';

export interface BleedOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  /** Which room carries on: the dining car or the waiting room's platform. */
  room: 'car' | 'station';
  /** The car's hour: its tint falls on the strips as it falls on the walls. */
  phase?: Phase;
  hud?: Hud;
  /** The car's walnut and boards; without them, flat. */
  wood?: Wood;
}

/** How dark each room already is at the world's edge, where its strips start. */
const EDGE: Record<BleedOpts['room'], number> = { car: 0.95, station: 0.85 };

/* the car's textures, as the car (dining-car.ts) and the Floor instrument lay them */
function carTextures(P: string, wood: Wood, hud: Hud): string {
  const { floorY, floorH, B } = carLines(geometry(hud));
  return `<defs>${walnutImage(P + 'wimg', wood.walnut)}${veneer(P + 'wal', P + 'wimg', 0, 0.08 * STAGE_W)}${walnutAcross(P + 'wald', P + 'wimg')}${boards(P + 'brd', wood.boards, floorY, floorH / 2)}${boards(P + 'apr', wood.boards, B + 0.045 * STAGE_H, 0.05 * STAGE_H)}</defs>`;
}

/* the car's back flat, apron and floor between x0 and x1, on the car's panel lines; P names its textures */
function car(x0: number, x1: number, phase: Phase, hud: Hud, P: string | null): string {
  const W = STAGE_W,
    H = STAGE_H,
    s = 1,
    w = x1 - x0,
    { floorY, floorH, dado, B } = carLines(geometry(hud)),
    step = 0.08 * W;
  let d = `<rect x="${x0}" y="0" width="${w}" height="${floorY}" fill="${P ? `url(#${P}wal)` : CAR.wall}"/>`;
  for (let px = Math.ceil(x0 / step) * step; px < x1; px += step)
    d += `<path d="M${px.toFixed(0)},0 V${dado}" stroke="${CAR.wallDark}" stroke-width="${4 * s}"/>`;
  d += `<rect x="${x0}" y="${dado}" width="${w}" height="${floorY - dado}" fill="${P ? `url(#${P}wald)` : CAR.dado}"/>`;
  if (P)
    d += `<rect x="${x0}" y="${dado}" width="${w}" height="${floorY - dado}" fill="#000" opacity="${DARKER['#3a2212']}"/>`;
  d += `<rect x="${x0}" y="${dado - 4 * s}" width="${w}" height="${8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.4 * s}"/>`;
  d += `<rect x="${x0}" y="0" width="${w}" height="${floorY}" fill="${CAR.wallDark}" opacity=".38"/>`;
  d += `<rect x="${x0}" y="${floorY}" width="${w}" height="${floorH}" fill="${P ? `url(#${P}brd)` : BOARD}"/><path d="M${x0},${(floorY + floorH / 2).toFixed(0)} H${x1}" stroke="${BOARD2}" stroke-width="${1.6 * s}" opacity=".7"/>`;
  // the apron below the rail, as the Floor instrument draws it
  d += `<rect x="${x0}" y="${B - 2}" width="${w}" height="${H - B + 2}" fill="${P ? `url(#${P}apr)` : BOARD}"/>`;
  for (let y = B + 0.045 * H; y < H; y += 0.05 * H)
    d += `<path d="M${x0},${y.toFixed(0)} H${x1}" stroke="${BOARD2}" stroke-width="1.6" opacity="0.7"/>`;
  const Lt = ROOMLIGHT[phase];
  if (Lt.tint)
    d += `<rect x="${x0}" y="0" width="${w}" height="${H}" fill="${Lt.tint}" opacity="${Lt.a}" style="mix-blend-mode:multiply"/>`;
  return d;
}

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
    hud = o.hud ?? 'live',
    P = o.id + '-',
    e = EDGE[o.room];
  let d = '';
  if (o.room === 'car') {
    const T = o.wood ? P : null;
    if (o.wood) d += carTextures(P, o.wood, hud);
    d += car(-b, 0, o.phase ?? 'day', hud, T) + car(W, W + b, o.phase ?? 'day', hud, T);
  } else d = station(-b, 0) + station(W, W + b);
  // the darkening: from the room's own edge value at the seam to the house's dark
  const at = (x: number) => ((x + b) / (W + 2 * b)).toFixed(4);
  const stop = (x: number, a: number) =>
    `<stop offset="${at(x)}" stop-color="#0c0a07" stop-opacity="${a}"/>`;
  d += `<defs><linearGradient id="${P}bdark" gradientUnits="userSpaceOnUse" x1="${-b}" y1="0" x2="${W + b}" y2="0">${stop(-BLEED_DARK, 1)}${stop(0, e)}${stop(W, e)}${stop(W + BLEED_DARK, 1)}</linearGradient></defs>`;
  d += `<rect x="${-b}" y="0" width="${b}" height="${H}" fill="url(#${P}bdark)"/><rect x="${W}" y="0" width="${b}" height="${H}" fill="url(#${P}bdark)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${d}</svg>`;
}
