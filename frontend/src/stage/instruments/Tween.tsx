'use client';

/**
 * A group inside an SVG drawing that moves by a formula: the jar tipping over about its base,
 * the lid lifting and tilting on its string, a chip arcing out of the jar and turning over on
 * the way. These turn about a fixed point of the drawing, which an SVG `transform` attribute
 * says exactly; so rather than ask the animation library to guess an SVG's pivot, the group is
 * given a function from progress (0 → 1) to its transform and opacity, and the library only
 * runs the progress.
 *
 * Not played, the group sits at the end (progress 1): that is how every beat arrives at rest.
 */
import { animate, useMotionValue, useMotionValueEvent } from 'motion/react';
import { useEffect, useRef, type ReactNode } from 'react';
import { useMotionScale } from '../motion';

export type Ease =
  [number, number, number, number] | 'linear' | 'easeIn' | 'easeOut' | 'easeInOut';

export interface TweenProps {
  /** Play from 0; otherwise the group rests at 1. */
  play: boolean;
  duration: number;
  delay?: number;
  ease?: Ease;
  /** The group's transform at progress p. */
  transform?: (p: number) => string;
  /** The group's opacity at progress p. */
  opacity?: (p: number) => number;
  children?: ReactNode;
}

/** Linear interpolation, for the formulas. */
export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

export function Tween({
  play,
  duration,
  delay = 0,
  ease = 'easeInOut',
  transform,
  opacity,
  children,
}: TweenProps) {
  const k = useMotionScale();
  const p = useMotionValue(play ? 0 : 1);
  const ref = useRef<SVGGElement>(null);
  useMotionValueEvent(p, 'change', (v) => {
    const el = ref.current;
    if (!el) return;
    if (transform) el.setAttribute('transform', transform(v));
    if (opacity) el.style.opacity = String(opacity(v));
  });
  const easeKey = JSON.stringify(ease);
  useEffect(() => {
    if (!play) return;
    p.set(0);
    const run = animate(p, 1, {
      duration: duration * k,
      delay: delay * k,
      ease: JSON.parse(easeKey) as Ease,
    });
    return () => run.stop();
  }, [play, duration, delay, easeKey, k, p]);
  const now = p.get();
  return (
    <g
      ref={ref}
      transform={transform?.(now)}
      style={opacity ? { opacity: opacity(now) } : undefined}
    >
      {children}
    </g>
  );
}

/** The transform that turns and scales a group about the point (ox, oy), then moves it. */
export function about(
  ox: number,
  oy: number,
  o: { dx?: number; dy?: number; rot?: number; sx?: number; sy?: number },
): string {
  const { dx = 0, dy = 0, rot = 0, sx = 1, sy = sx } = o;
  return `translate(${dx + ox} ${dy + oy}) rotate(${rot}) scale(${sx} ${sy}) translate(${-ox} ${-oy})`;
}
