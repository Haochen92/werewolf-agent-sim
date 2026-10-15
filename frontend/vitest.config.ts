import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

// Next turns an image import into { src, width, height }; plain Vite gives a URL string.
// This mirrors Next's shape so tests can check the handles the manifest exports.
const staticImages = {
  name: 'next-static-image',
  enforce: 'pre' as const,
  async load(id: string) {
    if (!/\.(webp|png|jpe?g)$/.test(id)) return null;
    const { width, height } = await sharp(id).metadata();
    return `export default ${JSON.stringify({ src: id, width, height })};`;
  },
};

// The reducer/store stay the load-bearing suite. A small server-rendered component layer
// additionally proves that entitled faction/private data has an actual render consumer;
// it needs no browser or jsdom.
export default defineConfig({
  plugins: [staticImages],
  esbuild: { jsx: 'automatic' },
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    environment: 'node',
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});
