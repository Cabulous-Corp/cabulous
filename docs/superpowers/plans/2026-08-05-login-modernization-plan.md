# Modernização da página de login — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `/login` as a responsive split-panel shadcn interface while preserving the existing authentication behavior.

**Architecture:** Keep the auth action and API untouched. Replace the page composition with a two-column brand panel plus a shadcn card form, using CSS/Tailwind animation utilities instead of the current random triangle component. On mobile, the same two sections stack vertically without fixed-height overflow.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS v4, tw-animate-css, Radix/shadcn primitives, React Hook Form, Playwright, Bun.

## Global Constraints

- Use the existing shadcn primitives; do not add dependencies or create new UI primitives.
- Preserve `loginAction`, the identifier/password payload, the `/forgot-password` link, error handling, loading state and success redirect to `/`.
- All visible login copy must be valid pt-BR with accents.
- Remove the triangle animation component, random timers and its explicit TypeScript include.
- Keep the page accessible: visible labels, associated validation messages, keyboard focus and reduced-motion support.
- Use Bun for all frontend commands.

---

### Task 1: Define the new login contract with a failing E2E test

**Files:**
- Modify: `app/web/e2e/smoke.spec.ts:4-24`

**Interfaces:**
- Produces the selectors and user-visible copy that the page implementation must provide: `Entrar`, `E-mail ou usuário`, `Senha`, `Conecte-se ao que importa.`, `[data-login-panel="brand"]`, and `[data-login-panel="form"]`.

- [ ] **Step 1: Replace stale login assertions with the desired behavior**

Update the login render test to assert the new Portuguese copy, labels and split-panel hooks:

```ts
test('login page renders the split-panel form', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: 'Entrar', exact: true })).toBeVisible()
  await expect(page.getByText('Conecte-se ao que importa.')).toBeVisible()
  await expect(page.getByLabel('E-mail ou usuário')).toBeVisible()
  await expect(page.getByLabel('Senha')).toBeVisible()
  await expect(page.locator('[data-login-panel="brand"]')).toBeVisible()
  await expect(page.locator('[data-login-panel="form"]')).toBeVisible()
})
```

Replace the submit locators with `getByLabel('E-mail ou usuário')`, `getByLabel('Senha')` and `getByRole('button', { name: 'Entrar' })` so the test verifies the accessible interface rather than placeholder text.

- [ ] **Step 2: Add the responsive and reduced-motion regression test**

Add a focused test that checks both layouts without depending on pixel coordinates:

```ts
test('login page stacks on mobile without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/login')

  await expect(page.locator('[data-login-panel="brand"]')).toBeVisible()
  await expect(page.locator('[data-login-panel="form"]')).toBeVisible()
  await expect(page.locator('body')).toHaveJSProperty('scrollWidth', 390)
})
```

- [ ] **Step 3: Run the targeted E2E test and verify the expected RED failure**

Run from `app/web`:

```bash
bunx playwright test e2e/smoke.spec.ts --project=chromium --workers=1 -g "login page|submit login form"
```

Expected result: the new login render test fails because the current page has no `Entrar` heading, no accessible field labels, no split-panel data attributes and still exposes the old copy. Fix the test if it fails for a selector or syntax error rather than the missing feature.

- [ ] **Step 4: Commit the failing-test contract**

```bash
git add app/web/e2e/smoke.spec.ts
git commit -m "test: define modern login interface"
```

### Task 2: Replace the login page with the split-panel shadcn layout

**Files:**
- Modify: `app/web/app/(auth)/login/page.tsx`
- Modify: `app/web/app/(auth)/layout.tsx`

**Interfaces:**
- Consumes the existing `loginAction`, `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage`, `Input`, `Card` and `Button` components.
- Produces an accessible page with `data-login-panel="brand"` and `data-login-panel="form"` hooks consumed by Task 1.

- [ ] **Step 1: Replace the page composition with the minimal two-panel implementation**

Keep the existing `useForm`, `handleLogin`, `submitError` and `isSubmitting` logic. Replace the rendered tree with:

```tsx
<main className="grid min-h-svh w-full bg-background lg:grid-cols-[minmax(18rem,0.85fr)_minmax(28rem,1.15fr)]">
  <section data-login-panel="brand" className="relative isolate flex min-h-56 overflow-hidden bg-linear-to-br from-[#2b1d43] via-[#543a78] to-[#8b68bd] p-8 text-white lg:min-h-svh lg:p-12">
    <div aria-hidden="true" className="animate-pulse-slow motion-reduce:animate-none absolute -right-20 -top-20 size-72 rounded-full bg-white/15 blur-3xl" />
    <div className="relative z-10 flex max-w-sm flex-col justify-between gap-12">
      <span className="text-sm font-semibold tracking-[0.24em] uppercase">Cabulous</span>
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Conecte-se ao que importa.</h1>
        <p className="mt-4 max-w-xs text-sm leading-6 text-white/75">Entre para continuar sua jornada na comunidade.</p>
      </div>
    </div>
  </section>

  <section data-login-panel="form" className="flex items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
    <Card className="w-full max-w-md border-border/70 shadow-lg shadow-foreground/5">
      <CardHeader className="gap-2 px-6 pt-7 sm:px-8 sm:pt-8">
        <CardTitle className="text-2xl">Entrar</CardTitle>
        <CardDescription>Use seu e-mail ou usuário para acessar sua conta.</CardDescription>
      </CardHeader>
      <CardContent className="px-6 pb-7 sm:px-8 sm:pb-8">
        <Form {...form}>
          <form className="grid gap-5" onSubmit={form.handleSubmit(handleLogin)}>
            <FormField
              control={form.control}
              name="identifier"
              rules={{ required: 'E-mail ou usuário é obrigatório.' }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>E-mail ou usuário</FormLabel>
                  <FormControl>
                    <Input {...field} type="text" placeholder="seu@email.com" startAdornment={<Mail aria-hidden="true" />} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              rules={{ required: 'Senha é obrigatória.', minLength: { value: 8, message: 'A senha deve ter pelo menos 8 caracteres.' } }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Senha</FormLabel>
                  <FormControl>
                    <Input {...field} type="password" placeholder="••••••••" startAdornment={<LockKeyhole aria-hidden="true" />} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {submitError ? <p role="alert" className="text-sm text-destructive">{submitError}</p> : null}
            <div className="flex items-center justify-between gap-4">
              <Button asChild variant="link" className="h-auto px-0 text-sm">
                <Link href="/forgot-password">Esqueceu sua senha?</Link>
              </Button>
              <Button type="submit" size="lg" disabled={isSubmitting}>
                {isSubmitting ? 'Entrando...' : 'Entrar'}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  </section>
</main>
```

Use `Mail` and `LockKeyhole` from `lucide-react` as the existing `Input` adornments. Use labels `E-mail ou usuário` and `Senha`, placeholders `seu@email.com` and `••••••••`, messages `E-mail ou usuário é obrigatório.` and `Senha é obrigatória.`, and button text `Entrar`/`Entrando...`. Render `submitError` in a paragraph with `role="alert"`.

- [ ] **Step 2: Add the form field structure and preserve submission behavior**

Each field must follow this structure so labels and errors are associated:

```tsx
<FormField
  control={form.control}
  name="identifier"
  rules={{ required: 'E-mail ou usuário é obrigatório.' }}
  render={({ field }) => (
    <FormItem>
      <FormLabel>E-mail ou usuário</FormLabel>
      <FormControl>
        <Input {...field} type="text" placeholder="seu@email.com" startAdornment={<Mail aria-hidden="true" />} />
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/> 
```

Keep the password `minLength` rule at 8, the forgot-password `Link`, the `loginAction` payload `{ identifier: values.identifier, password: values.password }`, the `router.push('/')` success path, and the existing error fallback behavior.

- [ ] **Step 3: Simplify the auth layout wrapper**

Remove the `divlay` class and the old radial wrapper. The auth layout should only provide `min-h-svh w-full bg-background` around its children so the page owns the split composition and dark-mode surface.

- [ ] **Step 4: Run targeted E2E and verify GREEN**

```bash
bunx playwright test e2e/smoke.spec.ts --project=chromium --workers=1 -g "login page|submit login form"
```

Expected result: the new render, responsive and submit tests pass. If they fail, correct the implementation while preserving the test contract.

- [ ] **Step 5: Commit the page implementation**

```bash
git add "app/web/app/(auth)/login/page.tsx" "app/web/app/(auth)/layout.tsx"
git commit -m "feat: modernize login page"
```

### Task 3: Remove the old animation implementation

**Files:**
- Delete: `app/web/app/(auth)/login/_components/AnimatedTrianglesBackground.tsx`
- Modify: `app/web/tsconfig.json:22-29`

**Interfaces:**
- No runtime consumers remain after Task 2; the page must not import or render the removed component.

- [ ] **Step 1: Delete the unused triangle component**

Remove the component after confirming `rg -n "AnimatedTrianglesBackground|floatUp|animate-float" app/web` returns no login references.

- [ ] **Step 2: Remove the explicit stale TypeScript include**

Delete the `app/(auth)/login/_components/AnimatedTrianglesBackground.tsx` entry from `tsconfig.json`; the existing `**/*.tsx` include already covers source files.

- [ ] **Step 3: Verify no old implementation remains**

```bash
rg -n "AnimatedTrianglesBackground|floatUp|animate-float|Faca seu Login|Bem vindo de volta|Sign in|Email/User|Password" app/web/app/'(auth)' app/web/e2e/smoke.spec.ts
```

Expected result: no matches.

- [ ] **Step 4: Run typecheck**

```bash
bun run typecheck
```

Expected result: exit code 0 with no TypeScript errors.

- [ ] **Step 5: Commit cleanup**

```bash
git add app/web/app/'(auth)'/login/_components/AnimatedTrianglesBackground.tsx app/web/tsconfig.json
git commit -m "refactor: remove legacy login animation"
```

### Task 4: Verify the complete frontend and browser presentation

**Files:**
- Modify: none unless a verification failure identifies a regression.
- Test: `app/web/e2e/smoke.spec.ts`

- [ ] **Step 1: Run the complete login smoke tests**

```bash
bunx playwright test e2e/smoke.spec.ts --project=chromium --workers=1
```

Expected result: all auth, calendar and event smoke tests pass or retain their existing backend-dependent behavior without a new failure.

- [ ] **Step 2: Inspect the rendered page in the in-app browser**

Open `http://127.0.0.1:3000/login` with the running app and inspect desktop and 390×844 viewports. Confirm the brand panel, form card, focus states, Portuguese copy, no horizontal overflow and reduced-motion-safe presentation.

- [ ] **Step 3: Run frontend quality gates**

```bash
bun run lint
bun run typecheck
bun run build
bun run test:coverage
```

Expected result: all commands exit 0. Existing lint warnings may remain only if they are unrelated to the login page.

- [ ] **Step 4: Review the diff and working tree**

```bash
git diff --check
git status --short
```

Expected result: no whitespace errors and no generated browser report or screenshot changes unless intentionally added as a login regression artifact.
