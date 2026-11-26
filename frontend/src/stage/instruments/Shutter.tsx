'use client';

/**
 * The window's shutter, moving: a felt roller blind (a painted raster, `SPRITES.props.shutter`;
 * the felt set of 2026-10-17) that comes down out of the walnut pelmet over the glass, its hem
 * rod and pull ring on the frame's foot, or rolls back up into it. It drops at the vote and at the morning's
 * report, and gathers up when night falls and when the day begins (handoff §2).
 *
 * At rest it draws exactly what the paint's `shutter()` draws (the same markup, from
 * `shutterParts`), so a scene that mounts this instrument leaves the paint's shutter out. When
 * played, the panel slides from under the pelmet (its box is clipped there, so it comes from
 * behind it and goes back behind it) and the rolled-up stack under the pelmet fades out as the
 * panel leaves it, or in as it returns. The panel is an HTML box of its own (its slide a CSS
 * transform; the stack and the pelmet stay in the drawing above it). Timings from benches 67 and 75: down 1.1 s after 0.35 s;
 * up 1.2 s after `delay`.
 */
import { motion } from 'motion/react';
import type { CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { usePaintId } from '../Stage';
import { useMotionScale, useSteps } from '../motion';
import { shutterGeometry, shutterParts, type ShutterState } from '../paint/window';
import { WOOD } from '../textures';
import { STAGE_H, STAGE_W, type StageGeometry } from '../units';

export interface ShutterProps {
  g: StageGeometry;
  /** Where the shutter ends up. */
  state: ShutterState;
  /** Play the move into `state` from the other one. */
  animate?: boolean;
  /** Seconds before the move starts (default: the bench's 0.35 down, 1.4 up). */
  delay?: number;
}

export function Shutter({ g, state, animate = false, delay }: ShutterProps) {
  const k = useMotionScale();
  const step = useSteps();
  const id = usePaintId();
  const { clip, panel, stack, pelmet } = shutterParts(
    g,
    id,
    WOOD.walnut,
    SPRITES.props.shutter.src,
  );
  const closed = state === 'closed';
  const d = delay ?? (closed ? 0.35 : 1.4);
  const html = (s: string) => ({ dangerouslySetInnerHTML: { __html: s } });
  const full: CSSProperties = {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    overflow: 'visible',
  };
  // the panel's own box: the clip's rectangle, under the pelmet (window.ts `shutterGeometry`);
  // raised, the whole picture (the ring's foot too) goes up past its top
  const { box, picture } = shutterGeometry(g);
  const up = -(picture.y + picture.h - box.y + 4);
  return (
    <>
      {/* the panel rides an HTML box clipped under the pelmet, so its slide is a CSS transform
          on one finished picture, not an SVG move relaid out every frame (build log §8.4) */}
      <div
        style={{
          position: 'absolute',
          left: box.x,
          top: box.y,
          width: box.w,
          height: box.h,
          overflow: 'hidden',
        }}
        aria-hidden="true"
      >
        <motion.div
          data-moves=""
          style={{ position: 'absolute', inset: 0 }}
          initial={animate ? { y: closed ? up : 0 } : false}
          animate={{ y: closed ? 0 : up }}
          // not played: at rest in its state at once, also when the state changes under a
          // mounted shutter (the set stays up across a scene's beats)
          transition={
            !animate
              ? { duration: 0 }
              : closed
                ? step({ duration: 1.1 * k, delay: d * k, ease: [0.4, 0.7, 0.4, 1] })
                : step({ duration: 1.2 * k, delay: d * k, ease: [0.4, 0.2, 0.4, 1] })
          }
        >
          <svg
            viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`}
            style={full}
            aria-hidden="true"
            {...html(panel)}
          />
        </motion.div>
      </div>
      <svg viewBox={`0 0 ${STAGE_W} ${STAGE_H}`} style={full} aria-hidden="true">
        <defs {...html(clip)} />
        <motion.g
          {...html(stack)}
          initial={animate ? { opacity: closed ? 1 : 0 } : false}
          animate={{ opacity: closed ? 0 : 1 }}
          transition={
            !animate
              ? { duration: 0 }
              : {
                  duration: 0.3 * k,
                  delay: (closed ? d + 0.05 : d + 1.0) * k,
                  ease: 'linear',
                }
          }
        />
        <g {...html(pelmet)} />
      </svg>
    </>
  );
}
