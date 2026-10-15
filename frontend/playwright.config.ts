/**
 * Playwright drives the workbench headless (stage_architecture.md §7): one screenshot per
 * named workbench URL, compared against a golden once the scene has settled. It is how an
 * agent sees the stage without the owner at the screen; not a CI gate until the scenes stop
 * moving.
 *
 * It does not start a server. Run the dev server first (`npx next dev -p 3117`), or point
 * `WORKBENCH_URL` at any running build, then `npm run e2e` (`-- --update-snapshots` to
 * regenerate the goldens after a deliberate change, and read the diff).
 */
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  snapshotPathTemplate: '{testDir}/__screenshots__/{arg}{ext}',
  fullyParallel: true,
  reporter: [['list']],
  use: {
    baseURL: process.env.WORKBENCH_URL ?? 'http://localhost:3117',
  },
  expect: {
    // the stage is raster sprites over SVG paint: allow antialiasing noise, not a moved object
    toHaveScreenshot: { maxDiffPixelRatio: 0.005, animations: 'disabled' },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1600, height: 900 } },
    },
  ],
});
