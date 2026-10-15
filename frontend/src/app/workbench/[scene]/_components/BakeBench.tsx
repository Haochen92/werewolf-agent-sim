'use client';

/**
 * The bake bench (`/workbench/bake?phase=day&hud=live&side=0`): the car's set with nothing in
 * front of it, drawn at scale 1 with the whole bleed showing, for `scripts/bake-sets.mjs` to
 * photograph. The picture it saves is what `instruments/Backdrop.tsx` then shows in place of the
 * live paint and haze: the same drawing, flattened to one bitmap (build log §8.3).
 *
 * No control strip, no HUD, no frame: the page is exactly 2200×900 css px (the world and 300
 * of bleed each side), so a screenshot of the viewport at a device scale is the file.
 */
import { CarHaze } from '@/stage/Atmosphere';
import { Layer, Stage } from '@/stage/Stage';
import { PHASES_IN_ORDER, type Phase } from '@/stage/paint/materials';
import { CarPaint } from '@/stage/scenes/DiningCarParts';
import { BLEED, STAGE_H, STAGE_W, type Hud } from '@/stage/units';
import styles from './BakeBench.module.css';

const pick = <T extends string>(v: string | null, all: readonly T[], dflt: T): T =>
  all.includes(v as T) ? (v as T) : dflt;

export function BakeBench({ params }: { params: URLSearchParams }) {
  const phase = pick<Phase>(params.get('phase'), PHASES_IN_ORDER, 'day');
  const hud = pick<Hud>(params.get('hud'), ['live', 'replay'], 'live');
  const side = params.get('side') === '1';
  return (
    <div
      data-bake={`car-${phase}-${hud}-${side ? 'side' : 'full'}`}
      className={styles.sheet}
      style={{ width: STAGE_W + 2 * BLEED, height: STAGE_H }}
    >
      <div className={styles.world} style={{ left: BLEED, width: STAGE_W }}>
        <Stage fit="width" className={styles.open}>
          <Layer name="paint">
            <CarPaint phase={phase} hud={hud} side={side} />
          </Layer>
          <Layer name="haze">
            <CarHaze phase={phase} hud={hud} side={side} />
          </Layer>
        </Stage>
      </div>
    </div>
  );
}
