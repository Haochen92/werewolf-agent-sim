/**
 * The role's kit, standing at the right end of the shelf: the healer's plasters, the
 * investigator's lens, the vigilante's popgun and caps, the wolves' mask and bone. It says
 * whose room this is at a glance, without a word. A picture only: it carries no state.
 *
 * The carriage clock and the lamp are kits in the sprite set too, but they are not a role's:
 * the clock on the shelf is drawn in vector (CarriageClock), because its hand shows state.
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

export function Kit({ role, x, foot, height }: KitProps) {
  if (!ROLE_KITS.includes(role as KitName)) return null;
  const img = SPRITES.kits[role as KitName];
  const w = (height * img.width) / img.height;
  return (
    <div
      className={styles.kit}
      data-kit={role}
      style={{ left: x - w / 2, top: foot - height, width: w, height }}
    >
      <Image src={img} alt="" unoptimized priority draggable={false} />
    </div>
  );
}
