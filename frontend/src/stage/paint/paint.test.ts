import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { BLEED, STAGE_W, type Hud } from '../units';
import { bleed } from './bleed';
import { diningCar, diningCarPlan } from './dining-car';
import { drape } from './drape';
import { light } from './light';
import { PHASES_IN_ORDER } from './materials';
import { shelfLight, shelfRoom } from './shelf-room';
import { shutter } from './window';

const HUDS: Hud[] = ['none', 'live', 'replay'];

const idsOf = (html: string) => [...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
const refsOf = (html: string) => [...html.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1]);

/** Every generator, at every option it takes, as (label, prefix → markup). */
const CASES: [string, (id: string) => string][] = [
  ...PHASES_IN_ORDER.flatMap((phase) =>
    HUDS.flatMap((hud) =>
      [false, true].flatMap((side) =>
        [true, false].map(
          (wallClock) =>
            [
              `diningCar ${phase} ${hud}${side ? ' side' : ''}${wallClock ? '' : ' no-clock'}`,
              (id: string) => diningCar({ id, phase, hud, side, wallClock }),
            ] as [string, (id: string) => string],
        ),
      ),
    ),
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
  ...HUDS.flatMap((hud) => [
    [`shelfRoom ${hud}`, (id: string) => shelfRoom({ id, hud })] as [
      string,
      (id: string) => string,
    ],
    [
      `shelfRoom ${hud} wood`,
      (id: string) => shelfRoom({ id, hud, wood: '/walnut.webp' }),
    ] as [string, (id: string) => string],
    [`shelfLight ${hud}`, (id: string) => shelfLight({ id, hud })] as [
      string,
      (id: string) => string,
    ],
    [`shelfLight ${hud} chosen`, (id: string) => shelfLight({ id, hud, chosen: 3 })] as [
      string,
      (id: string) => string,
    ],
  ]),
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
  ...PHASES_IN_ORDER.flatMap((phase) =>
    HUDS.map(
      (hud) =>
        [
          `bleed car ${phase} ${hud}`,
          (id: string) => bleed({ id, room: 'car', phase, hud }),
        ] as [string, (id: string) => string],
    ),
  ),
  ...HUDS.map(
    (hud) =>
      [`bleed shelf ${hud}`, (id: string) => bleed({ id, room: 'shelf', hud })] as [
        string,
        (id: string) => string,
      ],
  ),
  ['light bleed', (id: string) => light({ id, bleed: BLEED })],
  ['shelfLight bleed', (id: string) => shelfLight({ id, chosen: 2, bleed: BLEED })],
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
  // The kit is a plain script that declares one global; evaluate it and take that global.
  const Kit = new Function(`${src}; return StageKit;`)();

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
});

/* The bleed: two strips past the world's sides, darkening outwards to the house's dark. */
describe('bleed', () => {
  const car = bleed({ id: 'stA', room: 'car', phase: 'night', hud: 'live' });
  const shelf = bleed({ id: 'stA', room: 'shelf', hud: 'live' });

  it('draws both strips, outside the world and nowhere in it', () => {
    for (const html of [car, shelf]) {
      expect(html).toContain(`<rect x="${-BLEED}" y="0" width="${BLEED}"`);
      expect(html).toContain(`<rect x="${STAGE_W}" y="0" width="${BLEED}"`);
    }
  });

  it('darkens to the house’s dark, from the room’s own edge value', () => {
    for (const html of [car, shelf]) {
      expect(html).toMatch(
        /<linearGradient id="stA-bdark"[^>]*gradientUnits="userSpaceOnUse"/,
      );
      expect(html).toContain('stop-color="#0c0a07" stop-opacity="1"');
      expect(html).toContain('fill="url(#stA-bdark)"');
    }
    // the car fades its own ends to near-black, so its strips start there; the shelf does not
    expect(car).toContain('stop-opacity="0.95"');
    expect(shelf).toContain('stop-opacity="0"');
  });

  it('takes the hour’s tint on the car, none by day', () => {
    expect(car).toContain('mix-blend-mode:multiply');
    expect(bleed({ id: 'stA', room: 'car', phase: 'day' })).not.toContain('mix-blend-mode');
  });

  it('leaves the light and the drape as they were without it', () => {
    expect(light({ id: 'k', bleed: 0 })).toBe(light({ id: 'k' }));
    expect(drape({ id: 'k' })).toBe(drape());
    expect(shelfLight({ id: 'k', bleed: 0 })).toBe(shelfLight({ id: 'k' }));
  });
});
