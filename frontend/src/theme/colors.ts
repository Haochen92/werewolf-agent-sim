/**
 * Colour slice. The palette itself lives in `styles/tokens.css` (one source of truth,
 * usable from CSS modules); this slice teaches Mantine's own components the same colours so
 * a `<Button>` and a hand-styled bubble agree without either restating a hex.
 */
import { createTheme, type MantineColorsTuple } from '@mantine/core';

/** Amber — the story world's single accent, read as pooled lamplight. */
const amber: MantineColorsTuple = [
  '#fdf3e2',
  '#f7e3c4',
  '#f0cf9c',
  '#e9bb74',
  '#e4ac57',
  '#e0a33f', // 5 — --amber
  '#c98f33',
  '#8a6526', // 7 — --amber-dim
  '#5c4319',
  '#2f220d',
];

/** Cold cyan — the machine world. Deliberately never used in story-world chrome. */
const xrayCyan: MantineColorsTuple = [
  '#e4f7f9',
  '#c3ecf0',
  '#9adfe6',
  '#72d2dc',
  '#58c6d1', // 4 — --cyan
  '#43b3be',
  '#3a9aa4',
  '#2c6067', // 7 — --cyan-dim
  '#1c4045',
  '#0e2225',
];

/**
 * Warm ink — replaces Mantine's blue-grey `dark` scale outright. Without this every stock
 * Mantine surface reads cold and fights the tavern, which is the exact failure the
 * baseline calls out.
 */
const ink: MantineColorsTuple = [
  '#e9dfd4', // 0 — --text
  '#c4b7ab',
  '#a4948a', // 2 — --text-dim
  '#6d605a', // 3 — --text-faint
  '#3a2f29', // 4 — --ink-500
  '#2a221e', // 5 — --ink-600
  '#1e1815', // 6 — --ink-700
  '#16120f', // 7 — --ink-800
  '#100d0c', // 8 — --ink-850
  '#0b0908', // 9 — --ink-900
];

export const colorsTheme = createTheme({
  colors: { amber, xrayCyan, dark: ink },
  primaryColor: 'amber',
  primaryShade: { light: 6, dark: 5 },
  white: '#e9dfd4',
  black: '#0b0908',
});
