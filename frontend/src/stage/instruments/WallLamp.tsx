'use client';

/**
 * The dining car's wall lamp, at the right: the owner's painted brass lantern on its curled iron
 * bracket (SPRITES.props.wallLampUnlit / wallLampLit), unlit by day and dawn, its candle burning
 * at dusk and night (the hour's `lit`). Where a beat plays the hour's change, the two pictures
 * crossfade with the car's own fade, as pictures (stage_architecture.md §6).
 *
 * It hangs where the car's plan says (`diningCarPlan().lamp`): its glass centred on the kit's
 * lantern glass, so the car's glow, halo and pool (still code, in the car's paint and the house
 * lights) stay round it. The room's tint falls on the iron and the brass; lit, less of it, and
 * none on the glowing glass. Its shadow is thrown on the wall behind (the rooms' atmosphere).
 */
import { motion, type Transition } from 'motion/react';
import { SPRITES } from '@/assets/manifest';
import { PHASES, ROOMLIGHT, type Phase } from '../paint/materials';

/**
 * The pictures (493×763, one framing for both) in their own pixels: the glass's box, the four
 * panes the candle lights.
 */
const LAMP_PX = { x0: 187.5, x1: 462.5, y0: 365, y1: 632.5 };
/** The glass's height in units: a little taller than the kit's lantern box (0.075 H), for its build. */
const GLASS_H = 78;

/** Its shadow on the wall, thrown by the key light: how far it falls and how dark. */
const SHADOW = { dx: 26, dy: 22, a: 0.5 };

export function WallLamp({
  x,
  y,
  phase,
  from = null,
  fade,
}: {
  /** The glass's centre, from the car's plan. */
  x: number;
  y: number;
  phase: Phase;
  /** Played: the hour the car was at before this beat; its lamp fades off over the new. */
  from?: Phase | null;
  fade?: Transition;
}) {
  const src = (p: Phase) =>
    (PHASES[p].lit ? SPRITES.props.wallLampLit : SPRITES.props.wallLampUnlit).src;
  const img = SPRITES.props.wallLampUnlit,
    kp = GLASS_H / (LAMP_PX.y1 - LAMP_PX.y0),
    iw = img.width * kp,
    ih = img.height * kp;
  const sh = SPRITES.shadow.wall.lamp,
    su = ih / 128;
  const on = PHASES[phase].lit,
    tint = ROOMLIGHT[phase];
  const fill = { position: 'absolute', inset: 0, width: '100%', height: '100%' } as const;
  // the glass's box as a fraction of the picture: a lit lamp's tint keeps off it
  const g = {
    l: (LAMP_PX.x0 / img.width) * 100,
    r: (LAMP_PX.x1 / img.width) * 100,
    t: (LAMP_PX.y0 / img.height) * 100,
    b: (LAMP_PX.y1 / img.height) * 100,
  };
  return (
    <div
      aria-hidden="true"
      data-wall-lamp={on ? 'lit' : 'unlit'}
      style={{
        position: 'absolute',
        left: x - ((LAMP_PX.x0 + LAMP_PX.x1) / 2) * kp,
        top: y - ((LAMP_PX.y0 + LAMP_PX.y1) / 2) * kp,
        width: iw,
        height: ih,
      }}
    >
      {/* eslint-disable @next/next/no-img-element -- still pictures laid in units, never optimised */}
      <img
        src={sh.src}
        alt=""
        draggable={false}
        style={{
          position: 'absolute',
          left: (iw - sh.width * su) / 2 + SHADOW.dx,
          top: -12 * su + SHADOW.dy,
          width: sh.width * su,
          height: sh.height * su,
          maxWidth: 'none',
          opacity: SHADOW.a,
        }}
      />
      <img src={src(phase)} alt="" draggable={false} style={fill} />
      {from && PHASES[from].lit !== on ? (
        <motion.img
          src={src(from)}
          alt=""
          draggable={false}
          style={fill}
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={fade}
        />
      ) : null}
      {/* eslint-enable @next/next/no-img-element */}
      {tint.tint ? (
        // the room's tint on the iron and brass, in the lamp's own shape; still, never fading
        <div
          style={{
            ...fill,
            background: tint.tint,
            opacity: on ? tint.a * 0.6 : tint.a,
            maskImage: `url(${src(phase)})`,
            maskSize: '100% 100%',
            clipPath: on
              ? `polygon(evenodd, 0 0, 100% 0, 100% 100%, 0 100%, 0 0, ${g.l}% ${g.t}%, ${g.l}% ${g.b}%, ${g.r}% ${g.b}%, ${g.r}% ${g.t}%, ${g.l}% ${g.t}%)`
              : undefined,
          }}
        />
      ) : null}
    </div>
  );
}
