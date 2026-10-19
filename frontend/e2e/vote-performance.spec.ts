import { expect, test } from '@playwright/test';

test('the vote stacks vertically without changing chip size as the tally grows', async ({
  page,
}) => {
  await page.goto('/workbench/vote?beat=17&animate=0');
  const rings = page.locator('[data-plate] image[href*="chip-ring"]');
  await expect(rings.first()).toBeVisible();
  const width = await rings.first().getAttribute('width');
  for (let beat = 18; beat <= 22; beat++) {
    await page.keyboard.press('ArrowRight');
    await expect
      .poll(() => new URL(page.url()).searchParams.get('beat'))
      .toBe(String(beat));
    for (const value of await rings.evaluateAll((els) =>
      els.map((el) => el.getAttribute('width')),
    ))
      expect(Number(value)).toBeCloseTo(Number(width), 8);
    for (const plate of await page.locator('[data-plate]').all()) {
      const xs = await plate
        .locator('image[href*="chip-ring"]')
        .evaluateAll((els) => els.map((el) => el.getAttribute('x')));
      expect(new Set(xs).size).toBeLessThanOrEqual(1);
    }
  }
});

test('each flying chip moves a small HTML box without animating its SVG faces', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto('/workbench/vote?beat=17&animate=1');
  await expect(page.locator('[data-vote-table]')).toBeVisible();
  for (const beat of [18, 19]) {
    await page.keyboard.press('ArrowRight');
    await expect
      .poll(() => new URL(page.url()).searchParams.get('beat'))
      .toBe(String(beat));
    const chip = page.locator('[data-vote-drawing="chip"]');
    const stats = await chip.evaluate(async (el) => {
      let svgWrites = 0;
      let transformWrites = 0;
      const mo = new MutationObserver((rs) => {
        for (const r of rs) {
          if (r.target instanceof SVGElement) svgWrites++;
          if (r.target === el && r.attributeName === 'style') transformWrites++;
        }
      });
      mo.observe(el, { attributes: true, subtree: true });
      const width = parseFloat((el as HTMLElement).style.width);
      const height = parseFloat((el as HTMLElement).style.height);
      await new Promise((resolve) => setTimeout(resolve, 1100));
      mo.disconnect();
      return {
        svgWrites,
        transformWrites,
        width,
        height,
        connected: el.isConnected,
      };
    });
    expect(stats.svgWrites).toBe(0);
    expect(stats.transformWrites).toBeGreaterThan(0);
    expect(stats.width * stats.height).toBeLessThan(1600 * 900 * 0.05);
    expect(stats.connected).toBe(false);
    await expect(chip).toHaveCount(0);
  }
});
