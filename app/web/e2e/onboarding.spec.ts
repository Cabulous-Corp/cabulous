import { test, expect } from '@playwright/test'

test.describe('Onboarding flow', () => {
  test('full onboarding wizard works end to end', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000/login')
    await page.getByPlaceholder('Email/User').fill('test@cabulous.com')
    await page.getByPlaceholder('Password').fill('testpass123')
    await page.getByRole('button', { name: /Sign in/ }).click()

    // Should redirect to onboarding
    await expect(page).toHaveURL(/\/onboarding/, { timeout: 15000 })

    // Step 1: Profile
    await expect(page.getByText('Quem e voce?')).toBeVisible({ timeout: 10000 })
    await page.getByRole('textbox', { name: 'Nome' }).fill('Teste')
    await page.getByRole('textbox', { name: 'Sobrenome' }).fill('Usuario')
    await page.getByRole('textbox', { name: '@seunome' }).fill('testuser2')
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step1.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).click()

    // Step 2: Bio
    await expect(page.getByText('Conte sobre voce')).toBeVisible({ timeout: 5000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step2.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).click()

    // Step 3: Contact
    await expect(page.getByText('Como te encontram?')).toBeVisible({ timeout: 5000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step3.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).click()

    // Step 4: Password
    await expect(page.getByText('Sua senha')).toBeVisible({ timeout: 5000 })
    await page.getByPlaceholder('Minimo 8 caracteres').fill('testpass123')
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step4.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).click()

    // Step 5: Preview
    await expect(page.getByText('Seu perfil')).toBeVisible({ timeout: 5000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step5.png', fullPage: true })
    await page.getByRole('button', { name: 'Concluir!' }).click()

    // Should redirect to home
    await expect(page).toHaveURL('/', { timeout: 10000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-done.png', fullPage: true })
  })
})
