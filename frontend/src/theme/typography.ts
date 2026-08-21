/**
 * Typography slice.
 *
 * The non-negotiable from ux_baseline §1: ALL dialogue and UI text stays on the clean sans
 * stack. Pixel display type is for page titles and chrome ONLY, and monospace is reserved
 * exclusively for machine-world panes. Both contrasts collapse the moment either leaks into
 * body text, and this is a reading app before it is an atmospheric one — so GM narration,
 * which is tempting to make "special", stays body text.
 *
 * `--font-display` is wired to a real pixel face in `app/layout.tsx` via `next/font`, with
 * the sans stack behind it: if the face ever fails to load, chrome degrades to sans rather
 * than to a fallback that misrenders at display sizes.
 */
import { createTheme } from '@mantine/core';

const SANS = 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

export const typographyTheme = createTheme({
  fontFamily: SANS,
  fontFamilyMonospace:
    'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  headings: {
    // Headings are chrome — they take the display face through the CSS variable.
    fontFamily: `var(--font-display), ${SANS}`,
    sizes: {
      h1: { fontSize: '1.6rem', lineHeight: '1.3' },
      h2: { fontSize: '1.2rem', lineHeight: '1.35' },
      h3: { fontSize: '1rem', lineHeight: '1.4' },
    },
  },
  lineHeights: { xs: '1.4', sm: '1.5', md: '1.65', lg: '1.7', xl: '1.75' },
});
