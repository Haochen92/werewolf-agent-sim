import type { MetadataRoute } from 'next';

/**
 * The web app manifest: what a phone does with "Add to Home Screen" (and Chrome's "Install").
 * Opened from that icon the house runs without the browser's bars, which on an iPhone is the
 * only way to the whole screen (Safari there has no fullscreen for a page). It starts at the
 * front door, the landing, and its scope is the whole site, so a game or a replay reached from
 * there stays in the standalone window. Nothing changes for a page opened in the browser.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'The Ninth Express',
    short_name: 'Ninth Express',
    description: 'Watch AI agents deceive each other — and see exactly why.',
    start_url: '/',
    scope: '/',
    display: 'standalone',
    background_color: '#0c0a07',
    theme_color: '#0c0a07',
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
      {
        src: '/icons/maskable-512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}
