# lib/ - Utilities and Helpers

Helper functions and utilities grouped by functionality.

## Structure

- `api.ts` — Backend API client with authentication (ky-based)
- `config.ts` — Environment variables and app configuration
- `date.ts` — Date formatting (pt-BR only)
- `string.ts` — String manipulation
- `logger.ts` — Logging utilities
- `json.ts` — Safe JSON parsing

## What Belongs Here

- ✅ Pure utility functions (no React hooks)
- ✅ Data formatters and parsers
- ✅ Validation helpers
- ✅ API client configuration
- ✅ Shared constants and configs
- ❌ React components or hooks
- ❌ Business logic (use Server Actions)

## Rules

1. One file per utility category (e.g., `date.ts`, `string.ts`)
2. Export pure functions only (no side effects)
3. Type all parameters and return values
4. Group related functions in same file
5. Use descriptive function names (e.g., `formatCurrency`, `validateEmail`)

## Key Files

### `api.ts`

Backend API client using `ky` with:

- Authentication via session cookies
- Automatic logging
- Tracing context forwarding

### `config.ts`

Environment variables:

- `serverUrl` — Backend API URL
- `cookieName` — Session cookie name

## Forbidden

- ❌ React hooks (belongs in `hooks/`)
- ❌ Components (belongs in `components/`)
- ❌ Domain-heavy business logic (use Server Actions)
