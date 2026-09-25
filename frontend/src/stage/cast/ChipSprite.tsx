/**
 * A seat's chip: the character's head, cut from its base figure, as the wing's tiles and the
 * speech box's header show it. Just the picture; the numeral, the ring and any state are
 * drawn by whoever places it, never baked in.
 *
 * `unoptimized`: the sprites are already WebP at their final size, so re-encoding them through
 * the image optimiser would only add artefacts to the flat felt colours.
 */
import Image from 'next/image';
import { SPRITES, type Character } from '@/assets/manifest';

export function ChipSprite({
  character,
  className,
}: {
  character: Character;
  className?: string;
}) {
  return (
    <Image
      src={SPRITES.day[character].chip}
      alt=""
      unoptimized
      draggable={false}
      className={className}
      style={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }}
    />
  );
}
