/**
 * The theme, merged from four slices so a visual variant is a slice swap rather than a
 * scatter of edits across app code (build_plan §3). The layout slice is where spacing and
 * radii land in the styling pass.
 */
import { createTheme, mergeThemeOverrides } from '@mantine/core';
import { colorsTheme } from './colors';
import { typographyTheme } from './typography';
import { componentsTheme } from './components';

const layoutTheme = createTheme({
  defaultRadius: 'sm',
});

export const theme = mergeThemeOverrides(
  colorsTheme,
  typographyTheme,
  layoutTheme,
  componentsTheme,
);
