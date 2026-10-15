/**
 * Typography slice, from the landing mockup: Outfit for everything on dark (titles at 800 with
 * tight tracking), IM Fell English for what is printed on paper (the `Paper` and `HangTag`
 * components set it themselves). The faces are loaded in `theme/fonts.ts`; the stacks carry a
 * fallback so a failed load degrades to a plain sans, never to the browser's serif.
 *
 * Monospace stays for machine text only (ids, keys).
 */
import { createTheme } from '@mantine/core';
import { FONT_SANS } from './tokens';

export const typographyTheme = createTheme({
  fontFamily: FONT_SANS,
  fontFamilyMonospace:
    'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  fontSizes: { xs: '13px', sm: '14px', md: '16px', lg: '17px', xl: '19px' },
  lineHeights: { xs: '1.35', sm: '1.45', md: '1.5', lg: '1.55', xl: '1.6' },
  headings: {
    fontFamily: FONT_SANS,
    fontWeight: '800',
    sizes: {
      // the page title (`.ttl`): clamp(34px, 5vw, 50px) in the mockups
      h1: { fontSize: 'clamp(34px, 5vw, 50px)', lineHeight: '1.02' },
      // section heads (`.sec-head h2`; the footer's sign-off is 30px)
      h2: { fontSize: '34px', lineHeight: '1.1' },
      h3: { fontSize: '20px', lineHeight: '1.3', fontWeight: '600' },
    },
  },
});
