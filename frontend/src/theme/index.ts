/**
 * The site's Mantine theme, merged from four slices so a visual variant is a slice swap rather
 * than a scatter of edits across app code (build_plan §3). Every value traces back to
 * `theme/tokens.ts` (the landing mockup's tokens, the theatre's where they share a name). The
 * theatre never reads this theme: the stage is CSS modules over `materials.ts`.
 */
import { createTheme, mergeThemeOverrides } from '@mantine/core';
import { colorsTheme } from './colors';
import { typographyTheme } from './typography';
import { componentsTheme } from './components';
import { SITE_TOKENS } from './tokens';

/**
 * Radii from the mockups: `sm`/`md`/`lg` are `--r-s`/`--r-m`/`--r-l`; `xs` is the dark
 * controls' 8px; `xl` is the pill. Spacing follows the landing's rhythm (8, 12, 18, 28, 48).
 */
const layoutTheme = createTheme({
  radius: {
    xs: '8px',
    sm: SITE_TOKENS['--r-s'],
    md: SITE_TOKENS['--r-m'],
    lg: SITE_TOKENS['--r-l'],
    xl: '999px',
  },
  defaultRadius: 'sm',
  spacing: { xs: '8px', sm: '12px', md: '18px', lg: '28px', xl: '48px' },
  shadows: { xl: SITE_TOKENS['--shadow'] },
  cursorType: 'pointer',
});

export const theme = mergeThemeOverrides(
  colorsTheme,
  typographyTheme,
  layoutTheme,
  componentsTheme,
);
