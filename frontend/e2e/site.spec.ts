/**
 * The site shell (app/(site)/layout.tsx): every site page wears the top nav with the product
 * name and the footer with the GitHub link, and the theatre's routes wear neither. No API is
 * running for these; the pages' own data may fail to load, the chrome must not care.
 */
import { expect, test } from '@playwright/test';

const GITHUB = 'https://github.com/Haochen92/werewolf-agent-sim';

for (const path of ['/', '/replays', '/rooms', '/play']) {
  test(`site shell: ${path}`, async ({ page }) => {
    await page.goto(path);
    await expect(page).toHaveTitle(/^Carriage Nine/);

    const nav = page.getByRole('navigation', { name: 'Site' });
    await expect(nav.getByRole('link', { name: 'Carriage Nine' })).toBeVisible();
    for (const door of ['Play', 'Rooms', 'Replays']) {
      await expect(nav.getByRole('link', { name: door, exact: true })).toBeVisible();
    }

    const footer = page.getByRole('contentinfo');
    await expect(footer.getByRole('link', { name: 'GitHub', exact: true })).toHaveAttribute(
      'href',
      GITHUB,
    );
    await expect(footer).toContainText('Liu Haochen');
  });
}

test('the theatre wears no site chrome: /workbench/day', async ({ page }) => {
  await page.goto('/workbench/day?beat=6&animate=0&strip=0', { waitUntil: 'networkidle' });
  // the stage rendered (the speaker's figure is up), and around it there is no nav or footer
  await expect(page.locator('[data-layer="figures"] img')).toHaveCount(1);
  await expect(page.getByRole('navigation', { name: 'Site' })).toHaveCount(0);
  await expect(page.getByText('Carriage Nine', { exact: true })).toHaveCount(0);
  await expect(page.locator(`a[href="${GITHUB}"]`)).toHaveCount(0);
});
