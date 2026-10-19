'use client';

/**
 * The dining car's painting at an hour: the owner's room at that hour, the country painted in
 * its glass.
 *
 * It sits where the car's plan puts it (`diningCarPlan().picture`): across with the puppet's
 * centre line and up or down with the rail, so its window and floor land on the stage's. In
 * the replay's layout, where the rail is higher, the picture's own last rows of floor are laid
 * again under its foot, so the floor still reaches the frame's edge. A scene fades one hour's
 * backdrop off over the next (CarPaint): a still picture and a flat colour, so it fades as a
 * bitmap (stage_architecture.md §6).
 */
import Image from 'next/image';
import { SPRITES } from '@/assets/manifest';
import { diningCarPlan } from '../paint/dining-car';
import type { Phase } from '../paint/materials';
import { STAGE_H, STAGE_W, type Hud } from '../units';

export function CarBackdrop({
  phase,
  hud,
  side = false,
}: {
  phase: Phase;
  hud: Hud;
  /** The side slot is open: the room is further left. */
  side?: boolean;
}) {
  const { x, y } = diningCarPlan({ phase, hud, side }).picture;
  const img = SPRITES.car[phase];
  const box = { position: 'absolute', top: 0, width: STAGE_W, height: STAGE_H } as const;
  return (
    <div data-car={phase} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {y < 0 ? (
        // under the foot of a raised picture: its own last rows again, down to the frame's edge
        <div style={{ ...box, left: x, top: STAGE_H + y, height: -y, overflow: 'hidden' }}>
          <Image
            decoding="sync"
            src={img}
            alt=""
            unoptimized
            draggable={false}
            style={{ ...box, top: -(STAGE_H + y) }}
          />
        </div>
      ) : null}
      <Image
        decoding="sync"
        src={img}
        alt=""
        unoptimized
        priority
        draggable={false}
        style={{ ...box, left: x, top: y }}
      />
    </div>
  );
}
