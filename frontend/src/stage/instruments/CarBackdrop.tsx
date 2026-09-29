'use client';

/**
 * The dining car's painting at an hour: the day picture by day and at dawn, the same picture
 * under the hour's warm tint at dusk, and the night picture (the day's, relit) at night. Its
 * glass is clear, so the felt country (FeltWindow) shows through it.
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

/**
 * The hour's tint over the painting: the dusk's warm fall of light (materials.ts `ROOMLIGHT`,
 * #c0703a multiplied at 0.24), as a flat warm dark laid at normal alpha, since a fading
 * backdrop carries no blend mode. Night has its own picture, day and dawn none.
 */
export const CAR_TINT: Partial<Record<Phase, string>> = { dusk: 'rgba(78, 24, 4, 0.2)' };

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
  const img = SPRITES.car[phase === 'night' ? 'night' : 'day'];
  const tint = CAR_TINT[phase];
  const box = { position: 'absolute', top: 0, width: STAGE_W, height: STAGE_H } as const;
  return (
    <div data-car={phase} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      {y < 0 ? (
        // under the foot of a raised picture: its own last rows again, down to the frame's edge
        <div style={{ ...box, left: x, top: STAGE_H + y, height: -y, overflow: 'hidden' }}>
          <Image
            src={img}
            alt=""
            unoptimized
            draggable={false}
            style={{ ...box, top: -(STAGE_H + y) }}
          />
        </div>
      ) : null}
      <Image
        src={img}
        alt=""
        unoptimized
        priority
        draggable={false}
        style={{ ...box, left: x, top: y }}
      />
      {tint ? (
        <div style={{ ...box, left: x, top: 0, height: STAGE_H, background: tint }} />
      ) : null}
    </div>
  );
}
