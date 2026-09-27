'use client';

/**
 * The room carried on past the stage's sides, for a screen wider than 16:9 (see
 * paint/bleed.ts). A scene puts it first in its paint layer, under the room's own paint. It
 * never fades: at an hour change it takes the new hour at once, under the old hour's picture.
 * It wears the rooms' textures, as they do.
 */
import { Paint } from '../Stage';
import { bleed, type BleedOpts } from '../paint/bleed';
import { WOOD } from '../textures';

export function Bleed(props: Omit<BleedOpts, 'id' | 'wood'>) {
  return <Paint of={bleed} opts={{ ...props, wood: WOOD }} />;
}
