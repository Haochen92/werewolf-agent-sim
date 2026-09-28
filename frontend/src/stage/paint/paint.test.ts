import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { BLEED, geometry, STAGE_W, type Hud } from '../units';
import { bleed } from './bleed';
import { diningCar, diningCarPlan } from './dining-car';
import { drape } from './drape';
import { light } from './light';
import { PHASES_IN_ORDER } from './materials';
import { photoTwine, roomChoice, roomLight, roomPlan, ROOMS } from './compartment';
import { stationBack, stationFront, stationPlan } from './station';
import { boards, DARKER, veneer, walnutAcross, walnutImage } from './texture';
import { carLines, shutter } from './window';

const HUDS: Hud[] = ['none', 'live', 'replay'];
const ROOM_NAMES = Object.keys(ROOMS) as (keyof typeof ROOMS)[];
const WOOD = { walnut: '/walnut.webp', boards: '/boards.webp' };

const idsOf = (html: string) => [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
const refsOf = (html: string) => [...html.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1]);

/** Every generator, at every option it takes, as (label, prefix → markup). */
const CASES: [string, (id: string) => string][] = [
  ...PHASES_IN_ORDER.flatMap((phase) =>
    HUDS.flatMap((hud) =>
      [false, true].map(
        (side) =>
          [
            `diningCar ${phase} ${hud}${side ? ' side' : ''}`,
            (id: string) => diningCar({ id, phase, hud, side }),
          ] as [string, (id: string) => string],
      ),
    ),
  ),
  ...HUDS.map(
    (hud) =>
      [
        `diningCar night ${hud} wood`,
        (id: string) => diningCar({ id, phase: 'night', hud, wood: WOOD }),
      ] as [string, (id: string) => string],
  ),
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
  ...PHASES_IN_ORDER.flatMap((phase) =>
    HUDS.map(
      (hud) =>
        [
          `bleed car ${phase} ${hud}`,
          (id: string) => bleed({ id, room: 'car', phase, hud }),
        ] as [string, (id: string) => string],
    ),
  ),
  [
    'bleed car wood',
    (id: string) => bleed({ id, room: 'car', phase: 'dusk', wood: WOOD }),
  ] as [string, (id: string) => string],
  ...HUDS.flatMap((hud) => [
    [`bleed station ${hud}`, (id: string) => bleed({ id, room: 'station', hud })] as [
      string,
      (id: string) => string,
    ],
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
  // The window's departure: the kit's vector country behind the glass is gone (the felt pictures
  // lie over it), so its glass becomes a plain fill of the hour's top sky colour.
  const country =
    'winSky(ctx, c, wx, wy, ww, wh, s, { orb: true, r: rr }) + `<g clip-path="url(#${ctx.P}ws${Math.round(wx)}c)">${snowfall(wx, wy, ww, wh, s)}</g>`';
  const glass =
    '`<rect x="${wx}" y="${wy}" width="${ww}" height="${wh}" rx="${rr}" fill="${c.skyTop}"/>`';
  // The wall clock and the lantern's departure (2026-09-27): both are painted pictures now
  // (WallClock, WallLamp), so the kit's vector pieces draw nothing; their specials, the lantern's
  // halo and pool and the room's glows stay the car's. Only the lit lantern's flame goes too.
  const pieces: [string, string][] = [
    [
      'return { d: cutout(ctx.P, s, d, 1), emit, glows, wins: [] };',
      'return { d: "", emit, glows, wins: [] };',
    ],
    [' + flameAt(x, y + 0.005 * H, 1.2 * s);', ';'],
    [
      'return { d: `<g class="sk-hang">${cutout(ctx.P, s, d, 1)}</g>`, emit: "", glows: [], wins: [] };',
      'return { d: "", emit: "", glows: [], wins: [] };',
    ],
  ];
  it('finds the kit’s country to swap for the glass, and its clock and lantern', () => {
    expect(src.split(country)).toHaveLength(2);
    for (const [from] of pieces) expect(src.split(from)).toHaveLength(2);
  });
  // The kit is a plain script that declares one global; evaluate it and take that global.
  const swapped = pieces.reduce(
    (s, [from, to]) => s.replace(from, to),
    src.replace(country, glass),
  );
  const Kit = new Function(`${swapped}; return StageKit;`)();

  for (const hud of HUDS)
    for (const side of [false, true])
      for (const phase of PHASES_IN_ORDER)
        it(`diningCar and light match scene() and light() at ${phase}, hud ${hud}${side ? ', side' : ''}`, () => {
          const g = Kit.geometry(1600, 900, { hud, side });
          const sc = Kit.scene(g, phase, { id: 'k' });
          expect(diningCar({ id: 'k', phase, hud, side })).toBe(sc.html);
          const plan = diningCarPlan({ phase, hud, side });
          expect(plan.window).toEqual(sc.window);
          expect(plan.floor).toEqual(sc.floor);
          expect(light({ id: 'k', hud, side, from: 'over', scene: plan })).toBe(
            Kit.light(g, sc, { id: 'k', from: 'over' }),
          );
          expect(light({ id: 'k', hud, side, scene: plan, dark: 70 })).toBe(
            Kit.light(g, sc, { id: 'k', dark: 70 }),
          );
        });

  // The textures' departure (2026-09-27): given `wood`, the kit's flat walnut, dado and boards
  // are filled with the texture patterns instead (defined after the kit's first defs), the dado
  // under a black veil to its darker value. Nothing else changes.
  const textured = (html: string, hud: Hud) => {
    const { floorY, floorH, dado } = carLines(geometry(hud));
    const P = 'k-';
    const one = (h: string, from: string, to: string) => {
      expect(h.split(from)).toHaveLength(2);
      return h.replace(from, to);
    };
    const defs = `<defs>${walnutImage(P + 'wimg', WOOD.walnut)}${veneer(P + 'wal', P + 'wimg', 0, 128)}${walnutAcross(P + 'wald', P + 'wimg')}${boards(P + 'brd', WOOD.boards, floorY, floorH / 2)}</defs>`;
    let h = one(
      html,
      '</defs><rect width="1600" height="900" fill="#0c0a07"/>',
      `</defs>${defs}<rect width="1600" height="900" fill="#0c0a07"/>`,
    );
    h = one(
      h,
      `height="${floorY}" fill="#4a2c18"/>`,
      `height="${floorY}" fill="url(#${P}wal)"/>`,
    );
    const dadoRect = `<rect x="0" y="${dado}" width="1600" height="${floorY - dado}"`;
    h = one(
      h,
      `${dadoRect} fill="#3a2212"/>`,
      `${dadoRect} fill="url(#${P}wald)"/>${dadoRect} fill="#000" opacity="${DARKER['#3a2212']}"/>`,
    );
    h = one(
      h,
      `height="${floorH}" fill="#5a3f26"/>`,
      `height="${floorH}" fill="url(#${P}brd)"/>`,
    );
    return one(
      h,
      `fill="#5a3f26" stroke="#2a1a0c"`,
      `fill="url(#${P}brd)" stroke="#2a1a0c"`,
    );
  };
  for (const hud of HUDS)
    for (const side of [false, true])
      for (const phase of PHASES_IN_ORDER)
        it(`diningCar with wood is scene() with its textures at ${phase}, hud ${hud}${side ? ', side' : ''}`, () => {
          const sc = Kit.scene(Kit.geometry(1600, 900, { hud, side }), phase, { id: 'k' });
          expect(diningCar({ id: 'k', phase, hud, side, wood: WOOD })).toBe(
            textured(sc.html, hud),
          );
        });
});

/* The bleed: two strips past the world's sides, darkening outwards to the house's dark. */
describe('bleed', () => {
  const car = bleed({ id: 'stA', room: 'car', phase: 'night', hud: 'live' });
  const station = bleed({ id: 'stA', room: 'station', hud: 'live' });

  it('draws both strips, outside the world and nowhere in it', () => {
    for (const html of [car, station]) {
      expect(html).toContain(`<rect x="${-BLEED}" y="0" width="${BLEED}"`);
      expect(html).toContain(`<rect x="${STAGE_W}" y="0" width="${BLEED}"`);
    }
  });

  it('darkens to the house’s dark, from the room’s own edge value', () => {
    for (const html of [car, station]) {
      expect(html).toMatch(
        /<linearGradient id="stA-bdark"[^>]*gradientUnits="userSpaceOnUse"/,
      );
      expect(html).toContain('stop-color="#0c0a07" stop-opacity="1"');
      expect(html).toContain('fill="url(#stA-bdark)"');
    }
    // each starts from how dark the room already is at its edge
    expect(car).toContain('stop-opacity="0.95"');
    expect(station).toContain('stop-opacity="0.85"');
  });

  it('takes the hour’s tint on the car, none by day', () => {
    expect(car).toContain('mix-blend-mode:multiply');
    expect(bleed({ id: 'stA', room: 'car', phase: 'day' })).not.toContain('mix-blend-mode');
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
          // two heights (three with the slot open) for a full line, one row for a short one
          expect(new Set(R.photos.map((p) => p.row)).size).toBe(
            n <= 4 ? 1 : side && n === 8 ? 3 : 2,
          );
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
    expect(stationPlan('live').cx).toBe(844);
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
