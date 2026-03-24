# hooks/ - Custom React Hooks

Reusable React hooks for shared logic across components.

## Structure

- All hooks at top level with kebab-case naming (e.g., `use-mobile.ts`, `use-theme.ts`)

## What Belongs Here

- ✅ Reusable React hooks
- ✅ Browser API wrappers (window, localStorage)
- ✅ State management patterns (UI state)
- ❌ Business logic (use Server Actions)
- ❌ API calls (use Server Actions)
- ❌ Component-specific logic (keep in component)

## Rules

1. Naming: `use-{name}.ts` (kebab-case files)
2. Export function: `use{Name}` (camelCase with 'use' prefix)
3. Mark as client component with `'use client'` if needed
4. Type all parameters and return values
5. Only create hooks used by 2+ components

## Common Patterns

- `use-theme.ts` — Dark/light mode switcher
- `use-clipboard.ts` — Copy to clipboard functionality
- `use-user.tsx` — Current user data (mocked for now, no workspaces)

## Forbidden

- ❌ Hooks used in only one place
- ❌ API calls to backend (use Server Actions)
- ❌ Business logic
- ❌ Naming without 'use' prefix
- ❌ Missing cleanup in useEffect
