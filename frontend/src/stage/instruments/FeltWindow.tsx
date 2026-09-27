'use client';

/**
 * The country behind the dining car's window: felt pictures, one pair per hour. The far sky and
 * hills stand still; the near row of pines, fence and pole scrolls left, one picture's width and
 * round again, so the train seems to roll on.
 *
 * It sits over the car's paint, exactly in the glass, so the brass frame still surrounds it, and
 * under everything after it in the paint layer: the shutter covers it when down and uncovers it
 * as it gathers up. At an hour change it crossfades with the car (`fade`, the same transition),
 * as pictures, never live SVG (stage_architecture.md §6). The car's paint fills the glass
 * with the hour's sky until the pictures load; the snow and the blind's pull are drawn on top.
 */
import Image from 'next/image';
import { motion, type Transition } from 'motion/react';
import { useLayoutEffect, useRef, type CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { CAR, type Phase } from '../paint/materials';
import { snowfall, windowRect } from '../paint/window';
import { geometry, STAGE_H, type Hud } from '../units';
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
}: {
  phase: Phase;
  /** Played: the hour the car was at before this beat; its pictures fade off over the new. */
  from?: Phase | null;
  /** The car's own crossfade, so the glass and the wall change hour together. */
  fade?: Transition;
  hud: Hud;
  /** The side slot is open: the window is further left (as for `CarPaint`). */
  side?: boolean;
}) {
  const [x, y, w, h] = windowRect(geometry(hud, side));
  // the paint's corner radius (window.ts `windowFrame`), so the frame's brass meets the felt
  const r = 0.04 * STAGE_H;
  const pull =
    `<path d="M${w / 2},-8 v16" stroke="#2a180c" stroke-width="2"/>` +
    `<circle cx="${w / 2}" cy="12" r="5" fill="none" stroke="${CAR.brass}" stroke-width="2"/>`;
  return (
    <div
      className={styles.glass}
      style={{ left: x, top: y, width: w, height: h, borderRadius: r }}
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
      <div className={styles.pane} />
      <svg
        className={styles.fill}
        viewBox={`0 0 ${w} ${h}`}
        dangerouslySetInnerHTML={{ __html: pull }}
      />
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
