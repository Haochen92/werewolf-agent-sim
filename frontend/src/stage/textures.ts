/**
 * The room's surface pictures by URL, for the paints and the floor that fill their shapes with
 * them (paint/texture.ts; stage_architecture.md §4).
 */
import { SPRITES } from '@/assets/manifest';
import type { Wood } from './paint/texture';

export const WOOD: Wood = {
  walnut: SPRITES.textures.walnut.src,
  boards: SPRITES.textures.boards.src,
};

export const VELVET: string = SPRITES.textures.velvet.src;
