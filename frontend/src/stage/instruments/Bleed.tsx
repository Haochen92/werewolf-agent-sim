'use client';

/**
 * The room carried on past the stage's sides, for a screen wider than 16:9 (see
 * paint/bleed.ts): the waiting room's platform. A scene puts it first in its paint layer,
 * under the room's own paint.
 *
 * The painted rooms (the dining car, the night compartments) cannot carry on past their own
 * edges, so they sink into the house's dark there instead (`PaintedBleed`).
 */
import { Paint } from '../Stage';
import { bleed, type BleedOpts } from '../paint/bleed';
import { BLEED, STAGE_W } from '../units';

export function Bleed(props: Omit<BleedOpts, 'id'>) {
  return <Paint of={bleed} opts={props} />;
}

/** The house's dark, as `r,g,b` (the stage's own background). */
const HOUSE = '12,10,7';
/** How far in from its edge a painting starts to sink, and how dark it is at the edge. */
const SINK = { inner: 28, edge: 0.6 };
/** Past the edge: how dark the dark starts, and how far out it is the house's full dark. */
const DARK = { from: 0.82, at: 90 };

/**
 * A painting's sides sinking into the house's dark: its last stretch darkens towards its edge,
 * and past the edge the dark carries on, to the far end of the bleed. Plain gradients over the
 * picture, so nothing is mirrored and nothing fades or moves. `x`, `w`: the painting's box.
 * `outside`: the stretch that sinks stops at the world's side, so nothing inside the 16:9 frame
 * is dimmed (the car's table lamps stand at its edges); a painting that ends at the world's side
 * meets the dark there.
 */
export function PaintedBleed({
  x,
  w,
  h = 900,
  outside = false,
}: {
  x: number;
  w: number;
  h?: number;
  outside?: boolean;
}) {
  const side = (at: 'left' | 'right') => {
    const edge = at === 'left' ? x : x + w;
    // the sinking stretch: its last SINK.inner units, or only what of it lies past the world
    const inner = outside
      ? Math.max(0, Math.min(SINK.inner, at === 'left' ? -edge : edge - STAGE_W))
      : SINK.inner;
    const outer =
      at === 'left'
        ? { left: -BLEED, width: Math.max(0, edge + BLEED) }
        : { left: edge, width: Math.max(0, STAGE_W + BLEED - edge) };
    const away = at === 'left' ? 'left' : 'right';
    return (
      <div key={at} aria-hidden="true">
        {inner > 0 ? (
          <div
            style={{
              position: 'absolute',
              top: 0,
              height: h,
              left: at === 'left' ? edge : edge - inner,
              width: inner,
              pointerEvents: 'none',
              background: `linear-gradient(to ${away}, rgba(${HOUSE},0), rgba(${HOUSE},${SINK.edge}))`,
            }}
          />
        ) : null}
        <div
          style={{
            position: 'absolute',
            top: 0,
            height: h,
            ...outer,
            pointerEvents: 'none',
            background: `linear-gradient(to ${away}, rgba(${HOUSE},${DARK.from}), rgba(${HOUSE},1) ${DARK.at}px)`,
          }}
        />
      </div>
    );
  };
  return (
    <>
      {side('left')}
      {side('right')}
    </>
  );
}
