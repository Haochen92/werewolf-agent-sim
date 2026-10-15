import type { Metadata, Viewport } from 'next';
import '@mantine/core/styles.css';
import '@/styles/tokens.css';
import '@/styles/gpu-probe.css';
import { ColorSchemeScript, mantineHtmlProps } from '@mantine/core';
import { siteFonts } from '@/theme/fonts';
import { Providers } from './Providers';

// Every route's title reads "The Ninth Express · <page>"; a page sets only its own part.
export const metadata: Metadata = {
  title: { default: 'The Ninth Express', template: 'The Ninth Express · %s' },
  description: 'Watch AI agents deceive each other — and see exactly why.',
  // added to an iPhone's Home Screen (manifest.ts), the house opens without Safari's bars; the
  // status bar lies over the page, which the theatre pages already pad for
  appleWebApp: {
    capable: true,
    title: 'Ninth Express',
    statusBarStyle: 'black-translucent',
  },
};

// A phone: the page may reach under the notch and the home indicator (the theatre pages pad
// themselves by the safe-area insets), and the browser's own chrome takes the house's dark.
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  // iOS ignores these for the pinch (accessibility) but honours them for the double tap, which
  // otherwise zooms the page when a second fast tap misses a control (owner, 2026-10-02)
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
  themeColor: '#0c0a07',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // `mantineHtmlProps` hard-codes data-mantine-color-scheme="light" for SSR and lets the
    // client correct it after hydration. This app has no light theme — the tokens are a
    // dark two-world palette — so that default is a visible white flash on every first
    // paint. Overriding the attribute here (and forcing the scheme in the provider) means
    // the very first byte is already dark. The site's font variables sit on <html> so that
    // Mantine's portals (modals, notifications), which mount outside any page, get them too.
    <html
      lang="en"
      {...mantineHtmlProps}
      data-mantine-color-scheme="dark"
      className={siteFonts}
    >
      <head>
        <ColorSchemeScript forceColorScheme="dark" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
