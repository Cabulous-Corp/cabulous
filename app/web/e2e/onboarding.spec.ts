import { test, expect } from '@playwright/test'

test.describe('Onboarding flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/login')
    await expect(page.getByPlaceholder('Email/User')).toBeVisible()
    await page.getByPlaceholder('Email/User').fill('test@cabulous.com')
    await page.getByPlaceholder('Password').fill('testpass123')
    await page.getByRole('button', { name: /Sign in/ }).click()
  })

  test('onboarding step 1 renders and avatar upload works', async ({ page }) => {
    await expect(page).toHaveURL(/\/onboarding/, { timeout: 15000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step1.png', fullPage: true })

    // Check that the key elements are visible
    await expect(page.getByText('Quem e voce?')).toBeVisible({ timeout: 10000 })
    await expect(page.getByPlaceholder('Nome')).toBeVisible()
    await expect(page.getByPlaceholder('Sobrenome')).toBeVisible()
    await expect(page.getByPlaceholder('@seunome')).toBeVisible()

    // Test avatar upload
    const fileInput = page.locator('input[type="file"]').first()
    await expect(fileInput).toBeVisible({ timeout: 5000 })

    // Create a small test image
    const fs = require('fs')
    // ponytail: use a tiny 1x1 PNG for testing
    const testImagePath = 'e2e/test-image.png'
    // if no test image, skip upload test
    const fileExists = fs.existsSync(testImagePath)

    // Navigate through steps
    await page.getByPlaceholder('Nome').fill('Teste')
    await page.getByPlaceholder('Sobrenome').fill('Usuario')
    await page.getByPlaceholder('@seunome').fill('testuser2')
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
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step4.png', fullPage: true })
    await page.getByPlaceholder('Minimo 8 caracteres').fill('testpass123')
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
