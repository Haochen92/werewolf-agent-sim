'use client';

/**
 * The country behind the dining car's window: felt pictures, one pair per hour. The far sky and
 * hills stand still; the near row of pines, fence and pole scrolls left, one picture's width and
 * round again, so the train seems to roll on.
 *
 * It sits in the car painting's cleared glass (`diningCarPlan().glass`), so the painted brass
 * frame surrounds it, and under everything after it in the paint layer: the shutter covers it
 * when down and uncovers it as it gathers up. At an hour change it crossfades with the car
 * (`fade`, the same transition), as pictures, never live SVG (stage_architecture.md §6). The
 * glass holds the hour's sky until the pictures load; the snow is drawn on top.
 *
 * The night rooms reuse it behind their paintings' cleared glass (`rect`, `radius`): the same
 * night, and in the wolves' red-lit room a `tint` of their light on the glass.
 */
import Image from 'next/image';
import { motion, type Transition } from 'motion/react';
import { useLayoutEffect, useRef, type CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { diningCarPlan } from '../paint/dining-car';
import { PHASES, type Phase } from '../paint/materials';
import { snowfall } from '../paint/window';
import type { Hud } from '../units';
import styles from './FeltWindow.module.css';

/** How much of the glass's height the near row fills: tree tops just above the middle. */
const NEAR = 0.52;
/** The near picture's width over its height (1536×520). */
const NEAR_ASPECT = 1536 / 520;
/** Units a second the near row moves: the old vector tree line's pace (120 units in 5 s). */
const SPEED = 24;

export function FeltWindow({
  phase,
  from,
  fade,
  hud,
  side = false,
  rect,
  radius,
  tint,
}: {
  phase: Phase;
  /** Played: the hour the car was at before this beat; its pictures fade off over the new. */
  from?: Phase | null;
  /** The car's own crossfade, so the glass and the wall change hour together. */
  fade?: Transition;
  hud: Hud;
  /** The side slot is open: the car's window is further left (as for `CarPaint`). */
  side?: boolean;
  /** The glass as [x, y, w, h] in units, when it is not the car's window (a night room's). */
  rect?: readonly [number, number, number, number];
  /** Its corner radius in units, with `rect`. */
  radius?: number;
  /** A colour laid over the glass, the room's own light on it (a CSS colour with alpha). */
  tint?: string;
}) {
  // the car's painted glass, unless a room gives its own
  const car = rect ? null : diningCarPlan({ phase, hud, side }).glass;
  const [x, y, w, h] = rect ?? [car!.x, car!.y, car!.w, car!.h];
  const r = radius ?? car!.r;
  return (
    <div
      className={styles.glass}
      style={{
        left: x,
        top: y,
        width: w,
        height: h,
        borderRadius: r,
        background: PHASES[phase].skyTop,
      }}
      data-felt-window={phase}
    >
      <Country hour={phase} w={w} h={h} />
      {from && from !== phase ? (
        <motion.div
          className={styles.fill}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={fade}
        >
          <Country hour={from} w={w} h={h} />
        </motion.div>
      ) : null}
      <svg
        className={styles.fill}
        viewBox={`0 0 ${w} ${h}`}
        suppressHydrationWarning
        dangerouslySetInnerHTML={{ __html: snowfall(0, 0, w, h, 1) }}
      />
      {tint ? <div className={styles.fill} style={{ background: tint }} /> : null}
      <div className={styles.pane} />
    </div>
  );
}

/** One hour's country: the far picture standing still, the near row scrolling over it. */
function Country({ hour, w, h }: { hour: Phase; w: number; h: number }) {
  const strip = useRef<HTMLDivElement>(null);
  const sh = h * NEAR,
    tile = sh * NEAR_ASPECT,
    dur = tile / SPEED;
  useLayoutEffect(() => {
    // keyed to the page's clock, so an hour's crossfade starts both rows at the same place
    const el = strip.current;
    if (el) el.style.animationDelay = `${-((performance.now() / 1000) % dur)}s`;
  }, [dur]);
  return (
    <>
      <Image
        decoding="sync"
        src={SPRITES.window[hour].far}
        alt=""
        unoptimized
        draggable={false}
        className={styles.far}
      />
      <div
        ref={strip}
        className={styles.near}
        style={
          {
            width: w + tile,
            height: sh,
            backgroundImage: `url(${SPRITES.window[hour].near.src})`,
            backgroundSize: `${tile}px ${sh}px`,
            animationDuration: `${dur}s`,
            '--tile': `${tile}px`,
          } as CSSProperties
        }
      />
    </>
  );
}
