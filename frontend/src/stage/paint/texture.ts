/**
 * The room's painted surfaces as SVG patterns: seamless tiles of walnut veneer, floor boards and
 * velvet, laid in the world's units. The shapes stay the paint's own vector; the tile only fills
 * them, anchored to the world rather than to the shape, so the grain stays put when the side
 * slot moves the room, and carries on across two drawings that meet (the room and its bleed).
 *
 * Each tile was tinted at conversion so its average is the flat colour it replaces (§4 of
 * stage_architecture.md): a textured surface keeps the room's value and hue. A darker flat is the
 * same tile under a black veil (`DARKER`).
 */

/** The surfaces' pictures, as URLs (a live paint) or data URIs (a paint drawn as a picture). */
export interface Wood {
  walnut: string;
  boards: string;
}

/** Units per repeat of the walnut tile (640 px): the grain reads as veneer at stage size. */
export const WALNUT = 400;

/** Units per repeat of the velvet tile (512 px): a fold every ~50 units. */
export const VELVET = 400;

/** The walnut tile, defined once in a drawing's defs for its patterns to `<use>`. */
export const walnutImage = (id: string, href: string): string =>
  `<image id="${id}" href="${href}" width="${WALNUT}" height="${WALNUT}" preserveAspectRatio="none"/>`;

// where each panel's window starts on the tile, as a share of the room it has to move in
const WINDOWS = [0, 0.62, 0.23, 0.85, 0.41];

/**
 * Veneered panels: a pattern five panels wide, each panel a different window on the walnut
 * tile, so neighbours never share their grain and the repeat is five panels long. `x0` is a
 * panel's left edge; `img` the id of `walnutImage`. Grain runs up and down.
 */
export function veneer(id: string, img: string, x0: number, panel: number): string {
  const slack = WALNUT - panel;
  let q = `<pattern id="${id}" patternUnits="userSpaceOnUse" x="${x0}" y="0" width="${panel * WINDOWS.length}" height="${WALNUT}">`;
  WINDOWS.forEach((f, i) => {
    q += `<svg x="${i * panel}" y="0" width="${panel}" height="${WALNUT}"><use href="#${img}" x="${(-f * slack).toFixed(1)}"/></svg>`;
  });
  return q + '</pattern>';
}

/** Walnut with its grain running across: a rail, a board, a pelmet. */
export const walnutAcross = (id: string, img: string): string =>
  `<pattern id="${id}" patternUnits="userSpaceOnUse" width="${WALNUT}" height="${WALNUT}" patternTransform="rotate(90)"><use href="#${img}"/></pattern>`;

/**
 * Floor boards running left to right, `plank` units wide, a seam at `y0` (and every plank on):
 * the tile's eight planks were evened out at conversion so its seams fall on that beat. The tile
 * is stretched to twice its width along the grain, so its knots repeat less often.
 */
export const boards = (id: string, href: string, y0: number, plank: number): string =>
  `<pattern id="${id}" patternUnits="userSpaceOnUse" x="0" y="${y0}" width="${16 * plank}" height="${8 * plank}"><image href="${href}" width="${16 * plank}" height="${8 * plank}" preserveAspectRatio="none"/></pattern>`;

/** Velvet in soft vertical folds. */
export const velvet = (id: string, href: string): string =>
  `<pattern id="${id}" patternUnits="userSpaceOnUse" width="${VELVET}" height="${VELVET}"><image href="${href}" width="${VELVET}" height="${VELVET}" preserveAspectRatio="none"/></pattern>`;

/**
 * The black veil's opacity that brings the walnut tile (averaging `#4a2c18`) down to a darker
 * flat of the same wood: `#3a2212` (the car's dado, the shutter's stiles)
 * or `#2c1a0e` (the shutter's louvres).
 */
export const DARKER = { '#3a2212': 0.22, '#2c1a0e': 0.41 } as const;
