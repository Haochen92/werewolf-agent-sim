'use client';

/**
 * How fast the stage moves. Beats set how long things take; the viewer's speed control
 * scales all of it at once: normal as authored, fast at half the time (stage_architecture.md
 * §6). A component asks `useMotionScale()` for the factor and multiplies its durations and
 * delays by it, so no component carries its own speed logic.
 */
import { cubicBezier, easeIn, easeInOut, easeOut } from 'motion';
import { MotionConfig, type Transition } from 'motion/react';
import { createContext, useContext, type ReactNode } from 'react';
import type { MotionSpeed } from './scenes/types';
import { useSmall } from './set';

const SCALE: Record<MotionSpeed, number> = { normal: 1, fast: 0.5 };
const MotionScale = createContext(1);

export function StageMotion({
  speed,
  children,
}: {
  speed: MotionSpeed;
  children: ReactNode;
}) {
  // an unknown speed (an old 'skip' kept somewhere) moves at normal
  const k = SCALE[speed] ?? 1;
  return (
    <MotionScale.Provider value={k}>
      <MotionConfig reducedMotion="user">{children}</MotionConfig>
    </MotionScale.Provider>
  );
}

/** The factor every duration and delay is multiplied by: 1 or 0.5. */
export function useMotionScale(): number {
  return useContext(MotionScale);
}

/**
 * On a phone a move steps at film's rate. A figure, a chip or a card moving with no GPU layer
 * is repainted by the CPU on every frame, with the light's gradients under it, and at the
 * screen's rate that paint does not fit a frame: frames drop unevenly and the move reads as
 * stutter (build log §8.9). Sampled at 24 steps a second the same curve asks for a repaint
 * every 42 ms instead, on a steady beat, and the browser paints only when the value changes.
 */
const PHONE_FPS = 24;

type Easing = NonNullable<Transition['ease']>;
type EasingFn = (t: number) => number;

/* the curve as a function, for the eases the stage uses; anything else is left alone */
function easeFn(e: Easing | undefined): EasingFn | null {
  if (typeof e === 'function') return e;
  if (Array.isArray(e)) {
    const nums: number[] = [];
    for (const v of e as unknown[]) if (typeof v === 'number') nums.push(v);
    return nums.length === 4 && e.length === 4
      ? cubicBezier(nums[0], nums[1], nums[2], nums[3])
      : null;
  }
  switch (e) {
    case undefined:
    case 'easeOut':
      return easeOut;
    case 'easeIn':
      return easeIn;
    case 'easeInOut':
      return easeInOut;
    case 'linear':
      return (t) => t;
    default:
      return null;
  }
}

/** The transition with its curve sampled at `PHONE_FPS` over its duration: same start, end and shape. */
export function stepped<T extends { duration?: number; ease?: Transition['ease'] }>(
  t: T,
): T {
  const fn = easeFn(t.ease);
  if (!fn || !t.duration) return t;
  const n = Math.max(2, Math.round(t.duration * PHONE_FPS));
  return { ...t, ease: (p: number) => fn(Math.min(1, Math.floor(p * n + 1e-6) / n)) };
}

const asIs = <T,>(t: T) => t;

/**
 * How a mover's transition is given to motion: as written on a desktop, stepped on a phone
 * (`useSmall`). For moves only; a fade is the compositor's and needs no stepping.
 */
export function useSteps(): <T extends { duration?: number; ease?: Transition['ease'] }>(
  t: T,
) => T {
  return useSmall() ? stepped : asIs;
}
