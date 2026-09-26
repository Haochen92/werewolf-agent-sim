'use client';

/**
 * The room carried on past the stage's sides, for a screen wider than 16:9 (see
 * paint/bleed.ts). A scene puts it first in its paint layer, under the room's own paint. It
 * never fades: at an hour change it takes the new hour at once, under the old hour's picture.
 */
import { Paint } from '../Stage';
import { bleed, type BleedOpts } from '../paint/bleed';

export function Bleed(props: Omit<BleedOpts, 'id'>) {
  return <Paint of={bleed} opts={props} />;
}
