import { test, expect } from '@playwright/test';

test('subpath, localization, filtering, sidebar consistency and direct refresh', async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('./');
  await expect(page.getByText('ДЕМО · вымышленные вакансии и работодатели')).toBeVisible();
  if (testInfo.project.name === 'mobile')
    await page.getByRole('button', { name: 'Обзор рынка', exact: true }).click();
  const denom = await page.getByTestId('insights-denominator').textContent();
  expect(Number(denom)).toBeGreaterThan(0);
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  if (testInfo.project.name === 'mobile')
    await page.getByRole('button', { name: 'Filters', exact: true }).click();
  await page.getByLabel('Search vacancies', { exact: true }).fill('KServe');
  if (testInfo.project.name === 'mobile')
    await page.getByRole('button', { name: 'Vacancies', exact: true }).first().click();
  const count = await page.getByTestId('results-count').textContent();
  const n = Number(count!.match(/\d+/)![0]);
  expect(n).toBeGreaterThan(0);
  await expect(page.getByTestId('vacancy')).toHaveCount(n);
  if (testInfo.project.name === 'mobile')
    await page.getByRole('button', { name: 'Market insights', exact: true }).click();
  await expect(page.getByTestId('insights-denominator')).toHaveText(String(n));
  await page.reload();
  await expect(page.getByRole('button', { name: 'EN', exact: true })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  await expect(page).toHaveURL(/q=KServe/);
  if (testInfo.project.name === 'mobile')
    await page.getByRole('button', { name: 'Vacancies', exact: true }).first().click();
  await page.getByRole('button', { name: 'Stack Relevance', exact: true }).first().click();
  await expect(page.getByRole('heading', { name: 'Stack Relevance', exact: true })).toBeVisible();
  await expect(page.getByText('No completed comparable history yet.')).toBeVisible();
  await page.screenshot({
    path: `../docs/screenshots/${testInfo.project.name}-stack-en.png`,
    fullPage: false,
  });
  expect(errors).toEqual([]);
});

test('local profile, bookmarks, details, notes and comparison persist', async ({
  page,
}, testInfo) => {
  await page.goto('./?lang=en');
  await page.getByRole('button', { name: 'Personal profile', exact: true }).first().click();
  await page
    .getByLabel('Technologies I know', { exact: true })
    .fill('Linux, Kubernetes, Python, MLflow');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await page
    .getByRole('button', { name: /Bookmark MLOps Engineer/ })
    .first()
    .click();
  await page.getByRole('button', { name: 'Details', exact: true }).first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Private local notes').fill('local-only-canary');
  await page.getByLabel('Application status', { exact: true }).selectOption('applied');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Details', exact: true }).first().click();
  await expect(page.getByLabel('Private local notes')).toHaveValue('local-only-canary');
  await expect(page.getByLabel('Application status', { exact: true })).toHaveValue('applied');
  expect(page.url()).not.toContain('local-only-canary');
  await page.keyboard.press('Escape');
  await page.getByRole('checkbox', { name: 'Compare', exact: true }).first().check();
  await page.getByRole('checkbox', { name: 'Compare', exact: true }).nth(1).check();
  await page.getByRole('button', { name: 'Compare (2/3)', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Comparison (up to 3)' })).toBeVisible();
  await page.keyboard.press('Escape');
  await page.screenshot({
    path: `../docs/screenshots/${testInfo.project.name}-vacancies-en.png`,
    fullPage: false,
  });
  await page.getByRole('button', { name: 'RU', exact: true }).click();
  await page.screenshot({
    path: `../docs/screenshots/${testInfo.project.name}-vacancies-ru.png`,
    fullPage: false,
  });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  expect(overflow).toBe(false);
});

test('forecast cold start and error state', async ({ page }) => {
  await page.goto('./?lang=en&tab=trends');
  await expect(
    page.getByText('Insufficient history for a forecast', { exact: true }),
  ).toBeVisible();
  await page.route('**/data/demo.json', (route) =>
    route.fulfill({ status: 503, body: 'unavailable' }),
  );
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('Dataset could not be loaded');
  await expect(page.getByTestId('vacancy')).toHaveCount(0);
});
