/**
 * The site's faces, as the page mockups load them: Outfit (300 to 800; the titles use 800) for
 * everything on dark, and IM Fell English (roman and italic) for anything printed on paper,
 * like the hang tags. Loaded with next/font so they are self-hosted and never flash in late.
 *
 * These are the site's own instances; the theatre keeps its own in `stage/fonts.ts`, so a
 * change to one never moves the other.
 */
import { IM_Fell_English, Outfit } from 'next/font/google';

const sans = Outfit({
  weight: ['300', '400', '500', '600', '700', '800'],
  subsets: ['latin'],
  variable: '--font-site-sans',
  display: 'swap',
});

const serif = IM_Fell_English({
  weight: '400',
  style: ['normal', 'italic'],
  subsets: ['latin'],
  variable: '--font-site-serif',
  display: 'swap',
});

/** Class names that define `--font-site-sans` and `--font-site-serif`. */
export const siteFonts = `${sans.variable} ${serif.variable}`;
