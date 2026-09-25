import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import type { Hud } from '../units';
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
