'use client';

/**
 * The atmosphere: what makes the rooms read as one small set lit by one lamp and filmed, the
 * puppets' own light (warm, from the upper left) carried over the whole room.
 *
 * Two parts, in two layers (Stage.tsx):
 * - the haze, over the room's paint and under everything standing in front of it: the key
 *   light warming the upper left of the wall, the shadows the wall pieces cast (the car's), and
 *   a faint warm veil that sets the back of the room back (clear round a lit lamp), so the
 *   stand, the table and the figures are what the eye lands on;
 * - the grade, over the whole picture and under the HUD: the key light falling off towards the
 *   lower right, a soft vignette, and a fine grain. It sits outside the camera's box, as a
 *   lens's would, so the count's push-in moves the room under it.
 *
 * Every piece is still: plain gradients, a static SVG (its blur rasterised once, as the car's
 * own cut-out shadows are) and a tiled picture, drawn with normal alpha, no blend mode and no
 * CSS filter (stage_architecture.md §6). A scene puts one in; the platform has none.
 */
import type { CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { Layer, Paint } from './Stage';
import { KEY, carHaze } from './paint/atmosphere';
import type { Phase } from './paint/materials';
import { geometry, type Hud } from './units';
import styles from './Atmosphere.module.css';

export function Atmosphere({
  room,
  phase,
  hud,
  side = false,
}: {
  /** The dining car (its wall pieces cast shadows) or a seat's shelf room at night. */
  room: 'car' | 'shelf';
  /** The room's hour: the key light is strongest by day and all but out at night. */
  phase: Phase;
  hud: Hud;
  /** The side slot is open: the car's pieces are further left. */
  side?: boolean;
}) {
  // the grade's vignette centres on the room the puppet stands in (narrower with the slot open)
  const g = geometry(hud, side);
  return (
    <>
      <Layer name="haze">
        {/* the seat's room at night is lit by its candle alone (shelfLight), not the key */}
        {room === 'car' ? (
          <div className={styles.key} style={{ opacity: KEY[phase] }} />
        ) : null}
        {room === 'car' ? (
          <Paint of={carHaze} opts={{ phase, hud, side }} />
        ) : (
          <div className={styles.veil} />
        )}
      </Layer>
      <Layer name="grade">
        <div
          className={styles.grade}
          style={
            {
              '--grain': `url(${SPRITES.grain.src})`,
              '--cx': `${g.cx}px`,
              '--room': `${g.room}px`,
            } as CSSProperties
          }
        />
      </Layer>
    </>
  );
}
