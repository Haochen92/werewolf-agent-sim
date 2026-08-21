import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

// Ruling 8: Vitest covers src/game/ only — the reducer is the load-bearing core and the
// one thing provable without a browser. No component tests, no jsdom, no E2E.
export default defineConfig({
  test: {
    include: ['src/game/**/*.test.ts'],
    environment: 'node',
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});
