# actions/ - Server Actions

Async functions that execute on the server, called directly from components and forms.

## Structure

- Root level — Domain-specific action files
- Subdirectories — Grouped related actions

## What Belongs Here

- ✅ Backend API calls via `api` from `@/lib/api`
- ✅ Server-side data fetching and mutations
- ✅ Input validation with Zod schemas
- ✅ Cache revalidation (`revalidatePath`, `revalidateTag`)
- ❌ Client-side logic or state management
- ❌ Direct fetch() calls (use `api` helper from @/lib/api)

## Rules

1. Start every file with `'use server'` directive
2. Group by domain (one file per feature area)
3. Use `api` from `@/lib/api` for all backend calls
4. Handle errors appropriately, return clean error objects
5. Revalidate cache when mutating data (`revalidatePath`, `revalidateTag`)

## Forbidden

- ❌ Client-side hooks (useState, useEffect)
- ❌ Browser APIs (localStorage, window, document)
- ❌ Direct fetch() (use `api` from @/lib/api)
- ❌ Missing error handling
