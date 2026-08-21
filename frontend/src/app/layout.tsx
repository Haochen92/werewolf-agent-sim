import type { Metadata } from 'next';
import { Silkscreen } from 'next/font/google';
import { ColorSchemeScript, mantineHtmlProps } from '@mantine/core';
import { Providers } from './Providers';

import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@/styles/tokens.css';

/**
 * The pixel display face — titles and chrome only (ux_baseline §1). Silkscreen over the
 * blockier Press Start 2P: at heading sizes it stays legible, which matters because these
 * are navigational labels, not decoration. `display: 'swap'` with the sans stack behind it
 * means a font failure degrades to sans instead of blocking the render.
 */
const display = Silkscreen({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Werewolf — agent sim',
  description: 'Watch AI agents deceive each other — and see exactly why.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" {...mantineHtmlProps} className={display.variable}>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
