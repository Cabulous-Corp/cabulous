# components/ - UI Component System

Reusable React components built with Radix UI primitives and Tailwind CSS.

## Structure

- `ui/` — Wrapped Radix primitives (kebab-case files)
- `layout/` — Page layout components used across multiple pages (PascalCase files)
- Root level — Feature components used in 2+ locations (kebab-case files)
- Page-exclusive components go in `app/(section)/_components/`, not here

## What Belongs Here

- ✅ Reusable UI components (buttons, dialogs, accordions, cards, inputs)
- ✅ Layout components (headers, sidebars, breadcrumbs)
- ✅ Wrapped Radix primitives with Tailwind styling
- ❌ Page-exclusive components (use `_components/` in page folder)
- ❌ Business logic or API calls (use Server Actions)

## Rules

1. Always type props with TypeScript interfaces
2. Mark client components with `'use client'` only if needed
3. Use Tailwind classes from `@theme inline` (e.g., `bg-destructive`, `text-success`)
4. Avoid nested interactive elements — use Radix `asChild` prop
5. Use skeleton animations for loading states
6. All imports from Radix, lucide-react allowed

## Forbidden

- ❌ CSS-in-JS (emotion, styled-components)
- ❌ Direct API calls (use server actions)
- ❌ Business logic in components
- ❌ Nested buttons (causes hydration errors)
- ❌ Untyped props (`any`)

## Accessibility

- Semantic HTML (`<button>`, `<nav>`, `<main>`)
- Label-to-input: `htmlFor`/`id` pairs
- ARIA labels where needed
- Keyboard navigation (Radix handles most)
