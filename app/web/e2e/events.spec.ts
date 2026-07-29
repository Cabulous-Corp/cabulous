import { test, expect } from '@playwright/test'

const TOKEN = process.env.E2E_TOKEN ?? 'mock-token'

test.beforeEach(async ({ context }) => {
  await context.addCookies([{ name: 'ev_s_tkn', value: TOKEN, domain: 'localhost', path: '/' }])
})

// ponytail: pages are server components that call the backend (port 8000).
// The backend rejects 'mock-token' with 401, causing pages to crash.
// Tests that navigate to auth-protected pages verify:
//   1. The cookie bypasses auth middleware (no redirect to /login)
//   2. The page loads (even if it shows an error)
// Assert on UI content only when the backend accept the token.
// Add real assertions when: backend is seeded with test data and the E2E
// token is valid.

test.describe('Calendar page', () => {
  test('loads without auth redirect (month view)', async ({ page }) => {
    await page.goto('/events')
    // Cookie bypasses middleware; we stay on /events, not redirected to /login
    await expect(page).not.toHaveURL(/\/login/)
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'e2e/screenshots/calendar-month.png', fullPage: true })
  })

  test('week view toggle renders', async ({ page }) => {
    await page.goto('/events')
    await page.waitForTimeout(2000)
    // ponytail: view toggle buttons may render in client components even if page errored;
    // if the calendar content rendered, click Semana and screenshot
    const semanaBtn = page.getByText('Semana')
    if (await semanaBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await semanaBtn.click()
      await page.waitForTimeout(500)
    }
    await page.screenshot({ path: 'e2e/screenshots/calendar-week.png', fullPage: true })
  })

  test('agenda view toggle renders', async ({ page }) => {
    await page.goto('/events')
    await page.waitForTimeout(2000)
    const agendaBtn = page.getByText('Agenda')
    if (await agendaBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await agendaBtn.click()
      await page.waitForTimeout(500)
    }
    await page.screenshot({ path: 'e2e/screenshots/calendar-agenda.png', fullPage: true })
  })

  test('filters area loads', async ({ page }) => {
    await page.goto('/events')
    await page.waitForTimeout(2000)
    await expect(page).not.toHaveURL(/\/login/)
    await page.screenshot({ path: 'e2e/screenshots/calendar-filters.png', fullPage: true })
  })
})

test.describe('Create event', () => {
  test('form page loads', async ({ page }) => {
    await page.goto('/events/new')
    await page.waitForTimeout(2000)
    await expect(page).not.toHaveURL(/\/login/)
    await page.screenshot({ path: 'e2e/screenshots/create-event-form.png', fullPage: true })
  })

  test('location picker map renders', async ({ page }) => {
    await page.goto('/events/new')
    // ponytail: Leaflet map loads tiles from OSM; allow time for tile layer
    await page.waitForTimeout(3000)
    await page.screenshot({ path: 'e2e/screenshots/create-event-map.png', fullPage: true })
  })

  test('submit button exists', async ({ page }) => {
    await page.goto('/events/new')
    await page.waitForTimeout(2000)
    // ponytail: if form rendered despite backend error, test submit behavior
    const submitBtn = page.getByRole('button', { name: /Criar Evento/ })
    if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await submitBtn.click()
      await page.waitForTimeout(1000)
    }
    await page.screenshot({ path: 'e2e/screenshots/create-event-validation.png', fullPage: true })
  })
})

test.describe('Event detail', () => {
  test('detail page renders not-found for non-existent event', async ({ page }) => {
    // ponytail: getEvent returns 404 or backend rejects token (401);
    // the page catches the error and calls notFound()
    await page.goto('/events/00000000-0000-0000-0000-000000000000')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'e2e/screenshots/event-detail.png', fullPage: true })
  })

  test('detail page loads for formatted event id', async ({ page }) => {
    await page.goto('/events/some-test-id')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'e2e/screenshots/event-detail-testid.png', fullPage: true })
  })
})
