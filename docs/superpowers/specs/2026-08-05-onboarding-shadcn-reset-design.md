# Onboarding UI and shadcn Primitive Reset — Design

**Date**: 2026-08-05  
**Status**: Approved

## Problem

The onboarding implementation follows the intended five-step flow but renders
incorrectly in the running application. The live browser reproduces three
independent defects:

1. `globals.css` exposes space-separated HSL channels as Tailwind v4 theme
   colors without wrapping them in a valid color function. Classes such as
   `bg-background`, `bg-primary`, `bg-input`, and `text-primary-foreground`
   therefore compute to transparent or invalid colors, especially under the
   system dark theme.
2. Shared primitives contain non-shadcn overrides. `Input` uses a fixed
   `w-100` width and `h-16`, and `Button`, `Textarea`, and `Card` add custom
   purple hover states, oversized controls, and heavier borders. The two-name
   onboarding row consequently overflows its card.
3. The E2E flow takes screenshots immediately after a step becomes visible,
   while Framer Motion is still animating its opacity. The screenshots can
   capture a half-transparent step even when the final layout is correct.

## Goals

- Restore shadcn's standard neutral/zinc color model for light and dark themes.
- Make shared onboarding primitives behave like the generated shadcn
  components: fluid width, compact standard heights, neutral borders, and
  predictable focus states.
- Keep Cabulous typography and the existing public UI contracts intact while
  removing non-standard color and sizing overrides from the primitives used by
  onboarding.
- Make the onboarding card responsive at desktop and mobile widths with no
  horizontal overflow.
- Preserve the five-step flow, upload previews, validation, animated
  transitions, and Portuguese copy from the approved onboarding spec.
- Add automated checks for the visual regressions and stable screenshot timing.

## Non-goals

- Redesigning the profile page, event pages, backend onboarding API, or login
  information architecture.
- Replacing Framer Motion or removing animation from the wizard.
- Introducing a new design system or adding a second theme layer.

## Design

### Theme reset

Run the shadcn initializer from `app/web` with the repository's existing
neutral base color and CSS-variable mode. Treat the generated `components.json`
and `globals.css` color mapping as the source of truth. Keep the existing
Poppins and Geist font variables, `tw-animate-css`, dark-mode selector, and
small project utilities only when they do not alter shadcn token semantics.

Theme variables must be complete CSS colors consumed by Tailwind v4, using the
same representation in `:root`, `.dark`, and `@theme inline`. Heading and
success tokens may remain as project aliases, but headings default to the
foreground token and success remains a valid foreground/background pair.

### Shared primitives

Normalize the primitives that are part of the onboarding surface:

- `Input`: retain the existing `error` and `startAdornment` API, but use
  `w-full`, a standard shadcn height, `bg-background`, `border-input`, and
  standard focus/error rings. Error text and the icon remain inline and
  accessible.
- `Textarea`: retain the `error` API and use the same neutral background,
  border, focus, and error treatment as `Input`.
- `Button`: restore the default shadcn variants and sizes. Preserve the
  project-specific `xl` size because login uses it, but remove the custom
  purple/scale behavior from default and outline variants.
- `Card`: restore standard neutral card, border, radius, spacing, and text
  tokens. Existing card subcomponents continue exporting the same names.
- `Avatar`: keep the Radix behavior and image fallback, but ensure the root and
  fallback use the normalized background/foreground tokens.

Other generated primitives are audited for the same invalid color or obvious
fixed-width overrides. Only files with a concrete regression are changed.

### Onboarding layout and behavior

- The route remains `/onboarding` and the server-side session guard remains in
  place.
- The page uses a full-viewport `bg-background` container and a responsive
  centered card with a bounded width. The card's content uses `min-w-0` and
  responsive one/two-column form layout so long labels and inputs cannot push
  outside the card.
- The progress component keeps the current step count and segmented progress,
  but uses standard theme tokens and a compact accessible label.
- File drop zones retain immediate blob previews and upload spinners. Object
  URLs are revoked when replaced or when the component unmounts, and upload
  failures are surfaced in the form instead of being silently ignored.
- The wizard keeps the animated step transition. The motion container exposes
  a stable `data-onboarding-step` hook so browser tests wait for opacity 1
  before taking screenshots.

### Verification

The frontend E2E suite will verify:

- the existing login-to-onboarding flow still completes;
- the first step has no horizontal document overflow at the desktop viewport;
- the input controls fit their card and the primary action has a non-
  transparent computed background;
- each captured step is fully opaque after its transition completes.

Manual browser verification will inspect the first, middle, and preview steps
at the running local application, including a mobile-width viewport check.

## Acceptance criteria

1. `globals.css` and `components.json` match a valid neutral/zinc shadcn setup.
2. The onboarding card is centered, opaque, and visually readable in light and
   dark system themes.
3. No onboarding control exceeds the card or viewport width at desktop or
   mobile widths.
4. Primary and outline buttons, inputs, textareas, cards, and avatars use
   visible standard shadcn styling without custom purple hover artifacts.
5. The five-step E2E flow completes and its screenshots are stable after
   animations.
6. Frontend lint, typecheck, build, and coverage commands pass.

