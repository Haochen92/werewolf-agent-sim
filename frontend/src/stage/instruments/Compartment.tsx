'use client';

/**
 * The night room's painting: the owner's sleeping compartment for the role, with the night
 * going by behind its cleared glass (the dining car's felt country and snow, FeltWindow).
 *
 * The painting cannot carry on past its own edges, so where the stage shows more (the bleed, or
 * the room slid left for the open side slot) its last stretch is mirrored and sinks into the
 * house's dark, as the other rooms' bleed does. Still pictures only; the window's near row and
 * snow are the one thing that moves.
 */
import Image from 'next/image';
import type { CSSProperties } from 'react';
import { SPRITES, type RoomPicture } from '@/assets/manifest';
import { roomPlan } from '../paint/compartment';
import { BLEED, STAGE_W, type Hud } from '../units';
import { FeltWindow } from './FeltWindow';
import styles from './NightRoom.module.css';

/** The house's dark the edges sink into, and how dark the mirrored stretch is where it starts. */
const HOUSE = '12,10,7';
const EDGE = 0.45;
/** How far out the mirrored stretch reaches the house's full dark, in units. */
const DARK_AT = 170;

/** The red of the wolves' lamp on their glass, so the night outside sits in their light. */
const WOLF_GLASS = 'rgba(150, 24, 16, 0.28)';

export function Compartment({
  room,
  hud,
  side = false,
}: {
  room: RoomPicture;
  hud: Hud;
  side?: boolean;
}) {
  const P = roomPlan({ room, hud, side });
  const { x, w, h } = P.picture;
  const g = P.glass;
  const img = SPRITES.rooms[room];
  // the mirrored strip each side, and the dark past it to the bleed's end
  const strip = (at: 'left' | 'right'): CSSProperties => ({
    left: at === 'left' ? x - BLEED : x + w,
    width: BLEED,
    height: h,
  });
  const fade = (at: 'left' | 'right') =>
    `linear-gradient(to ${at}, rgba(${HOUSE},${EDGE}), rgba(${HOUSE},1) ${(DARK_AT / BLEED) * 100}%)`;
  const leftEnd = x - BLEED,
    rightEnd = x + w + BLEED;
  return (
    <>
      <FeltWindow
        phase="night"
        hud={hud}
        rect={[g.x, g.y, g.w, g.h]}
        radius={g.r}
        tint={room === 'wolf' ? WOLF_GLASS : undefined}
      />
      <div
        className={styles.room}
        data-room={room}
        style={{ left: x, width: w, height: h }}
      >
        <Image src={img} alt="" unoptimized priority draggable={false} />
      </div>
      {(['left', 'right'] as const).map((at) => (
        <div key={at} className={styles.mirror} style={strip(at)} aria-hidden="true">
          <Image
            src={img}
            alt=""
            unoptimized
            draggable={false}
            style={{ left: at === 'left' ? BLEED - w : 0, width: w, height: h }}
          />
          <i style={{ background: fade(at) }} />
        </div>
      ))}
      {/* past the mirrored stretch, to the far edge of the bleed: the house's dark */}
      {leftEnd > -BLEED ? (
        <div
          className={styles.house}
          style={{ left: -BLEED, width: leftEnd + BLEED, height: h }}
        />
      ) : null}
      {rightEnd < STAGE_W + BLEED ? (
        <div
          className={styles.house}
          style={{ left: rightEnd, width: STAGE_W + BLEED - rightEnd, height: h }}
        />
      ) : null}
    </>
  );
}
