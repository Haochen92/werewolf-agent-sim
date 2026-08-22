import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

// The reducer/store stay the load-bearing suite. A small server-rendered component layer
// additionally proves that entitled faction/private data has an actual render consumer;
// it needs no browser or jsdom.
export default defineConfig({
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
