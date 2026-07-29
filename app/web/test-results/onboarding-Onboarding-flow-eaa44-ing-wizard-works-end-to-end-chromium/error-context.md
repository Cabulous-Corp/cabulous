# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: onboarding.spec.ts >> Onboarding flow >> full onboarding wizard works end to end
- Location: e2e\onboarding.spec.ts:4:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByPlaceholder('Nome')
Expected: visible
Error: strict mode violation: getByPlaceholder('Nome') resolved to 3 elements:
    1) <input data-slot="input" name="first_name" placeholder="Nome" class="h-16 w-100 min-w-0 px-4 rounded-md bg-input text-base transition-all outline-none border border-input hover:border-purple-500 file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 focus-within:ring-2 focus-within:…/> aka getByRole('textbox', { name: 'Nome', exact: true })
    2) <input name="last_name" data-slot="input" placeholder="Sobrenome" class="h-16 w-100 min-w-0 px-4 rounded-md bg-input text-base transition-all outline-none border border-input hover:border-purple-500 file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 focus-within:ring-2 focus-wit…/> aka getByRole('textbox', { name: 'Sobrenome' })
    3) <input name="username" data-slot="input" placeholder="@seunome" class="h-16 w-100 min-w-0 px-4 rounded-md bg-input text-base transition-all outline-none border border-input hover:border-purple-500 file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 focus-within:ring-2 focus-withi…/> aka getByRole('textbox', { name: '@seunome' })

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByPlaceholder('Nome')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]: 1 de 5
    - generic [ref=e14]:
      - generic [ref=e15]:
        - heading "Quem e voce?" [level=2] [ref=e16]
        - paragraph [ref=e17]: Conte um pouco sobre voce.
      - generic [ref=e18]:
        - generic [ref=e19] [cursor=pointer]:
          - button "Choose File" [ref=e20]
          - generic [ref=e21]: Adicionar banner
        - generic [ref=e29] [cursor=pointer]:
          - button "Choose File" [ref=e30]
          - generic [ref=e31]: "?"
        - generic [ref=e37]:
          - text: Nome completo *
          - generic [ref=e38]:
            - textbox "Nome" [ref=e41]
            - textbox "Sobrenome" [ref=e44]
        - generic [ref=e45]:
          - text: Username *
          - textbox "@seunome" [ref=e48]
      - button "Continuar" [ref=e49] [cursor=pointer]
  - region "Notifications alt+T"
  - button "Open Next.js Dev Tools" [ref=e55] [cursor=pointer]
  - alert [ref=e59]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | 
  3  | test.describe('Onboarding flow', () => {
  4  |   test('full onboarding wizard works end to end', async ({ page }) => {
  5  |     // Login
  6  |     await page.goto('http://localhost:3000/login')
  7  |     await page.getByPlaceholder('Email/User').fill('test@cabulous.com')
  8  |     await page.getByPlaceholder('Password').fill('testpass123')
  9  |     await page.getByRole('button', { name: /Sign in/ }).click()
  10 | 
  11 |     // Should redirect to onboarding
  12 |     await expect(page).toHaveURL(/\/onboarding/, { timeout: 15000 })
  13 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-step1.png', fullPage: true })
  14 | 
  15 |     // Step 1: Profile
  16 |     await expect(page.getByText('Quem e voce?')).toBeVisible({ timeout: 10000 })
> 17 |     await expect(page.getByPlaceholder('Nome')).toBeVisible()
     |                                                 ^ Error: expect(locator).toBeVisible() failed
  18 |     await expect(page.getByPlaceholder('Sobrenome')).toBeVisible()
  19 |     await expect(page.getByText('Adicionar banner')).toBeVisible()
  20 |     await page.getByPlaceholder('Nome').fill('Teste')
  21 |     await page.getByPlaceholder('Sobrenome').fill('Usuario')
  22 |     await page.getByPlaceholder('@seunome').fill('testuser2')
  23 |     await page.getByRole('button', { name: 'Continuar' }).click()
  24 | 
  25 |     // Step 2: Bio
  26 |     await expect(page.getByText('Conte sobre voce')).toBeVisible({ timeout: 5000 })
  27 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-step2.png', fullPage: true })
  28 |     await page.getByRole('button', { name: 'Continuar' }).click()
  29 | 
  30 |     // Step 3: Contact
  31 |     await expect(page.getByText('Como te encontram?')).toBeVisible({ timeout: 5000 })
  32 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-step3.png', fullPage: true })
  33 |     await page.getByRole('button', { name: 'Continuar' }).click()
  34 | 
  35 |     // Step 4: Password
  36 |     await expect(page.getByText('Sua senha')).toBeVisible({ timeout: 5000 })
  37 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-step4.png', fullPage: true })
  38 |     await page.getByPlaceholder('Minimo 8 caracteres').fill('testpass123')
  39 |     await page.getByRole('button', { name: 'Continuar' }).click()
  40 | 
  41 |     // Step 5: Preview
  42 |     await expect(page.getByText('Seu perfil')).toBeVisible({ timeout: 5000 })
  43 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-step5.png', fullPage: true })
  44 |     await page.getByRole('button', { name: 'Concluir!' }).click()
  45 | 
  46 |     // Should redirect to home
  47 |     await expect(page).toHaveURL('/', { timeout: 10000 })
  48 |     await page.screenshot({ path: 'e2e/screenshots/onboarding-done.png', fullPage: true })
  49 |   })
  50 | })
  51 | 
```