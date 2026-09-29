import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { BLEED, geometry, STAGE_W, WING_N, type Hud } from '../units';
import { bleed } from './bleed';
import { CAR_PICTURE, diningCarPlan } from './dining-car';
import { drape } from './drape';
import { light } from './light';
import { PHASES_IN_ORDER } from './materials';
import { photoTwine, roomChoice, roomLight, roomPlan, ROOMS } from './compartment';
import { stationBack, stationFront, stationPlan } from './station';
import { shutter } from './window';

const HUDS: Hud[] = ['none', 'live', 'replay'];
const ROOM_NAMES = Object.keys(ROOMS) as (keyof typeof ROOMS)[];

const idsOf = (html: string) => [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
const refsOf = (html: string) => [...html.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1]);

/** Every generator, at every option it takes, as (label, prefix → markup). */
const CASES: [string, (id: string) => string][] = [
  ...HUDS.flatMap((hud) =>
    (['open', 'closed'] as const).map(
      (state) =>
        [`shutter ${state} ${hud}`, (id: string) => shutter({ id, hud, state })] as [
          string,
          (id: string) => string,
        ],
    ),
  ),
  ...(['open', 'closed'] as const).map(
    (state) =>
      [
        `shutter ${state} walnut`,
        (id: string) => shutter({ id, state, walnut: '/walnut.webp' }),
      ] as [string, (id: string) => string],
  ),
  ...ROOM_NAMES.flatMap((room) =>
    HUDS.flatMap((hud) =>
      [false, true].map(
        (side) =>
          [
            `roomLight ${room} ${hud}${side ? ' side' : ''}`,
            (id: string) => roomLight({ id, room, hud, side, n: 8 }),
          ] as [string, (id: string) => string],
      ),
    ),
  ),
  ['photoTwine', (id: string) => photoTwine({ id, room: 'healer' })],
  ...PHASES_IN_ORDER.flatMap((phase) =>
    (['over', 'stand'] as const).map(
      (from) =>
        [
          `light ${phase} ${from}`,
          (id: string) => {
            const plan = diningCarPlan({ phase });
            return light({
              id,
              from,
              scene: { glows: plan.glows, specials: plan.specials },
            });
          },
        ] as [string, (id: string) => string],
    ),
  ),
  ['drape', () => drape()],
  ['drape bleed', (id: string) => drape({ id, bleed: BLEED })],
  ['drape velvet', (id: string) => drape({ id, velvet: '/velvet.webp' })],
  [
    'drape bleed velvet',
    (id: string) => drape({ id, bleed: BLEED, velvet: '/velvet.webp' }),
  ],
  ['bleed station', (id: string) => bleed({ id, room: 'station' })],
  ...HUDS.flatMap((hud) => [
    [`stationBack ${hud}`, (id: string) => stationBack({ id, hud, sky: '/sky.webp' })] as [
      string,
      (id: string) => string,
    ],
    [
      `stationFront ${hud}`,
      (id: string) =>
        stationFront({
          id,
          hud,
          post: '/post.webp',
          lamp: '/lamp.webp',
          wood: '/wood.webp',
          stone: '/stone.webp',
        }),
    ] as [string, (id: string) => string],
    [`stationFront ${hud} flat`, (id: string) => stationFront({ id, hud })] as [
      string,
      (id: string) => string,
    ],
  ]),
  ['light bleed', (id: string) => light({ id, bleed: BLEED })],
  [
    'light lamps',
    (id: string) =>
      light({ id, lamps: diningCarPlan({ phase: 'day' }).lamps, bleed: BLEED }),
  ],
  ['roomLight bleed', (id: string) => roomLight({ id, room: 'wolf', bleed: BLEED })],
];

describe.each(CASES)('%s', (_label, draw) => {
  const a = draw('stA');
  const b = draw('stB');

  it('returns SVG markup', () => {
    expect(a).toContain('<svg');
  });

  it('prefixes every id with the caller’s id', () => {
    for (const id of idsOf(a)) expect(id.startsWith('stA')).toBe(true);
  });

  it('shares no id with a drawing under another prefix', () => {
    const inB = new Set(idsOf(b));
    for (const id of idsOf(a)) expect(inB.has(id)).toBe(false);
  });

  it('only references ids it defines', () => {
    const defined = new Set(idsOf(a));
    for (const ref of refsOf(a)) expect(defined.has(ref)).toBe(true);
  });
});

/* The port must draw what the kit draws: the frozen kit, evaluated as-is, is the reference. */
describe('fidelity to kits/stage-kit.js', () => {
  const src = readFileSync(
    fileURLToPath(
      new URL('../../../docs/design_2026-09-25/kits/stage-kit.js', import.meta.url),
    ),
    'utf8',
  );
  // The painting's departure (2026-09-29): the car is a painting (SPRITES.car), so nothing of the
  // kit's drawing is compared, only where things are. Its wall clock is gone (the owner ruled it
  // out), and the lantern's special and glow sit on the painted lantern rather than in the slot
  // right of the window; the painting's two table lamps glow as the lantern does. The painting's
  // lamps are measured in its own pixels at the layout it was fitted to (CAR_PICTURE.fit), so the
  // kit places them from its own centre line and rail.
  const at = (p: readonly [number, number]) =>
    `${p[0] - CAR_PICTURE.fit.cx} + sh.cx, ${p[1] - CAR_PICTURE.fit.railY} + sh.B`;
  const tableGlows = CAR_PICTURE.tableLamps
    .map((p) => `[${at(p)}, c.lit ? 0.3 * H : 0.06 * H, "#ffb35c"]`)
    .join(', ');
  const pieces: [string, string][] = [
    // the seat rail (HUD pass 2, 2026-09-29): the wing is WING_N wide, not the kit's 5.5%
    [
      'const wingN = on ? W * (phone ? 0.049 : 0.055) : 0',
      `const wingN = on ? (phone ? W * 0.049 : ${WING_N}) : 0`,
    ],
    ['    if (slotL[1] - slotL[0] > 0.06 * W) parts.push(wallClock(ctx, sh, c, slotL));\n', ''],
    [
      'x = (slot[0] + slot[1]) / 2, y = 0.3 * H, iron = "#1c1a18"',
      `[x, y] = [${at(CAR_PICTURE.lantern)}], iron = "#1c1a18"`,
    ],
    [
      'parts.push(lantern(ctx, sh, c, slotR));',
      `parts.push(lantern(ctx, sh, c, slotR));\n    parts.push({ d: "", emit: "", glows: [${tableGlows}], wins: [] });`,
    ],
  ];
  it('finds the kit’s clock and lantern to swap for the painting’s lamps', () => {
    for (const [from] of pieces) expect(src.split(from)).toHaveLength(2);
  });
  // The kit is a plain script that declares one global; evaluate it and take that global.
  const swapped = pieces.reduce((s, [from, to]) => s.replace(from, to), src);
  const Kit = new Function(`${swapped}; return StageKit;`)();
  // the lamps are placed by sums the kit does in another order: equal to well under a unit
  const round = (v: unknown) => JSON.parse(JSON.stringify(v), (_k, n) =>
    typeof n === 'number' ? Math.round(n * 1e6) / 1e6 : n,
  );

  for (const hud of HUDS)
    for (const side of [false, true])
      for (const phase of PHASES_IN_ORDER)
        it(`the car's plan and light match scene() and light() at ${phase}, hud ${hud}${side ? ', side' : ''}`, () => {
          const g = Kit.geometry(1600, 900, { hud, side });
          const sc = Kit.scene(g, phase, { id: 'k' });
          const plan = diningCarPlan({ phase, hud, side });
          expect(plan.window).toEqual(sc.window);
          expect(plan.floor).toEqual(sc.floor);
          expect(plan.slots).toEqual(sc.slots);
          expect(round(plan.glows)).toEqual(round(sc.glows));
          expect(round(plan.specials)).toEqual(round(sc.specials));
          expect(light({ id: 'k', hud, side, from: 'over', scene: plan })).toBe(
            Kit.light(g, sc, { id: 'k', from: 'over' }),
          );
          expect(light({ id: 'k', hud, side, scene: plan, dark: 70 })).toBe(
            Kit.light(g, sc, { id: 'k', dark: 70 }),
          );
        });
});

/* The painted car: where its picture and glass sit for each layout. */
describe('the dining car’s painting', () => {
  it('centres its glass on the puppet and lays its floor on the rail, in every layout', () => {
    for (const hud of HUDS)
      for (const side of [false, true]) {
        const g = geometry(hud, side),
          P = diningCarPlan({ phase: 'day', hud, side });
        expect(P.glass.x + P.glass.w / 2).toBeCloseTo(g.cx, 6);
        expect(P.picture.y + CAR_PICTURE.fit.railY).toBe(g.railY);
        // the glass sits inside the kit's window, which the shutter covers
        const [wx, wy, ww, wh] = P.window;
        expect(P.glass.x).toBeGreaterThanOrEqual(wx);
        expect(P.glass.x + P.glass.w).toBeLessThanOrEqual(wx + ww);
        expect(P.glass.y + P.glass.h).toBeLessThanOrEqual(wy + wh + 1);
      }
  });

  it('has no wall clock, and lights the painted lantern and table lamps', () => {
    const P = diningCarPlan({ phase: 'night', hud: 'none' });
    expect(P).not.toHaveProperty('clock');
    const lamps = [CAR_PICTURE.lantern, ...CAR_PICTURE.tableLamps];
    expect(P.glows.map(([x, y]) => [x, y])).toEqual(lamps.map(([x, y]) => [x, y]));
  });

  it('cuts each painted lamp a clean hole in the dark, on the lamp, in every layout and hour', () => {
    const lamps = [CAR_PICTURE.lantern, ...CAR_PICTURE.tableLamps];
    for (const hud of HUDS)
      for (const side of [false, true])
        for (const phase of PHASES_IN_ORDER) {
          const P = diningCarPlan({ phase, hud, side });
          expect(P.lamps.map(([x, y]) => [x - P.picture.x, y - P.picture.y])).toEqual(
            lamps.map(([x, y]) => [x, y]),
          );
          expect(P.lamps.every(([, , , a]) => a === 1)).toBe(true);
          const html = light({
            id: 'k',
            hud,
            side,
            scene: P,
            lamps: P.lamps,
            bleed: BLEED,
          });
          // unblurred, full at the flame: a gradient hole each, and each warmed
          expect(html.match(/fill="url\(#k-lamp\)"/g)).toHaveLength(3);
          expect(html).not.toMatch(/url\(#k-lamp\)"[^>]*filter=/);
          expect(html.match(/radial-gradient\(circle/g)).toHaveLength(3);
        }
  });
});

/* The bleed: two strips past the world's sides, darkening outwards to the house's dark. */
describe('bleed', () => {
  const station = bleed({ id: 'stA', room: 'station' });

  it('draws both strips, outside the world and nowhere in it', () => {
    expect(station).toContain(`<rect x="${-BLEED}" y="0" width="${BLEED}"`);
    expect(station).toContain(`<rect x="${STAGE_W}" y="0" width="${BLEED}"`);
  });

  it('darkens to the house’s dark, from the room’s own edge value', () => {
    expect(station).toMatch(/<linearGradient id="stA-bdark"[^>]*gradientUnits="userSpaceOnUse"/);
    expect(station).toContain('stop-color="#0c0a07" stop-opacity="1"');
    expect(station).toContain('fill="url(#stA-bdark)"');
    // it starts from how dark the platform already is at its edge
    expect(station).toContain('stop-opacity="0.85"');
  });

  it('leaves the light and the drape as they were without it', () => {
    expect(light({ id: 'k', bleed: 0 })).toBe(light({ id: 'k' }));
    expect(drape({ id: 'k' })).toBe(drape());
    expect(roomLight({ id: 'k', room: 'healer', bleed: 0 })).toBe(
      roomLight({ id: 'k', room: 'healer' }),
    );
    expect(roomChoice({ room: 'healer', chosen: 2, bleed: 0 })).toBe(
      roomChoice({ room: 'healer', chosen: 2 }),
    );
  });
});

/* The seat's own room at night: a painted compartment, photos on a line, the card on the table. */
describe('the night rooms', () => {
  it('lays the painting across the room right of the wing, and slides it left for the slot', () => {
    for (const room of ROOM_NAMES) {
      const full = roomPlan({ room });
      expect(full.picture.x + full.picture.w).toBeCloseTo(STAGE_W, 6);
      expect(full.picture.h).toBeGreaterThanOrEqual(900);
      // the slot opens at x 978: the window's glass ends at its edge, the wall stays in view
      const side = roomPlan({ room, side: true });
      expect(side.glass.x + side.glass.w).toBeLessThan(992);
      expect(side.glass.x).toBeGreaterThan(geometry('live').wingN);
    }
  });

  it('hangs every photo on the wall in view, clear of the wing and left of the window', () => {
    for (const room of ROOM_NAMES)
      for (const side of [false, true])
        for (const n of [3, 5, 8]) {
          const R = roomPlan({ room, side, n });
          expect(R.photos).toHaveLength(n);
          for (const p of R.photos) {
            expect(p.x - R.photo.w / 2).toBeGreaterThan(geometry('live').wingN);
            expect(p.x + R.photo.w / 2).toBeLessThan(R.glass.x);
            expect(p.drop).toBeGreaterThan(0);
          }
          // two heights (three with the slot open) for a full line, one row for a short one;
          // beside the slot, right of the seat rail, a short line may already need two
          const rows = new Set(R.photos.map((p) => p.row)).size;
          if (!side) expect(rows).toBe(n <= 4 ? 1 : 2);
          else expect(rows).toBe(n === 8 ? 3 : n <= 3 ? Math.min(rows, 2) : 2);
        }
  });

  it('stands the card on the table below the glass, left of the candle', () => {
    for (const room of ROOM_NAMES)
      for (const side of [false, true]) {
        const R = roomPlan({ room, side });
        expect(R.card.foot).toBeGreaterThan(R.glass.y + R.glass.h);
        expect(R.card.x + R.card.w / 2).toBeLessThan(R.candle.x);
      }
  });

  it('lights with gradients alone: no filter and no blend mode', () => {
    for (const room of ROOM_NAMES) {
      const lit = roomLight({ id: 'k', room }) + roomChoice({ room, chosen: 2 });
      expect(lit).not.toContain('filter');
      expect(lit).not.toContain('mix-blend-mode');
    }
  });

  it('leaves the table lit on a choice, and draws nothing for a photo that is not there', () => {
    expect(roomChoice({ room: 'healer', chosen: 2 })).toContain('mask-image');
    expect(roomChoice({ room: 'healer', chosen: 99 })).toBe('');
  });
});

/* The station: the platform the waiting room stands on, and its bleed. */
describe('station', () => {
  it('centres the dining car’s window on the room right of the wing, nine places in it', () => {
    for (const hud of HUDS) {
      const S = stationPlan(hud);
      expect(S.glass.x + S.glass.w / 2).toBeCloseTo(S.cx, 6);
      expect(S.places).toHaveLength(9);
      expect(S.places[0] - S.pitch / 2).toBeCloseTo(S.glass.x, 6);
      expect(S.places[8] + S.pitch / 2).toBeCloseTo(S.glass.x + S.glass.w, 6);
    }
    expect(stationPlan('none').cx).toBe(800);
    expect(stationPlan('live').cx).toBe(WING_N + (STAGE_W - WING_N) / 2);
  });

  it('pulls the whole train out past the world’s right edge', () => {
    const S = stationPlan('live');
    expect(S.train.x + S.pull).toBeGreaterThan(STAGE_W);
  });

  it('draws the pictures it is given, and none without them', () => {
    expect(stationBack({ id: 'k', sky: '/sky.webp' })).toContain('href="/sky.webp"');
    expect(stationBack({ id: 'k' })).not.toContain('<image');
    const front = stationFront({
      id: 'k',
      post: '/p.webp',
      lamp: '/l.webp',
      wood: '/w.webp',
      stone: '/s.webp',
    });
    // two posts (one mirrored), two lanterns, the beam's walnut and the edge's stone
    expect(front.match(/href="\/p\.webp"/g)).toHaveLength(2);
    expect(front).toContain('scale(-1 1)');
    expect(front.match(/href="\/l\.webp"/g)).toHaveLength(2);
    expect(front).toContain('href="/w.webp"');
    expect(front).toContain('href="/s.webp"');
    expect(stationFront({ id: 'k' })).not.toContain('<image');
  });

  it('carries the platform into the bleed from its own darkened sides', () => {
    const html = bleed({ id: 'stA', room: 'station' });
    expect(html).toContain(`<rect x="${-BLEED}" y="0" width="${BLEED}"`);
    expect(html).toContain(`<rect x="${STAGE_W}" y="0" width="${BLEED}"`);
    expect(html).toContain('stop-opacity="0.85"');
    expect(stationFront({ id: 'k' })).toContain('stop-opacity=".85"');
  });
});
