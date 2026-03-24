# Frontend AGENTS.md

This document guides AI agents working on the **Cabulous Frontend** (`/app/web`).

## Directory Purpose

Next.js 16+ application for the Cabulous Site. Handles user administrative tasks and site management.

## Tech Stack

| Technology          | Version | Purpose                              |
| ------------------- | ------- | ------------------------------------ |
| **Next.js**         | 16+     | React framework with App Router      |
| **React**           | 19+     | UI library                           |
| **TypeScript**      | Latest  | Type safety                          |
| **Tailwind CSS**    | v4      | Utility-first styling                |
| **Radix UI**        | Latest  | Headless component primitives        |
| **Lucide React**    | Latest  | Icon library                         |
| **React Hook Form** | Latest  | Form state management                |
| **Zod**             | Latest  | Schema validation                    |
| **Bun**             | Latest  | Package manager (preferred over npm) |

## Directory Structure

```
app/web/
├── app/                    # Next.js App Router (pages & layouts)
│   └── (section)/          # Grouped pages
│       ├── _components/    # Page-exclusive components (optional)
│       └── page.tsx        # Page component
├── components/             # Reusable React components
│   ├── ui/                # Radix-based UI primitives
│   └── layout/            # Layout components
├── actions/                # Server actions grouped by domain
├── types/                  # TypeScript type definitions grouped by domain
├── lib/                    # Utilities and helpers
├── hooks/                  # Custom React hooks
└── public/                 # Static assets
```

## Core Architecture

### Component Pattern

- Server components by default
- Use `'use client'` only when interactivity needed
- Page-exclusive components in `app/(section)/_components/`
- Reusable components in `components/`

### Data Flow

- Server Actions for backend communication (no direct fetch in components)
- React Hook Form + Zod for form validation
- Key integration: `lib/api.ts` for backend communication

### Styling

- Tailwind utility classes only
- Theme colors from `@theme inline` in `globals.css`
- Dark mode via `.dark` class

## Critical Rules

1. **Type everything** → No `any` types
2. **Server-first** → Use server components by default
3. **Validate inputs** → Zod schemas for all forms
4. **Page-exclusive components** → Use `_components/` in page folder

## Environment Setup

Reference `.env.example` in the project root for required environment variables.

## Navigation to Subsystems

→ **[./components/AGENTS.md](./components/AGENTS.md)** — UI component patterns  
→ **[./actions/AGENTS.md](./actions/AGENTS.md)** — Server actions conventions  
→ **[./types/AGENTS.md](./types/AGENTS.md)** — Type system and Zod patterns  
→ **[./hooks/AGENTS.md](./hooks/AGENTS.md)** — Custom React hooks patterns  
→ **[./lib/AGENTS.md](./lib/AGENTS.md)** — Utilities and helpers layout
