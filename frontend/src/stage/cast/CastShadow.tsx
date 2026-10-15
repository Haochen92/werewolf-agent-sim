/**
 * A figure's shadow on the wall behind it (the rooms' atmosphere, Atmosphere.tsx): its
 * silhouette baked small and soft (SPRITES.shadow: 128 px tall with a 12 px margin), laid
 * down and to the right of the figure as the key light from the upper left throws it.
 *
 * A still picture inside the figure's own box, so it rises, hangs and fades with the figure
 * and nothing is blurred live. Drawn as an SVG image, not an <img>, so the figure's picture
 * stays the one image in its box.
 */
import type { StaticImageData } from 'next/image';
import { windowRect } from '../paint/window';
import { STAGE_H, type StageGeometry } from '../units';

/** The baked silhouette's height and margin, in its own pixels (manifest.ts). */
const PX = 128,
  MARGIN = 12;

export function CastShadow({
  src,
  w,
  h,
  dx,
  dy,
  opacity,
}: {
  src: StaticImageData;
  /** The figure's box, in units. */
  w: number;
  h: number;
  /** How far the shadow falls, as fractions of the figure's height. */
  dx: number;
  dy: number;
  opacity: number;
}) {
  const u = h / PX,
    sw = src.width * u;
  return (
    <svg
      aria-hidden="true"
      style={{
        position: 'absolute',
        left: (w - sw) / 2 + dx * h,
        top: -MARGIN * u + dy * h,
        width: sw,
        height: src.height * u,
        opacity,
        overflow: 'visible',
        pointerEvents: 'none',
      }}
    >
      <image href={src.src} width="100%" height="100%" preserveAspectRatio="none" />
    </svg>
  );
}

/**
 * A clip that keeps a shadow off the car's window glass (a view through glass takes no shadow):
 * everything but the glass's rounded rect, as FeltWindow draws it, in world units.
 */
export function offGlass(g: StageGeometry): string {
  const [x, y, w, h] = windowRect(g),
    r = 0.04 * STAGE_H,
    a = `A${r},${r} 0 0 1`;
  const glass = `M${x + r},${y} H${x + w - r} ${a} ${x + w},${y + r} V${y + h - r} ${a} ${x + w - r},${y + h} H${x + r} ${a} ${x},${y + h - r} V${y + r} ${a} ${x + r},${y}Z`;
  return `path(evenodd, 'M-4000,-4000 H6000 V6000 H-4000Z ${glass}')`;
}
