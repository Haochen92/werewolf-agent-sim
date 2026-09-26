/**
 * Colour slice. The values come from `theme/tokens.ts` (the landing mockup's tokens, with the
 * theatre's value wherever the two share a name); this slice teaches Mantine's components the
 * same colours, so a Mantine `<Button>` and a CSS-module panel agree without restating a hex.
 *
 * Mantine wants ten shades per colour with the brand shade at 5 (`primaryShade`). The ramps
 * below mix the token toward the page's light text above 5 and toward the page's black below
 * it, so every shade stays in the lamplit palette.
 */
import { createTheme, type MantineColorsTuple } from '@mantine/core';
import { THEATRE_ALIASES as T, SITE_TOKENS as S } from './tokens';

function hex(c: string): [number, number, number] {
  const n = parseInt(c.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function mix(a: string, b: string, t: number): string {
  const [x, y] = [hex(a), hex(b)];
  return `#${x
    .map((v, i) =>
      Math.round(v + (y[i] - v) * t)
        .toString(16)
        .padStart(2, '0'),
    )
    .join('')}`;
}

/** Ten shades around `base` at index 5: light toward the text colour, dark toward the ground. */
function ramp(base: string): MantineColorsTuple {
  const up = [0.86, 0.7, 0.52, 0.34, 0.16].map((t) => mix(base, S['--text'], t));
  const down = [0.18, 0.36, 0.54, 0.72].map((t) => mix(base, S['--bg'], t));
  return [...up, base, ...down] as unknown as MantineColorsTuple;
}

/** Amber: the town's lamplight, the one accent (`--amber`, the theatre's). */
const amber = ramp(T['--amber']);
const wolf = ramp(T['--wolf']);
const sk = ramp(T['--sk']);
const brass = ramp(S['--brass']);

/**
 * Warm ink: replaces Mantine's blue-grey `dark` scale, which drives its dark-scheme surfaces
 * (0 text, 2 dimmed, 4 borders, 6 inputs, 7 the body). Without it every stock Mantine surface
 * reads cold against the lamplit pages.
 */
const dark: MantineColorsTuple = [
  S['--text'], // 0 text
  '#d6cab4',
  S['--muted'], // 2 dimmed
  '#7f735f',
  T['--cloak2'], // 4 borders
  S['--panel-2'], // 5 hover
  S['--panel'], // 6 input and paper surfaces
  S['--bg'], // 7 the body
  '#080604',
  '#050403',
];

export const colorsTheme = createTheme({
  colors: { amber, wolf, sk, brass, dark },
  primaryColor: 'amber',
  primaryShade: 5,
  white: S['--text'],
  black: S['--bg'],
});
