/**
 * A seat's chip: the character's head portrait, framed so every face fills its circle at the
 * same size (`HEAD_FRAME`), as the wing's tiles and the speech box's header show it. Just the
 * picture; the numeral, the ring and any state are drawn by whoever places it, never baked in.
 *
 * The parent sets the size and clips the shape (a circle, a rounded tile). The portrait is sized
 * from the parent's height, so a tile taller than wide shows the circle's framing cut at the sides.
 *
 * `unoptimized`: the sprites are already WebP at their final size, so re-encoding them through
 * the image optimiser would only add artefacts.
 */
import Image from 'next/image';
import { HEAD_FRAME, SPRITES, type Character } from '@/assets/manifest';

export function ChipSprite({
  character,
  className,
}: {
  character: Character;
  className?: string;
}) {
  const { s, x, y } = HEAD_FRAME[character];
  return (
    <span
      className={className}
      style={{
        position: 'relative',
        display: 'block',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        borderRadius: 'inherit',
      }}
    >
      <Image
        src={SPRITES.day[character].head}
        alt=""
        unoptimized
        draggable={false}
        style={{
          position: 'absolute',
          maxWidth: 'none',
          height: `${s * 100}%`,
          width: 'auto',
          aspectRatio: '1',
          top: `${50 - s * 50 + y * 100}%`,
          left: '50%',
          // the element is s × the height wide, so x / s of it is x × the height
          transform: `translateX(${-50 + (x / s) * 100}%)`,
          borderRadius: 0,
        }}
      />
    </span>
  );
}

/** Where to draw the head portrait in an SVG, for a circle of diameter `d` centred on (cx, cy). */
export function headRect(character: Character, cx: number, cy: number, d: number) {
  const { s, x, y } = HEAD_FRAME[character];
  return {
    x: cx - (s * d) / 2 + x * d,
    y: cy - (s * d) / 2 + y * d,
    width: s * d,
    height: s * d,
  };
}
