
# Onboarding UI and shadcn Primitive Reset Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Restore valid neutral/zinc shadcn styling, fix the responsive onboarding layout, and verify the five-step flow visually and automatically.

**Architecture:** Use the shadcn initializer as the theme source of truth, then keep only Cabulous font and utility additions that do not change shadcn token semantics. Normalize the shared primitives used by onboarding while preserving their public props and existing login usage. Add browser-level visual contracts for color application, overflow, and stable animated screenshots.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS v4, shadcn/ui, Radix UI, Framer Motion, Playwright, Bun.

## Global Constraints

- Frontend commands run from app/web/ and use Bun.
- Use Tailwind utility classes only; do not add a separate CSS design system.
- Preserve server components by default and existing client boundaries.
- Keep Portuguese labels and the approved five-step onboarding flow.
- Preserve existing Input error/startAdornment APIs and the Button xl size.
- Do not edit generated API types or backend migrations.
- Do not revert the user's pending screenshot changes; inspect and regenerate them only through the verified E2E flow.
- Before completion run bun run lint, bun run typecheck, bun run build, and bun run test:coverage from app/web/.

---

## File Map

- Modify app/web/components.json: keep the generated neutral/zinc shadcn configuration.
- Modify app/web/app/globals.css: use valid Tailwind v4 theme colors and preserve approved font/utilities.
- Modify app/web/components/ui/input.tsx: restore fluid standard input styling while keeping error/adornment behavior.
- Modify app/web/components/ui/textarea.tsx: align textarea styling and error behavior with Input.
- Modify app/web/components/ui/button.tsx: restore standard shadcn variants and retain the existing xl size.
- Modify app/web/components/ui/card.tsx: restore standard card tokens without changing exports.
- Modify app/web/components/ui/avatar.tsx: normalize fallback/root tokens without changing Radix behavior.
- Modify app/web/app/(onboarding)/onboarding/_components/OnboardingWizard.tsx: expose a stable animated-step hook and keep the card responsive.
- Modify app/web/app/(onboarding)/onboarding/_components/OnboardingProgress.tsx: use standard tokens and an accessible progress label.
- Modify app/web/app/(onboarding)/onboarding/_components/StepProfile.tsx: prevent form-row overflow and surface upload failures while preserving immediate previews.
- Modify app/web/e2e/onboarding.spec.ts: add failing visual contracts, wait for transition completion, and capture stable screenshots.

---

### Task 1: Add the failing visual regression contract

**Files:**
- Modify: app/web/e2e/onboarding.spec.ts

**Interfaces:**
- Consumes: Existing login-to-onboarding E2E flow.
- Produces: Assertions that onboarding has no horizontal overflow, the primary action has a visible background, and each animated step exposes a stable test hook.

- [ ] Step 1: Add assertions before changing production code

After the onboarding URL assertion and before filling the first step, add:

```ts
const stepSurface = page.locator('[data-onboarding-step]')
await expect(stepSurface).toHaveCSS('opacity', '1')

const hasHorizontalOverflow = await page.evaluate(
  () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
)
expect(hasHorizontalOverflow).toBe(true)

const primaryBackground = await page.getByRole('button', { name: 'Continuar' }).first().evaluate(
  (element) => getComputedStyle(element).backgroundColor,
)
expect(primaryBackground).not.toBe('rgba(0, 0, 0, 0)')
```

Add the same opacity assertion after every step transition and before its screenshot. Keep the existing submission and redirect assertions.

- [ ] Step 2: Run the focused E2E test and verify it fails for the current defect

Run from app/web/:

```bash
bunx playwright test e2e/onboarding.spec.ts --project=chromium --workers=1
```

Expected: FAIL because the data hook is missing and/or the current fixed-width input and invalid theme produce the overflow/transparent-background assertions.

- [ ] Step 3: Commit the red test

```bash
git add app/web/e2e/onboarding.spec.ts
git commit -m "test: capture onboarding visual regressions"
```

---

### Task 2: Reset the shadcn theme source of truth

**Files:**
- Modify: app/web/components.json
- Modify: app/web/app/globals.css

**Interfaces:**
- Consumes: Existing Next font variables, ThemeProvider, and Tailwind v4 setup.
- Produces: Valid light/dark neutral theme tokens consumed by background, text, border, and ring utilities.

- [ ] Step 1: Run the supported shadcn initializer

From app/web/, run:

```bash
bunx shadcn@latest init --defaults --force
```

Review the resulting diff immediately. Keep the generated neutral/zinc CSS-variable configuration and do not allow unrelated dependencies or routes to change.

- [ ] Step 2: Restore only project-safe additions

Use apply_patch to keep the generated shadcn color mapping and retain only the Tailwind imports, tw-animate-css, dark selector, Poppins/Geist variables, and small utilities that do not alter token semantics. Theme variables must be complete CSS colors; do not expose space-separated HSL channels directly to Tailwind v4.

- [ ] Step 3: Verify the theme compiles before changing primitives

Run:

```bash
bun run typecheck
```

Reload the running app and confirm through the browser that background, card, and primary utilities have non-transparent computed colors on /onboarding.

- [ ] Step 4: Commit the theme reset

```bash
git add app/web/components.json app/web/app/globals.css
git commit -m "chore: restore vanilla shadcn theme tokens"
```

---

### Task 3: Normalize shared shadcn primitives

**Files:**
- Modify: app/web/components/ui/input.tsx
- Modify: app/web/components/ui/textarea.tsx
- Modify: app/web/components/ui/button.tsx
- Modify: app/web/components/ui/card.tsx
- Modify: app/web/components/ui/avatar.tsx

**Interfaces:**
- Consumes: Valid theme tokens from Task 2.
- Produces: Existing component exports and props with standard fluid sizing, neutral surfaces, visible primary actions, and consistent focus/error states.

- [ ] Step 1: Replace Input fixed sizing and custom colors

Keep the wrapper, error, startAdornment, and error icon. The native input must be fluid with standard height and use background, border, focus, disabled, placeholder, and invalid tokens. Remove w-100, h-16, purple hover classes, and hover rings. Preserve password minLength and required behavior.

- [ ] Step 2: Align Textarea with Input

Keep the error prop and wrapper. Use a fluid min-height, full-width rounded border, background surface, standard placeholder/focus/disabled/invalid classes, and no custom primary-focus overrides.

- [ ] Step 3: Restore Button variants while preserving compatibility

Use shadcn standard base and variant classes for default, destructive, outline, secondary, ghost, and link. Preserve icebreaker if any consumer imports it, mapping it to a standard background/hover treatment. Keep the existing xl size entry because login uses it. Remove custom purple hover and active scaling from default and outline.

- [ ] Step 4: Normalize Card and Avatar tokens

Keep all Card exports and Radix Avatar behavior. Card uses valid card surface, foreground, border, radius, spacing, and shadow tokens. Avatar uses valid muted fallback tokens with unchanged sizing and image behavior.

- [ ] Step 5: Run focused static checks

```bash
bun run lint
bun run typecheck
```

Expected: both pass with no new errors.

- [ ] Step 6: Commit normalized primitives

```bash
git add app/web/components/ui/input.tsx app/web/components/ui/textarea.tsx app/web/components/ui/button.tsx app/web/components/ui/card.tsx app/web/components/ui/avatar.tsx
git commit -m "fix: normalize shared shadcn primitives"
```

---

### Task 4: Fix onboarding layout, progress, animation, and upload debt

**Files:**
- Modify: app/web/app/(onboarding)/onboarding/_components/OnboardingWizard.tsx
- Modify: app/web/app/(onboarding)/onboarding/_components/OnboardingProgress.tsx
- Modify: app/web/app/(onboarding)/onboarding/_components/StepProfile.tsx
- Modify: app/web/e2e/onboarding.spec.ts

**Interfaces:**
- Consumes: Normalized primitives and existing form/upload actions.
- Produces: Responsive onboarding card, stable data-onboarding-step hook, accessible progress state, immediate previews, revoked blob URLs, and visible upload errors.

- [ ] Step 1: Add the stable motion hook and responsive card classes

On the animated step wrapper, add data-onboarding-step and keep the Framer Motion transition. Use a full-width bounded card with min-w-0, rounded border, card background, padding, and shadow. The outer layout must include min-h-svh, full width, background, horizontal padding, and vertical breathing room.

- [ ] Step 2: Make the progress indicator accessible and neutral

Keep segmented progress bars and current step count, add an aria-label describing the current step, and use standard primary/muted tokens only. Do not change the five-step API.

- [ ] Step 3: Prevent StepProfile row overflow

Change the name fields to a responsive grid with min-w-0, one column by default and two columns from the small breakpoint. Keep full-width field wrappers and existing validation triggers.

- [ ] Step 4: Surface upload errors and revoke preview URLs

Use setError/clearErrors from useFormContext for upload failures, clear the matching key when an upload fails, revoke the previous object URL before replacing it, and revoke both current preview URLs in effect cleanup. Keep immediate previews and loading spinners.

- [ ] Step 5: Run the focused E2E test and verify green

```bash
bunx playwright test e2e/onboarding.spec.ts --project=chromium --workers=1
```

Expected: the existing flow completes, visual contracts pass, and screenshots are taken only after opacity reaches 1.

- [ ] Step 6: Commit onboarding corrections

```bash
git add app/web/app/(onboarding)/onboarding/_components/OnboardingWizard.tsx app/web/app/(onboarding)/onboarding/_components/OnboardingProgress.tsx app/web/app/(onboarding)/onboarding/_components/StepProfile.tsx app/web/e2e/onboarding.spec.ts
git commit -m "fix: make onboarding layout responsive and testable"
```

---

### Task 5: Verify the application visually and run the quality gate

**Files:**
- No source files unless browser inspection finds a targeted defect.

**Interfaces:**
- Consumes: Running service stack and Next.js app.
- Produces: Fresh desktop/mobile browser evidence and a clean frontend quality result.

- [ ] Step 1: Inspect the first step at desktop width

Use the in-app browser at http://localhost:3000/onboarding, wait for opacity 1, and capture the first-step screenshot. Verify centered opaque card and no horizontal scrolling.

- [ ] Step 2: Walk through middle and preview states

Fill required fields, advance through Bio, Contact, Password, and Preview, and capture Bio and Preview after transitions settle. Confirm primary/outline controls, textarea, preview card, and progress colors are visible.

- [ ] Step 3: Check mobile breakpoint

Set a narrow mobile viewport, reload /onboarding, and verify name fields stack, card stays within viewport, and buttons remain reachable. Reset the viewport afterward.

- [ ] Step 4: Run complete frontend quality

From app/web/ run:

```bash
bun run lint
bun run typecheck
bun run build
bun run test:coverage
```

Expected: all commands exit 0. If a command fails, return to the relevant task, make one focused fix, and rerun the complete affected command.

- [ ] Step 5: Inspect final diff and working tree

```bash
git diff --check
git status --short
git log --oneline --decorate -8
```

Confirm only intended source/docs changes plus already-present screenshot artifacts remain. Do not claim completion until verification output is fresh and clean.

