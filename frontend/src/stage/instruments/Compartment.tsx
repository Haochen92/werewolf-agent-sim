'use client';

/**
 * The night room's painting: the owner's sleeping compartment for the role, with the night
 * going by behind its cleared glass (the dining car's felt country and snow, FeltWindow).
 *
 * The painting cannot carry on past its own edges, so where the stage shows more (the bleed, or
 * the room slid left for the open side slot) its sides sink into the house's dark
 * (`PaintedBleed`), as the dining car's do. Still pictures only; the window's near row and snow
 * are the one thing that moves.
 */
import Image from 'next/image';
import { SPRITES, type RoomPicture } from '@/assets/manifest';
import { roomPlan } from '../paint/compartment';
import type { Hud } from '../units';
import { PaintedBleed } from './Bleed';
import { FeltWindow } from './FeltWindow';
import styles from './NightRoom.module.css';

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
      <PaintedBleed x={x} w={w} h={h} />
    </>
  );
}
