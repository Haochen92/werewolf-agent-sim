/**
 * The role's kit, standing at the right end of the shelf: the healer's plasters, the
 * investigator's lens, the vigilante's popgun and caps, the wolves' mask and bone. It says
 * whose room this is at a glance, without a word. A picture only: it carries no state.
 *
 * Two kits hold a lit flame (the healer's candle, the investigator's oil lamp): the room's
 * candle light comes from there (`kitFlame`). The clock and the lamp are kits in the sprite set
 * too, but not a role's, and the room shows neither.
 */
import Image from 'next/image';
import { SPRITES, type KitName } from '@/assets/manifest';
import styles from './NightRoom.module.css';

export interface KitProps {
  /** The wire's role name; a role with no kit draws nothing. */
  role: string;
  /** Centre x and the shelf's top face the kit stands on, in units. */
  x: number;
  foot: number;
  /** Its height in units (the benches use 0.19 of the stage's height). */
  height: number;
}

const ROLE_KITS: readonly KitName[] = [
  'healer',
  'investigator',
  'vigilante',
  'serial_killer',
  'wolf',
  'villager',
];

/** The flame in a kit's picture, as fractions of its width and height (measured on the WebPs). */
const FLAME: Partial<Record<KitName, [number, number]>> = {
  healer: [0.851, 0.251],
  investigator: [0.855, 0.344],
};

/** A kit's width in units at this height; 0 for a role with no kit. */
export function kitWidth(role: string, height: number): number {
  if (!ROLE_KITS.includes(role as KitName)) return 0;
  const img = SPRITES.kits[role as KitName];
  return (height * img.width) / img.height;
}

/** Where the kit's own flame burns, in units; null when its picture holds none. */
export function kitFlame(role: string, x: number, foot: number, height: number) {
  const f = FLAME[role as KitName];
  if (!f) return null;
  const w = kitWidth(role, height);
  return { x: x - w / 2 + f[0] * w, y: foot - height + f[1] * height };
}

export function Kit({ role, x, foot, height }: KitProps) {
  if (!ROLE_KITS.includes(role as KitName)) return null;
  const img = SPRITES.kits[role as KitName];
  const w = kitWidth(role, height);
  return (
    <>
      {/* where it stands on the shelf: a soft contact shadow, a touch down and to the right */}
      <div
        className={styles.contact}
        style={{ left: x - w * 0.5 + 6, top: foot - 7, width: w, height: 14 }}
      />
      <div
        className={styles.kit}
        data-kit={role}
        style={{ left: x - w / 2, top: foot - height, width: w, height }}
      >
        <Image src={img} alt="" unoptimized priority draggable={false} />
      </div>
    </>
  );
}
