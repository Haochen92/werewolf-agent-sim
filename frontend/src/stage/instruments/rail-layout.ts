/**
 * How the seat rail lays its cards out, from the number of seats (the table's size is not
 * fixed at nine, so nothing here assumes it).
 *
 * Two columns, as many rows as the seats need, the cards as tall as the rail's height allows.
 * The suspect slot takes the grid's spare cell when there is one (an odd count), and becomes a
 * strip across the foot when there is none (an even count). A table that would need more than
 * six rows gets a third column, and the rail wants to be wider for it.
 *
 * The rail is `WING_N` wide inside the world on every screen (the room is laid out around it);
 * where a screen wider than 16:9 shows the bleed beside the world, the rail grows out into it
 * up to `reach` (a phone held sideways), so its cards come out nearer the shape of a print.
 */
import { STAGE_H, WING_N } from '../units';

/** The rail's inner padding (its walnut frame and a margin of cork) and the gap between
 * cards (room for the tacks), in units. */
export const RAIL_PAD = 14;
export const RAIL_GAP = 10;
/** The most rows before a third column. */
export const RAIL_MAX_ROWS = 6;
/** The suspect strip's height, when the count is even. */
export const RAIL_STRIP = 64;
/** A card's width where the rail can grow into the bleed (about 58 css px on an iPhone 14). */
export const RAIL_CARD_W = 136;

export type SuspectPlace =
  { kind: 'cell'; row: number; col: number } | { kind: 'strip' } | null;

export interface RailLayout {
  /** Seats. */
  n: number;
  cols: number;
  /** Rows of cards (the strip, if any, is under them). */
  rows: number;
  /** Where the suspect slot goes (null: no slot, for a viewer who keeps no notes). */
  suspect: SuspectPlace;
  /** A card's height, in units: the rows fill the rail's height. */
  cardH: number;
  /** The rail's width inside the world, and the card width that gives. */
  width: number;
  cardW: number;
  /** The widest the rail grows into a wide screen's bleed, and the card width there. */
  target: number;
  targetCardW: number;
  /** How far past the world's left edge the rail may reach, at most (target − width). */
  reach: number;
}

export function railLayout(
  n: number,
  { suspect = true, height = STAGE_H, width = WING_N } = {},
): RailLayout {
  const cols = Math.max(2, Math.ceil(n / RAIL_MAX_ROWS));
  const rows = Math.max(1, Math.ceil(n / cols));
  const spare = rows * cols - n;
  const place: SuspectPlace = !suspect
    ? null
    : spare > 0
      ? { kind: 'cell', row: Math.floor(n / cols), col: n % cols }
      : { kind: 'strip' };
  const strip = place?.kind === 'strip' ? RAIL_STRIP + RAIL_GAP : 0;
  const cardH = (height - 2 * RAIL_PAD - strip - (rows - 1) * RAIL_GAP) / rows;
  const across = (w: number) => (w - 2 * RAIL_PAD - (cols - 1) * RAIL_GAP) / cols;
  const target = Math.max(width, 2 * RAIL_PAD + cols * RAIL_CARD_W + (cols - 1) * RAIL_GAP);
  return {
    n,
    cols,
    rows,
    suspect: place,
    cardH,
    width,
    cardW: across(width),
    target,
    targetCardW: across(target),
    reach: target - width,
  };
}
