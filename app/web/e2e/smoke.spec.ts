import { test, expect } from '@playwright/test'

test.describe('Auth smoke tests', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('Faca seu Login')).toBeVisible()
    await expect(page.getByPlaceholder('Email/User')).toBeVisible()
    await expect(page.getByPlaceholder('Password')).toBeVisible()
  })

  test('redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveURL(/\/login/)
  })

  test('successful login redirects to home', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('Email/User').fill('test@cabulous.com')
    await page.getByPlaceholder('Password').fill('testpass123')
    await page.getByRole('button', { name: /Sign in/ }).click()
    await expect(page).toHaveURL('/')
  })
})

test.describe('Calendar smoke tests', () => {
  test('calendar page renders with navigation', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events')
    await expect(page.getByText('Eventos')).toBeVisible()
    await expect(page.getByText('Mes')).toBeVisible()
    await expect(page.getByText('Semana')).toBeVisible()
    await expect(page.getByText('Agenda')).toBeVisible()
  })

  test('view toggle switches views', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events')
    await page.getByText('Agenda').click()
    await page.waitForURL('/events')
    await page.getByText('Mes').click()
    await page.waitForURL('/events')
  })
})

test.describe('Event detail smoke tests', () => {
  test('event detail page renders tabs', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events/some-uuid')
    await expect(page.getByText(/Participantes|Fotos|Highlights/)).toBeVisible({ timeout: 15000 })
  })
})

test.describe('Create event smoke tests', () => {
  test('create event page renders form fields', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events/new')
    await expect(page.getByText('Novo Evento')).toBeVisible()
    await expect(page.getByPlaceholder('Nome do evento')).toBeVisible()
  })
})
