# types/ - Type System

TypeScript type definitions and Zod validation schemas grouped by domain.

## Structure

- Root level — Shared type files
- Subdirectories — Domain-specific grouped types

## What Belongs Here

- ✅ Zod schemas for form validation
- ✅ TypeScript interfaces for API responses
- ✅ Type inference from Zod schemas
- ✅ Shared type definitions and enums
- ❌ Business logic or data fetching
- ❌ React components or hooks

## Rules

1. Group by domain (one file per feature area)
2. Use Zod for all form validation schemas
3. Export schema, inferred type, and response interface
4. Naming: PascalCase for all types (e.g., `UserResponse`)

## Forbidden

- ❌ Using `any` type (strive for unknown or actual types)
- ❌ Skipping validation for user inputs
- ❌ Duplicating types (use shared types)
- ❌ Business logic in type files
