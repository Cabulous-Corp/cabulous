import { test, expect } from '@playwright/test'

test.describe('Onboarding flow', () => {
  test('full onboarding wizard works end to end', async ({ page }) => {
    const testImage = {
      name: 'test-image.png',
      mimeType: 'image/png',
      buffer: Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
        'base64',
      ),
    }

    // Login
    await page.goto('http://localhost:3000/login')
    await page.getByLabel('E-mail ou usuário').fill('test@cabulous.com')
    await page.getByLabel('Senha').fill('testpass123')
    await page.getByRole('button', { name: 'Entrar' }).click()

    // Should redirect to onboarding
    await expect(page).toHaveURL(/\/onboarding/, { timeout: 15000 })

    // Step 1: Profile
    await expect(page.getByText('Quem é você?')).toBeVisible({ timeout: 10000 })
    const layout = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
    }))
    expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth)

    const primaryBackground = await page.getByRole('button', { name: 'Continuar' }).first().evaluate(
      (element) => getComputedStyle(element).backgroundColor,
    )
    expect(primaryBackground).not.toBe('rgba(0, 0, 0, 0)')

    const stepSurface = page.locator('[data-onboarding-step]')
    await expect(stepSurface).toHaveCSS('opacity', '1')
    await page.locator('input[name="first_name"]').fill('Teste')
    await page.locator('input[name="last_name"]').fill('Usuario')
    await page.locator('input[name="username"]').fill('testuser2')
    await page.locator('input[type="file"]').nth(0).setInputFiles({ ...testImage, name: 'banner.png' })
    await page.locator('input[type="file"]').nth(1).setInputFiles({ ...testImage, name: 'avatar.png' })
    await expect(page.locator('img[src^="blob:"]')).toHaveCount(2)
    await expect(page.getByText('Não foi possível enviar a imagem. Tente novamente.')).toHaveCount(0)
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step1.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).first().click()

    // Step 2: Bio
    await expect(page.getByText('Conte sobre você')).toBeVisible({ timeout: 5000 })
    await expect(stepSurface).toHaveCSS('opacity', '1')
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step2.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).first().click()

    // Step 3: Contact
    await expect(page.getByText('Como te encontram?')).toBeVisible({ timeout: 5000 })
    await expect(stepSurface).toHaveCSS('opacity', '1')
    await page.locator('input[name="email"]').fill('test2@cabulous.com')
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step3.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).first().click()

    // Step 4: Password
    await expect(page.getByText('Sua senha')).toBeVisible({ timeout: 5000 })
    await expect(stepSurface).toHaveCSS('opacity', '1')
    await page.getByPlaceholder('Mínimo de 8 caracteres').fill('testpass123')
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step4.png', fullPage: true })
    await page.getByRole('button', { name: 'Continuar' }).first().click()

    // Step 5: Preview
    await expect(page.getByText('Seu perfil')).toBeVisible({ timeout: 5000 })
    await expect(stepSurface).toHaveCSS('opacity', '1')
    const previewMedia = page.locator('[data-profile-preview-media]')
    const previewBanner = page.locator('[data-profile-preview-banner]')
    const previewAvatar = page.locator('[data-profile-preview-avatar]')
    await expect(previewMedia).toBeVisible()
    await expect(previewBanner).toBeVisible()
    await expect(previewAvatar).toBeVisible()
    const previewImages = await page.locator('[data-profile-preview-media] img').evaluateAll(
      (images) => images.map((element) => {
        const image = element as HTMLImageElement
        return { complete: image.complete, naturalWidth: image.naturalWidth }
      }),
    )
    expect(previewImages).toHaveLength(2)
    expect(previewImages.every((image) => image.complete && image.naturalWidth > 0)).toBe(true)
    const previewLayers = await Promise.all([
      previewBanner.boundingBox(),
      previewAvatar.boundingBox(),
      previewBanner.evaluate((element) => getComputedStyle(element).zIndex),
      previewAvatar.evaluate((element) => getComputedStyle(element).zIndex),
    ])
    expect(previewLayers[0]).not.toBeNull()
    expect(previewLayers[1]).not.toBeNull()
    expect(previewLayers[1]!.y).toBeLessThan(previewLayers[0]!.y + previewLayers[0]!.height)
    expect(Number(previewLayers[3])).toBeGreaterThan(Number(previewLayers[2]))
    const previewName = page.getByRole('heading', { name: 'Teste Usuario', exact: true })
    const previewNameBox = await previewName.boundingBox()
    expect(previewNameBox).not.toBeNull()
    expect(previewNameBox!.y).toBeGreaterThan(previewLayers[0]!.y + previewLayers[0]!.height)
    await page.screenshot({ path: 'e2e/screenshots/onboarding-step5.png', fullPage: true })
    await page.getByRole('button', { name: 'Concluir!' }).click()

    // Should redirect to home
    await expect(page).toHaveURL('/', { timeout: 10000 })
    await page.screenshot({ path: 'e2e/screenshots/onboarding-done.png', fullPage: true })
  })
})
