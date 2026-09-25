'use client';

/**
 * How fast the stage moves. Beats set how long things take; the viewer's speed control
 * scales all of it at once: normal as authored, fast at half the time, skip with no motion
 * at all (stage_architecture.md §6). A component asks `useMotionScale()` for the factor and
 * multiplies its durations and delays by it, so no component carries its own speed logic.
 */
import { MotionConfig } from 'motion/react';
import { createContext, useContext, type ReactNode } from 'react';
import type { MotionSpeed } from './scenes/types';

const SCALE: Record<MotionSpeed, number> = { normal: 1, fast: 0.5, skip: 0 };
const MotionScale = createContext(1);

export function StageMotion({
  speed,
  children,
}: {
  speed: MotionSpeed;
  children: ReactNode;
}) {
  const k = SCALE[speed];
  return (
    <MotionScale.Provider value={k}>
      <MotionConfig reducedMotion="user" transition={k === 0 ? { duration: 0 } : undefined}>
        {children}
      </MotionConfig>
    </MotionScale.Provider>
  );
}

/** The factor every duration and delay is multiplied by: 1, 0.5, or 0. */
export function useMotionScale(): number {
  return useContext(MotionScale);
}
