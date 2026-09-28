/**
 * The station platform: the waiting room's backdrop (review 2026-09-26 §A5, ruling F1), before
 * the train leaves for the deal.
 *
 * A winter night under the station's canopy. At the back, the painted country (a raster) with
 * the moon over it and the track bed below; on the track, the train (the dining car in the
 * middle, its one long window holding the nine places, a carriage either side); in front, the
 * cold stone platform, its edge the same stone under a soft drift of snow, two iron lamp posts
 * with their lanterns hung out over the platform, and a walnut beam with a brass trim along the
 * top, snow lying on it. The people waiting stand on
 * the platform, one under each place in the window, so the row on the platform mirrors the
 * row in the car.
 *
 * Two drawings, because the train and the platform's paving (both rasters, placed by the
 * scene) sit between them: `stationBack` (sky, moon, track) and `stationFront` (the edge, the
 * lamps' pools, the cold over everything behind the posts, the posts, the lamps, the beam).
 * `stationPlan` says where everything is, for the scene's rasters and instruments.
 *
 * Ported from the waiting-room mockup (`claude_artifacts/design/pages/waiting-room.html`),
 * whose geometry is in container units of a 16:9 box: 1cqw = 16 units, 1cqh = 9 units here.
 * The pictures are passed in as URLs (`SPRITES.station.*`), as the car takes its wood.
 */
import { STAGE_H, STAGE_W, geometry, type Hud } from '../units';
import { STATION } from './materials';

/** The train picture's own geometry, in the pixels of the master it was cut from (the mockup's `G`). */
const TRAIN_PX = {
  w: 11980,
  h: 1400,
  /** The dining car's window, left to right and top to bottom. */
  wx0: 4316,
  wx1: 7663,
  wy0: 393,
  wy1: 809,
  /** The roof's snow line and the wheels' foot. */
  snow: 61,
  bottom: 1379,
} as const;

/** The car from its roof's snow to its wheels (48cqh), and where that snow sits (16cqh). */
const CAR_H = 432;
const SNOW_Y = 144;

/** The post and lamp pictures' proportions (width / height). */
const POST_ASPECT = 489 / 1024;
const LAMP_ASPECT = 569 / 1008;

/** A box in units. */
export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface StationPlan {
  /** The room's centre line: the dining car's window and the station sign sit on it. */
  cx: number;
  /** The whole train picture at rest. */
  train: Box;
  /** The dining car's long window, in world units (the train at rest). */
  glass: Box;
  /** One place's width in the window. */
  pitch: number;
  /** The nine places' centres, left to right; the platform's marks sit under them. */
  places: number[];
  /** The top of the brass plates under the window. */
  plateY: number;
  /** The platform's top (its stone edge), and the edge's depth. */
  floorY: number;
  edgeH: number;
  /** Where the people waiting stand, and how tall a body is there. */
  feetY: number;
  bodyH: number;
  /** The two lamp posts: the pole's x, and whether the picture is mirrored (the right one). */
  posts: { x: number; mirror: boolean }[];
  /** The two lanterns' centres, hung out over the platform from the posts' arms. */
  lamps: number[];
  /** The post and lantern boxes' heights and tops. */
  post: { top: number; h: number; w: number };
  lamp: { top: number; h: number; w: number };
  /** How far right the train travels to leave the world (it is clipped at the world's edges). */
  pull: number;
}

/** Where everything on the platform is, in units, for a HUD mode (the wing narrows the room). */
export function stationPlan(hud: Hud = 'live'): StationPlan {
  const g = geometry(hud);
  // one master pixel in units, the same both ways (the mockup's `s`, turned into units)
  const k = CAR_H / (TRAIN_PX.bottom - TRAIN_PX.snow);
  const cx = g.wingN + g.area / 2;
  const wlen = (TRAIN_PX.wx1 - TRAIN_PX.wx0) * k;
  const wl = cx - wlen / 2;
  const train = {
    x: wl - TRAIN_PX.wx0 * k,
    y: SNOW_Y - TRAIN_PX.snow * k,
    w: TRAIN_PX.w * k,
    h: TRAIN_PX.h * k,
  };
  const glass = {
    x: wl,
    y: train.y + TRAIN_PX.wy0 * k,
    w: wlen,
    h: (TRAIN_PX.wy1 - TRAIN_PX.wy0) * k,
  };
  const pitch = wlen / 9;
  const postH = 0.69 * STAGE_H;
  const lampH = 0.13 * STAGE_H;
  // the posts stand 4.6cqw outside the window's ends; the lanterns hang 9.4cqw in from them
  const posts = [
    { x: wl - 73.6, mirror: false },
    { x: wl + wlen + 73.6, mirror: true },
  ];
  return {
    cx,
    train,
    glass,
    pitch,
    places: Array.from({ length: 9 }, (_, i) => wl + (i + 0.5) * pitch),
    plateY: glass.y + glass.h + 4.5,
    floorY: 0.66 * STAGE_H,
    edgeH: 0.038 * STAGE_H,
    feetY: 0.775 * STAGE_H,
    bodyH: 0.2 * STAGE_H,
    posts,
    lamps: [posts[0].x + 150.4, posts[1].x - 150.4],
    post: { top: 0.74 * STAGE_H - postH, h: postH, w: postH * POST_ASPECT },
    lamp: { top: 0.074 * STAGE_H, h: lampH, w: lampH * LAMP_ASPECT },
    // past the right edge, with a little to spare
    pull: STAGE_W - train.x + 64,
  };
}

export interface StationOpts {
  /** Prefix for every id this drawing makes, so two stages can share a page. */
  id: string;
  hud?: Hud;
  /** The painted country behind the track (`SPRITES.station.sky.src`); without it, flat sky. */
  sky?: string;
  /** The lamp post and the lantern; without them, neither is drawn. */
  post?: string;
  lamp?: string;
  /** The beam's walnut (`SPRITES.wood.src`) and the edge's stone (`SPRITES.station.floor.src`); without them, flat. */
  wood?: string;
  stone?: string;
}

const f = (n: number) => n.toFixed(1);
const svg = (d: string) =>
  `<svg viewBox="0 0 ${STAGE_W} ${STAGE_H}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${d}</svg>`;

/** The back: the night sky and the country, the moon, the track bed and its rails. */
export function stationBack(o: StationOpts): string {
  const W = STAGE_W,
    P = o.id + '-',
    S = stationPlan(o.hud),
    // the country fills the width and stands on the sky's foot (the mockup's 100% auto, bottom)
    skyH = 0.5 * STAGE_H,
    picH = (W * 627) / 2508,
    trackY = 0.45 * STAGE_H,
    trackH = 0.21 * STAGE_H,
    moonX = S.cx + 432,
    moonY = 129;
  let d = `<defs><linearGradient id="${P}bed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgb(14,16,26)" stop-opacity="0"/><stop offset=".18" stop-color="rgb(14,16,26)" stop-opacity=".85"/><stop offset=".4" stop-color="#0d0c0e"/><stop offset=".75" stop-color="#0b0a09"/><stop offset="1" stop-color="#15120f"/></linearGradient><linearGradient id="${P}rail" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.railTop}"/><stop offset="1" stop-color="${STATION.railBot}"/></linearGradient></defs>`;
  d += `<rect x="0" y="0" width="${W}" height="${skyH}" fill="${STATION.sky}"/>`;
  if (o.sky)
    d += `<image href="${o.sky}" x="0" y="${f(skyH - picH)}" width="${W}" height="${f(picH)}" preserveAspectRatio="none"/>`;
  d += `<circle cx="${moonX}" cy="${moonY}" r="38.4" fill="${STATION.moon}" opacity=".07"/><circle cx="${moonX}" cy="${moonY}" r="15.4" fill="${STATION.moon}" opacity=".92"/>`;
  // the bed, and its two rails: the near one at 78% down, the far one a little above it
  const rail = trackY + trackH * 0.78;
  d += `<rect x="0" y="${f(trackY)}" width="${W}" height="${f(trackH)}" fill="url(#${P}bed)"/>`;
  d += `<rect x="0" y="${f(rail - 28.8)}" width="${W}" height="4" fill="${STATION.railFar}"/><rect x="0" y="${f(rail)}" width="${W}" height="4.5" fill="url(#${P}rail)"/>`;
  return svg(d);
}

/**
 * The front: the platform's stone edge and the drift on it, the lamps' warm pools on the paving,
 * the night's cold over everything behind the posts, a darkening at the world's sides (where the
 * bleed takes over), the two posts and their lanterns, and the walnut beam along the top.
 */
export function stationFront(o: StationOpts): string {
  const W = STAGE_W,
    H = STAGE_H,
    P = o.id + '-',
    S = stationPlan(o.hud),
    y = S.floorY,
    eh = S.edgeH,
    // the stone tiles at 9cqw on the edge, the walnut at 14cqw on the beam (both square)
    stoneW = 144,
    woodW = 224,
    beamH = 0.052 * H,
    trim = 4.05;
  let d = `<defs>`;
  if (o.stone)
    d += `<pattern id="${P}stone" patternUnits="userSpaceOnUse" x="0" y="${f(y)}" width="${stoneW}" height="${stoneW}"><image href="${o.stone}" width="${stoneW}" height="${stoneW}" preserveAspectRatio="none"/></pattern>`;
  d += `<linearGradient id="${P}edgeTint" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.edgeTintTop}" stop-opacity=".25"/><stop offset="1" stop-color="${STATION.edgeTintBot}" stop-opacity=".45"/></linearGradient>`;
  d += `<linearGradient id="${P}edgeLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.edgeLight}" stop-opacity=".9"/><stop offset=".45" stop-color="${STATION.edgeLight}" stop-opacity="0"/></linearGradient>`;
  d += `<linearGradient id="${P}drift" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.drift}" stop-opacity="0"/><stop offset="1" stop-color="${STATION.drift}" stop-opacity=".85"/></linearGradient>`;
  d += `<linearGradient id="${P}shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".45"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>`;
  d += `<radialGradient id="${P}pool" cx=".5" cy=".3" r=".5" gradientTransform="translate(0 .3) scale(1 .9) translate(0 -.3)"><stop offset="0" stop-color="${STATION.lamp}" stop-opacity=".2"/><stop offset=".7" stop-color="${STATION.lamp}" stop-opacity="0"/></radialGradient>`;
  d += `<linearGradient id="${P}cold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgb(20,30,60)" stop-opacity=".1"/><stop offset="1" stop-color="rgb(10,15,35)" stop-opacity=".26"/></linearGradient>`;
  d += `<linearGradient id="${P}sides" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0c0a07" stop-opacity=".85"/><stop offset=".1" stop-color="#0c0a07" stop-opacity="0"/><stop offset=".9" stop-color="#0c0a07" stop-opacity="0"/><stop offset="1" stop-color="#0c0a07" stop-opacity=".85"/></linearGradient>`;
  if (o.wood)
    d += `<pattern id="${P}wood" patternUnits="userSpaceOnUse" x="0" y="0" width="${woodW}" height="${woodW}"><image href="${o.wood}" width="${woodW}" height="${woodW}" preserveAspectRatio="none"/></pattern>`;
  d += `<linearGradient id="${P}beamShade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.beamShadeTop}" stop-opacity=".25"/><stop offset="1" stop-color="${STATION.beamShadeBot}" stop-opacity=".55"/></linearGradient>`;
  d += `<linearGradient id="${P}lip" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${STATION.lipTop}"/><stop offset="1" stop-color="${STATION.lipBot}"/></linearGradient>`;
  d += `<filter id="${P}postsh" x="-20%" y="-5%" width="140%" height="110%"><feDropShadow dx="6.4" dy="0" stdDeviation="4.8" flood-color="#000" flood-opacity=".45"/></filter>`;
  d += `<filter id="${P}glow" x="-150%" y="-80%" width="400%" height="260%"><feDropShadow dx="0" dy="0" stdDeviation="19.2" flood-color="${STATION.lamp}" flood-opacity=".55"/></filter>`;
  d += `</defs>`;
  // the edge: its shadow on the paving, the stone lit from above, its dark foot, the drift on it
  d += `<rect x="0" y="${f(y + eh)}" width="${W}" height="12" fill="url(#${P}shade)"/>`;
  d += `<rect x="0" y="${f(y)}" width="${W}" height="${f(eh)}" fill="${o.stone ? `url(#${P}stone)` : STATION.edge}"/>`;
  d += `<rect x="0" y="${f(y)}" width="${W}" height="${f(eh)}" fill="url(#${P}edgeTint)"/>`;
  d += `<rect x="0" y="${f(y)}" width="${W}" height="${f(eh)}" fill="url(#${P}edgeLight)"/>`;
  d += `<rect x="0" y="${f(y + eh - 2.7)}" width="${W}" height="2.7" fill="#000" opacity=".35"/>`;
  d += `<rect x="0" y="${f(y - 5.4)}" width="${W}" height="9.9" fill="url(#${P}drift)"/>`;
  // each lantern's pool on the paving below it
  for (const lx of S.lamps)
    d += `<rect x="${f(lx - 240)}" y="${f(y)}" width="480" height="234" fill="url(#${P}pool)"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${H}" fill="url(#${P}cold)"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${H}" fill="url(#${P}sides)"/>`;
  if (o.post)
    for (const p of S.posts) {
      const { top, h, w } = S.post;
      // the pole stands 11.5% in from the picture's left edge; the right post is its mirror
      d += p.mirror
        ? `<image href="${o.post}" width="${f(w)}" height="${f(h)}" preserveAspectRatio="none" filter="url(#${P}postsh)" transform="translate(${f(p.x + 0.115 * w)} ${f(top)}) scale(-1 1)"/>`
        : `<image href="${o.post}" x="${f(p.x - 0.115 * w)}" y="${f(top)}" width="${f(w)}" height="${f(h)}" preserveAspectRatio="none" filter="url(#${P}postsh)"/>`;
    }
  if (o.lamp)
    for (const lx of S.lamps) {
      const { top, h, w } = S.lamp;
      d += `<image href="${o.lamp}" x="${f(lx - w / 2)}" y="${f(top)}" width="${f(w)}" height="${f(h)}" preserveAspectRatio="none" filter="url(#${P}glow)"/>`;
    }
  // the beam: its shadow on the scene, the walnut darkened, a dark line over the brass trim at
  // its foot, and the snow on top, thinning towards the ends
  d += `<rect x="0" y="${f(beamH)}" width="${W}" height="18" fill="url(#${P}shade)"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${f(beamH)}" fill="${o.wood ? `url(#${P}wood)` : STATION.beam}"/>`;
  d += `<rect x="0" y="0" width="${W}" height="${f(beamH)}" fill="url(#${P}beamShade)"/>`;
  d += `<rect x="0" y="${f(beamH - 6.3)}" width="${W}" height="6.3" fill="#000" opacity=".35"/>`;
  d += `<rect x="0" y="${f(beamH - trim)}" width="${W}" height="${trim}" fill="${STATION.trim}"/>`;
  d += `<path d="M0,0 H${W} V0.1 A${0.4 * W},8.1 0 0 1 ${0.6 * W},8.1 H${0.4 * W} A${0.4 * W},8.1 0 0 1 0,0.1Z" fill="url(#${P}lip)" opacity=".9"/>`;
  return svg(d);
}
