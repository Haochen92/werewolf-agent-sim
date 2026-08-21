/**
 * Hand-authored pixel glyphs on ONE 16×16 grid (ux_baseline §1 asset set: wolf / serial
 * killer / vigilante / lynch).
 *
 * Authored as string grids rather than path data on purpose: the art stays legible and
 * editable in the source, the 16-grid is enforced by construction rather than by
 * convention, and `shapeRendering="crispEdges"` keeps the pixels hard at any scale — an
 * antialiased pixel glyph is just a blurry glyph.
 *
 * These are the four DEATH marks. Role icons use tabler (per the baseline) rather than
 * being hand-authored, since a role badge is chrome, not story.
 */
import type { DeathGlyphKind } from '../manifest';

const GRID = 16;

// prettier-ignore
const FANGS = [
  '................',
  '................',
  '..###......###..',
  '..####....####..',
  '..####....####..',
  '..####....####..',
  '...###....###...',
  '...###....###...',
  '....##....##....',
  '....##....##....',
  '.....#....#.....',
  '.....#....#.....',
  '......#..#......',
  '................',
  '................',
  '................',
];

// prettier-ignore
const DAGGER = [
  '.......##.......',
  '......####......',
  '......####......',
  '......####......',
  '......####......',
  '......####......',
  '......####......',
  '......####......',
  '....########....',
  '.......##.......',
  '.......##.......',
  '......####......',
  '......####......',
  '......####......',
  '.......##.......',
  '................',
];

// prettier-ignore
const CARTRIDGE = [
  '.......##.......',
  '......####......',
  '.....######.....',
  '....########....',
  '....########....',
  '....########....',
  '....########....',
  '....########....',
  '...##########...',
  '...##########...',
  '....########....',
  '....########....',
  '....########....',
  '...##########...',
  '................',
  '................',
];

// prettier-ignore
const NOOSE = [
  '......##........',
  '......##........',
  '......##........',
  '......##........',
  '....######......',
  '....######......',
  '...##....##.....',
  '..##......##....',
  '..##......##....',
  '..##......##....',
  '..##......##....',
  '...##....##.....',
  '....######......',
  '................',
  '................',
  '................',
];

const GRIDS: Record<DeathGlyphKind, string[]> = {
  wolves: FANGS,
  serial_killer: DAGGER,
  vigilante: CARTRIDGE,
  lynch: NOOSE,
};

const LABELS: Record<DeathGlyphKind, string> = {
  wolves: 'killed by the wolves',
  serial_killer: 'killed by the serial killer',
  vigilante: 'shot by the vigilante',
  lynch: 'lynched by the village',
};

export function PixelGlyph({
  kind,
  size = 16,
  color = 'currentColor',
}: {
  kind: DeathGlyphKind;
  size?: number;
  color?: string;
}) {
  const grid = GRIDS[kind];
  const rects: React.ReactNode[] = [];

  // Merge each run of lit pixels into one rect: a 16×16 glyph is ~60 rects unmerged, and
  // these render once per death notice in a transcript that can hold many.
  grid.forEach((row, y) => {
    let runStart: number | null = null;
    for (let x = 0; x <= GRID; x += 1) {
      const lit = row[x] === '#';
      if (lit && runStart === null) runStart = x;
      if (!lit && runStart !== null) {
        rects.push(
          <rect
            key={`${y}-${runStart}`}
            x={runStart}
            y={y}
            width={x - runStart}
            height={1}
          />,
        );
        runStart = null;
      }
    }
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${GRID} ${GRID}`}
      fill={color}
      shapeRendering="crispEdges"
      role="img"
      aria-label={LABELS[kind]}
      style={{ flexShrink: 0, verticalAlign: 'text-bottom' }}
    >
      {rects}
    </svg>
  );
}
