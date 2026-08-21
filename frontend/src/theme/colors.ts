/**
 * Colour slice. Skeleton only at this stage — the aesthetic pass (hi-bit pixel × séance
 * noir, ux_baseline §1) fills it in without app code changing, which is the whole point of
 * splitting the theme into slices.
 */
import { createTheme, type MantineColorsTuple } from '@mantine/core';

/** Amber: the story world's single interactive/highlight accent. */
const amber: MantineColorsTuple = [
  '#fff8e1',
  '#ffecb3',
  '#ffe082',
  '#ffd54f',
  '#ffca28',
  '#ffc107',
  '#ffb300',
  '#ffa000',
  '#ff8f00',
  '#ff6f00',
];

/** Cold cyan: the machine world (X-ray panes, vote matrix, scheduler detail). */
const xrayCyan: MantineColorsTuple = [
  '#e0f7fa',
  '#b2ebf2',
  '#80deea',
  '#4dd0e1',
  '#26c6da',
  '#00bcd4',
  '#00acc1',
  '#0097a7',
  '#00838f',
  '#006064',
];

export const colorsTheme = createTheme({
  colors: { amber, xrayCyan },
  primaryColor: 'amber',
  primaryShade: { light: 6, dark: 5 },
});
