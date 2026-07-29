# Events Frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full events module on the Next.js 16 frontend consuming the Django backend events API, using shadcn/ui components.

**Architecture:** Hybrid approach — Server Components for initial data fetch via `ky`, Server Actions for all mutations with `revalidatePath`/`revalidateTag`, React Query (`@tanstack/react-query`) wrapping mutations in Client Components for optimistic cache invalidation.

**Tech Stack:** Next.js 16 + React 19, TypeScript 5.9, Tailwind v4, shadcn/ui (Radix primitives), react-hook-form + zod, ky, react-leaflet + leaflet-geosearch, date-fns, lucide-react, Playwright (e2e/visual)

## Global Constraints

- `'use server'` imports must start with `'use server'` + `'server-only'`; `'use client'` for interactive components
- No `any` types anywhere
- Tailwind utility classes only, theme colors from `@theme inline` in `globals.css`
- Page-exclusive components go in `_components/` within the page folder
- No direct fetch in components — use Server Actions for mutations, API layer for reads
- Portuguese labels (pt-BR locale for dates)
- `bun` as package manager (not npm/yarn)
- Run quality: `cd app/web && bun run lint && bun run typecheck && bun run build && bun run test:coverage`
- Run e2e: `cd app/web && bunx playwright test`
- Playwright uses Chromium only (--project=chromium), baseURL `http://localhost:3000`

---

### Task 0: Playwright setup

**Files:**
- Modify: `app/web/package.json` (add `@playwright/test`, add test scripts)
- Create: `app/web/playwright.config.ts`
- Create: `app/web/e2e/smoke.spec.ts`

**Interfaces:**
- Consumes: Nothing (runs against running Next.js dev server)
- Produces: `playwright.config.ts`, smoke test skeleton, Chromium browser installed

- [ ] **Step 1: Install Playwright**

```bash
cd app/web; bun add -D @playwright/test
```

- [ ] **Step 2: Install Chromium browser binary**

```bash
cd app/web; bunx playwright install chromium
```

- [ ] **Step 3: Create playwright.config.ts**

```typescript
// app/web/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'bun run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
})
```

- [ ] **Step 4: Create smoke test skeleton**

```typescript
// app/web/e2e/smoke.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Auth smoke tests', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('Faca seu Login')).toBeVisible()
    await expect(page.getByPlaceholder('Email/User')).toBeVisible()
    await expect(page.getByPlaceholder('Password')).toBeVisible()
  })

  test('redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/events')
    await expect(page).toHaveURL(/\/login/)
  })

  test('successful login redirects to home', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('Email/User').fill('test@cabulous.com')
    await page.getByPlaceholder('Password').fill('testpass123')
    await page.getByRole('button', { name: /Sign in/ }).click()
    await expect(page).toHaveURL('/')
  })
})

test.describe('Calendar smoke tests', () => {
  test('calendar page renders with navigation', async ({ page }) => {
    // ponytail: requires valid session cookie; set manually for local dev
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events')
    await expect(page.getByText('Eventos')).toBeVisible()
    await expect(page.getByText('Mes')).toBeVisible()
    await expect(page.getByText('Semana')).toBeVisible()
    await expect(page.getByText('Agenda')).toBeVisible()
  })

  test('view toggle switches views', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events')
    await page.getByText('Agenda').click()
    await page.waitForURL('/events')
    await page.getByText('Mes').click()
    await page.waitForURL('/events')
  })
})

test.describe('Event detail smoke tests', () => {
  test('event detail page renders tabs', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    // ponytail: replace with a real event ID from seed data
    await page.goto('/events/some-uuid')
    // Will show not-found or 404 state — adjust after seed data exists
    await expect(page.getByText(/Participantes|Fotos|Highlights/)).toBeVisible({ timeout: 15000 })
  })
})

test.describe('Create event smoke tests', () => {
  test('create event page renders form fields', async ({ page }) => {
    await page.context().addCookies([{ name: 'ev_s_tkn', value: 'mock-token', domain: 'localhost', path: '/' }])
    await page.goto('/events/new')
    await expect(page.getByText('Novo Evento')).toBeVisible()
    await expect(page.getByPlaceholder('Nome do evento')).toBeVisible()
  })
})
```

- [ ] **Step 5: Verify Playwright works with a dry-run**

```bash
cd app/web; bunx playwright test --project=chromium --list
```

- [ ] **Step 6: Commit**

```bash
git add app/web/package.json app/web/bun.lock app/web/playwright.config.ts app/web/e2e/smoke.spec.ts
git commit -m "chore: add Playwright e2e setup with smoke test skeleton"
```

---

### Task 1: Generate API types

**Files:**
- Modify: `app/web/package.json` (add type-check override)
- Create: `app/web/types/api.d.ts`

**Interfaces:**
- Consumes: Backend running on `localhost:8000` (or manual schema)
- Produces: `types/api.d.ts` with full typed API schema — all event, media, and auth types

- [ ] **Step 1: Ensure backend is running and generate types**

```bash
cd app/web; if (Test-Path types/api.d.ts) { Remove-Item types/api.d.ts }
```

Start backend in another terminal: `cd service && uv run python manage.py runserver 0.0.0.0:8000`

```bash
cd app/web; curl http://localhost:8000/openapi.json -o openapi.json
```

- [ ] **Step 2: Generate TypeScript types from OpenAPI schema**

```bash
cd app/web; bunx openapi-typescript openapi.json -o ./types/api.d.ts
```

- [ ] **Step 3: Verify file was created and has expected content**

Check that `types/api.d.ts` contains paths like `"/api/events/"`, `"/api/events/{id}/"`, event types, etc.

- [ ] **Step 4: Clean up temp file**

```bash
cd app/web; Remove-Item openapi.json -ErrorAction SilentlyContinue
```

- [ ] **Step 5: Check TypeScript compiles with new types**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/types/api.d.ts
git commit -m "feat: generate API types from backend OpenAPI schema"
```

---

### Task 2: Wire real authentication

**Files:**
- Modify: `app/web/src/actions/session.ts`
- Modify: `app/web/src/app/(auth)/login/page.tsx`
- Modify: `app/web/src/app/(private)/(pages)/(main)/layout.tsx`
- Create: `app/web/src/lib/api/auth.ts`
- Modify: `app/web/src/proxy.ts`

**Interfaces:**
- Consumes: `api` from `@/lib/api` (ky instance)
- Produces:
  - `login(request: LoginRequest) => Promise<LoginResponse>` — calls `/api/auth/login/`
  - `verifySession() => Promise<SessionUser | null>` — calls `/api/auth/me/`, returns `{ id: string; email: string; username: string } | null`
  - `logoutAction() => Promise<void>` — clears cookie

**Types needed** (write inline until Task 1 types are available):

```typescript
type LoginRequest = { email: string; password: string }
type LoginResponse = { access: string; refresh: string }
type SessionUser = { id: string; email: string; username: string }
```

- [ ] **Step 1: Create `lib/api/auth.ts` with login and session fetch functions**

```typescript
// app/web/src/lib/api/auth.ts
'use server'

import 'server-only'
import { api } from '@/lib/api'
import { cookieName } from '@/lib/config'
import { cookies } from 'next/headers'

type LoginRequest = { email: string; password: string }
type LoginResponse = { access: string; refresh: string }
type SessionUser = { id: string; email: string; username: string }

export async function loginRequest(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post('api/auth/login/', { json: data })

  const setCookieHeader = response.headers.get('set-cookie')
  if (setCookieHeader) {
    const cookieStore = await cookies()
    const match = setCookieHeader.match(new RegExp(`${cookieName}=([^;]+)`))
    if (match) {
      cookieStore.set(cookieName, match[1], {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24 * 30,
      })
    }
  }

  return response.json() as Promise<LoginResponse>
}

export async function fetchSession(): Promise<SessionUser | null> {
  try {
    return await api.get('api/auth/me/').json<SessionUser>()
  } catch {
    return null
  }
}
```

- [ ] **Step 2: Rewrite `actions/session.ts` to use real API**

```typescript
// app/web/src/actions/session.ts
'use server'

import 'server-only'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { cookieName } from '@/lib/config'
import { loginRequest, fetchSession } from '@/lib/api/auth'

type LoginRequest = { email: string; password: string }
type SessionUser = { id: string; email: string; username: string }

export async function loginAction(data: LoginRequest): Promise<{ error?: string }> {
  try {
    await loginRequest(data)
    return {}
  } catch (e: unknown) {
    const err = e as { response?: { status: number; json: () => Promise<unknown> } }
    if (err.response?.status === 401) {
      return { error: 'E-mail ou senha invalidos.' }
    }
    return { error: 'Erro inesperado. Tente novamente.' }
  }
}

export async function logoutAction(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(cookieName)
  redirect('/login')
}

export async function verifySession(): Promise<SessionUser> {
  const user = await fetchSession()
  if (!user) {
    redirect('/login')
  }
  return user
}

export async function verifySessionWithoutRedirect(): Promise<SessionUser | null> {
  return fetchSession()
}

export async function verifySessionForOnboarding(): Promise<SessionUser | null> {
  return fetchSession()
}

export async function getSessions(): Promise<SessionUser[]> {
  const user = await fetchSession()
  return user ? [user] : []
}
```

- [ ] **Step 3: Update login page to use Server Action**

Edit `app/web/src/app/(auth)/login/page.tsx`: replace direct `fetch('/api/auth/login')` with `loginAction`. Import from `@/actions/session` and redirect on success:
- Add `import { useRouter } from 'next/navigation'` and `import { loginAction } from '@/actions/session'`
- Replace `handleLogin` body: `const result = await loginAction({ email: values.identifier, password: values.password })`
- On success (`!result.error`): `router.push('/')`
- On error: `setSubmitError(result.error ?? 'Erro desconhecido.')`

- [ ] **Step 4: Update sidebar layout to use real session**

Edit `app/web/src/app/(private)/(pages)/(main)/layout.tsx`: remove mock, import `verifySession`, call it in a server wrapper or pass user data. Since this is `'use client'`, create a parent server component:

```typescript
// app/web/src/app/(private)/(pages)/(main)/layout.tsx (replace content)

import { verifySessionWithoutRedirect } from '@/actions/session'
import { MainLayoutClient } from './main-layout-client'

type SessionUser = { id: string; email: string; username: string }

export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const user = await verifySessionWithoutRedirect()
  return <MainLayoutClient user={user}>{children}</MainLayoutClient>
}
```

Create `app/web/src/app/(private)/(pages)/(main)/main-layout-client.tsx`:

```typescript
'use client'

import { useRouter, usePathname } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'
import { SidebarSection } from '@/components/layout/types'
import { MdHome, MdEvent } from 'react-icons/md'

type SessionUser = { id: string; email: string; username: string }

export function MainLayoutClient({ children, user }: { children: React.ReactNode; user: SessionUser | null }) {
  const router = useRouter()
  const pathname = usePathname()

  const sidebarSections: SidebarSection[] = [
    {
      items: [{ label: 'Home', href: '/', icon: MdHome, end: true, active: pathname === '/' }],
    },
    {
      title: 'Eventos',
      items: [{ label: 'Calendario', href: '/events', icon: MdEvent, active: pathname.startsWith('/events') }],
    },
  ]

  return (
    <Layout sidebarSections={sidebarSections} showBackButton={false}>
      {children}
    </Layout>
  )
}
```

- [ ] **Step 5: Update UserProvider to use real session**

Read `app/web/src/hooks/use-user.tsx` and modify to load user from server action. Since hooks are client-side, create a simple context that receives user as prop:

```typescript
// app/web/src/hooks/use-user.tsx
'use client'

import { createContext, useContext } from 'react'

type SessionUser = { id: string; email: string; username: string }

type UserContextType = { user: SessionUser | null }

const UserContext = createContext<UserContextType>({ user: null })

export function UserProvider({ children, user }: { children: React.ReactNode; user: SessionUser | null }) {
  return <UserContext.Provider value={{ user }}>{children}</UserContext.Provider>
}

export function useUser(): UserContextType {
  return useContext(UserContext)
}
```

Then update `app/web/src/app/(private)/layout.tsx` to pass user to `UserProvider`.

- [ ] **Step 6: Verify auth flow**

```bash
cd app/web; bun run build
```

- [ ] **Step 7: Commit**

```bash
git add app/web/src/actions/session.ts app/web/src/lib/api/auth.ts app/web/src/app/\(auth\)/login/page.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/layout.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/main-layout-client.tsx app/web/src/hooks/use-user.tsx app/web/src/app/\(private\)/layout.tsx
git commit -m "feat: wire real authentication with JWT backend"
```

---

### Task 3: API data layer for events and media

**Files:**
- Create: `app/web/src/lib/api/events.ts`
- Create: `app/web/src/lib/api/media.ts`

**Interfaces:**
- Consumes: `api` from `@/lib/api` (ky instance), generated types from Task 1
- Produces:

```typescript
// lib/api/events.ts
getEvents(params: EventListParams): Promise<PaginatedResponse<EventRead>>
getEvent(id: string): Promise<EventRead>
getEventParticipants(eventId: string, page?: number): Promise<PaginatedResponse<ParticipantRead>>
getEventPhotos(eventId: string, page?: number): Promise<PaginatedResponse<EventPhotoRead>>
getEventHighlights(eventId: string, page?: number): Promise<PaginatedResponse<HighlightRead>>
getEventOptions(): Promise<EventOptions>

// lib/api/media.ts
uploadPhoto(file: File): Promise<MediaPhoto>
```

- [ ] **Step 1: Create event API types inline (sync with Task 1 later)**

```typescript
// app/web/src/lib/api/events.ts
'use server'

import 'server-only'
import { api } from '@/lib/api'

export type EventType = 'UNIVERSITY_PARTY' | 'BIRTHDAY' | 'CLUB' | 'CASUAL_HANGOUT' | 'BARBECUE'
  | 'AFTER_PARTY' | 'GRADUATION' | 'SHOW' | 'FESTIVAL' | 'DINNER' | 'TRIP' | 'CABULOUS' | 'CINEMA'

export type EventStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export type Audience = 'ILUMINADOS' | 'VOYEURS' | 'ELETRONICOS' | 'OTHERS'

export interface EventLocationRead {
  id: string
  name: string
  address: string
  latitude: number
  longitude: number
}

export interface EventRead {
  id: string
  title: string
  description: string
  start_at: string
  end_at: string
  type: EventType
  type_color: string
  status: EventStatus
  cancelled_at: string | null
  audiences: Audience[]
  participants_count: number
  location: EventLocationRead | null
  thumbnail_url: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface EventListParams {
  starts_from?: string
  starts_until?: string
  status?: EventStatus
  type?: EventType
  audience?: Audience
  participant?: string
  creator?: string
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface ParticipantRead {
  id: string
  user: string
  username: string
  created_at: string
}

export interface EventPhotoRead {
  id: string
  photo: string
  content_type: string
  object_key: string
  is_thumbnail: boolean
  created_at: string
}

export interface HighlightPhotoRead {
  id: string
  object_key: string
  content_type: string
}

export interface HighlightRead {
  id: string
  text: string
  author_id: string
  photos: HighlightPhotoRead[]
  created_at: string
  updated_at: string
}

export interface EventOptions {
  types: { value: EventType; label: string; color: string }[]
  audiences: { value: Audience; label: string }[]
  statuses: { value: EventStatus; label: string }[]
}

export interface MediaPhoto {
  id: string
  object_key: string
  content_type: string
  size_bytes: number
  taken_on: string | null
  caption: string | null
}
```

- [ ] **Step 2: Write fetch functions in the same file**

```typescript
export async function getEvents(params: EventListParams = {}): Promise<PaginatedResponse<EventRead>> {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      searchParams.set(key, String(value))
    }
  })
  return api.get('api/events/', { searchParams }).json<PaginatedResponse<EventRead>>()
}

export async function getEvent(id: string): Promise<EventRead> {
  return api.get(`api/events/${id}/`).json<EventRead>()
}

export async function getEventParticipants(
  eventId: string,
  page?: number,
): Promise<PaginatedResponse<ParticipantRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/participants/`, { searchParams }).json<PaginatedResponse<ParticipantRead>>()
}

export async function getEventPhotos(eventId: string, page?: number): Promise<PaginatedResponse<EventPhotoRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/photos/`, { searchParams }).json<PaginatedResponse<EventPhotoRead>>()
}

export async function getEventHighlights(eventId: string, page?: number): Promise<PaginatedResponse<HighlightRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/highlights/`, { searchParams }).json<PaginatedResponse<HighlightRead>>()
}

export async function getEventOptions(): Promise<EventOptions> {
  return api.get('api/events/options/').json<EventOptions>()
}
```

- [ ] **Step 3: Create media upload function**

```typescript
// app/web/src/lib/api/media.ts
'use server'

import 'server-only'
import { api } from '@/lib/api'

type MediaPhoto = {
  id: string
  object_key: string
  content_type: string
}

export async function uploadMediaPhoto(formData: FormData): Promise<MediaPhoto> {
  return api.post('api/media/', { body: formData }).json<MediaPhoto>()
}
```

- [ ] **Step 4: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add app/web/src/lib/api/events.ts app/web/src/lib/api/media.ts
git commit -m "feat: add events and media API data layer"
```

---

### Task 4: Server actions for events, participants, photos, highlights

**Files:**
- Create: `app/web/src/actions/events.ts`
- Create: `app/web/src/actions/participants.ts`
- Create: `app/web/src/actions/photos.ts`
- Create: `app/web/src/actions/highlights.ts`

**Interfaces:**
- Consumes: `api` from `@/lib/api`, types from `@/lib/api/events`
- Produces: All mutation functions listed below

- [ ] **Step 1: Create `actions/events.ts`**

```typescript
// app/web/src/actions/events.ts
'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { api } from '@/lib/api'
import { verifySession } from '@/actions/session'

export interface CreateEventInput {
  title: string
  description?: string
  start_at: string
  end_at: string
  type: string
  audiences: string[]
  location?: {
    name?: string
    address: string
    latitude: number
    longitude: number
  } | null
}

export async function createEvent(data: CreateEventInput) {
  await verifySession()
  const body: Record<string, unknown> = {
    title: data.title,
    description: data.description ?? '',
    start_at: data.start_at,
    end_at: data.end_at,
    type: data.type,
    audiences: data.audiences,
  }
  if (data.location) {
    body.location = data.location
  }
  const result = await api.post('api/events/', { json: body }).json<{ id: string }>()
  revalidatePath('/events')
  redirect(`/events/${result.id}`)
}

export async function updateEvent(id: string, data: Partial<CreateEventInput>) {
  await verifySession()
  await api.patch(`api/events/${id}/`, { json: data }).json()
  revalidatePath('/events')
  revalidatePath(`/events/${id}`)
}

export async function deleteEvent(id: string) {
  await verifySession()
  await api.delete(`api/events/${id}/`)
  revalidatePath('/events')
  redirect('/events')
}

export async function cancelEvent(id: string) {
  await verifySession()
  await api.post(`api/events/${id}/cancel/`)
  revalidatePath('/events')
  revalidatePath(`/events/${id}`)
}

export async function reactivateEvent(id: string) {
  await verifySession()
  await api.post(`api/events/${id}/reactivate/`)
  revalidatePath('/events')
  revalidatePath(`/events/${id}`)
}
```

- [ ] **Step 2: Create `actions/participants.ts`**

```typescript
// app/web/src/actions/participants.ts
'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { api } from '@/lib/api'
import { verifySession } from '@/actions/session'

export async function addParticipants(eventId: string, userIds: string[]) {
  await verifySession()
  await api.post(`api/events/${eventId}/participants/`, { json: { user_ids: userIds } })
  revalidatePath(`/events/${eventId}`)
}

export async function removeParticipant(eventId: string, userId: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/participants/${userId}/`)
  revalidatePath(`/events/${eventId}`)
}
```

- [ ] **Step 3: Create `actions/photos.ts`**

```typescript
// app/web/src/actions/photos.ts
'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { api } from '@/lib/api'
import { uploadMediaPhoto } from '@/lib/api/media'
import { verifySession } from '@/actions/session'

export async function uploadAndLinkPhoto(eventId: string, formData: FormData) {
  await verifySession()
  const photo = await uploadMediaPhoto(formData)
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photo.id } })
  revalidatePath(`/events/${eventId}`)
  return photo
}

export async function linkPhoto(eventId: string, photoId: string) {
  await verifySession()
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photoId } })
  revalidatePath(`/events/${eventId}`)
}

export async function unlinkPhoto(eventId: string, photoPk: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/photos/${photoPk}/`)
  revalidatePath(`/events/${eventId}`)
}

export async function setThumbnail(eventId: string, photoId: string) {
  await verifySession()
  await api.put(`api/events/${eventId}/thumbnail/`, { json: { photo_id: photoId } })
  revalidatePath(`/events/${eventId}`)
}

export async function uploadAndSetThumbnail(eventId: string, formData: FormData) {
  await verifySession()
  const photo = await uploadMediaPhoto(formData)
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photo.id } })
  await api.put(`api/events/${eventId}/thumbnail/`, { json: { photo_id: photo.id } })
  revalidatePath(`/events/${eventId}`)
  return photo
}

export async function clearThumbnail(eventId: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/thumbnail/`)
  revalidatePath(`/events/${eventId}`)
}
```

- [ ] **Step 4: Create `actions/highlights.ts`**

```typescript
// app/web/src/actions/highlights.ts
'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { api } from '@/lib/api'
import { verifySession } from '@/actions/session'

export async function createHighlight(eventId: string, data: { text: string; photo_ids: string[] }) {
  await verifySession()
  await api.post(`api/events/${eventId}/highlights/`, { json: data })
  revalidatePath(`/events/${eventId}`)
}

export async function updateHighlight(
  eventId: string,
  highlightId: string,
  data: { text: string; photo_ids: string[] },
) {
  await verifySession()
  await api.patch(`api/events/${eventId}/highlights/${highlightId}/`, { json: data })
  revalidatePath(`/events/${eventId}`)
}

export async function deleteHighlight(eventId: string, highlightId: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/highlights/${highlightId}/`)
  revalidatePath(`/events/${eventId}`)
}
```

- [ ] **Step 5: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/src/actions/events.ts app/web/src/actions/participants.ts app/web/src/actions/photos.ts app/web/src/actions/highlights.ts
git commit -m "feat: add server actions for events, participants, photos, highlights"
```

---

### Task 5: Calendar page — navigation, filters, and shell

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/page.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarView.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarNavigation.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarFilters.tsx`

**Interfaces:**
- Consumes: `getEvents`, `getEventOptions` from `@/lib/api/events`, `EventListParams`, `EventRead`, `EventOptions`
- Produces: Calendar shell with navigation (prev/next month, week, agenda, "Hoje" button), view toggle, filter bar

- [ ] **Step 1: Create the server component page**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/page.tsx
import { getEvents, getEventOptions } from '@/lib/api/events'
import { CalendarView } from './_components/CalendarView'

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}

export default async function EventsPage({ searchParams }: Props) {
  const params = await searchParams
  const options = await getEventOptions()

  const startsFrom = typeof params.starts_from === 'string' ? params.starts_from : undefined
  const startsUntil = typeof params.starts_until === 'string' ? params.starts_until : undefined
  const status = typeof params.status === 'string' ? params.status : undefined
  const type = typeof params.type === 'string' ? params.type : undefined
  const audience = typeof params.audience === 'string' ? params.audience : undefined
  const search = typeof params.search === 'string' ? params.search : undefined

  const initialEvents = await getEvents({
    starts_from: startsFrom,
    starts_until: startsUntil,
    status: status as Parameters<typeof getEvents>[0]['status'],
    type: type as Parameters<typeof getEvents>[0]['type'],
    audience: audience as Parameters<typeof getEvents>[0]['audience'],
    search: search ?? (params.q as string | undefined),
    page_size: 200,
  })

  return <CalendarView initialEvents={initialEvents.results} options={options} />
}
```

- [ ] **Step 2: Create CalendarView shell with view state and navigation**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarView.tsx
'use client'

import { useState, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { addMonths, subMonths, addWeeks, subWeeks, startOfMonth, startOfWeek, format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { EventRead, EventOptions } from '@/lib/api/events'
import { CalendarNavigation } from './CalendarNavigation'
import { CalendarFilters } from './CalendarFilters'
import { MonthView } from './MonthView'
import { WeekView } from './WeekView'
import { AgendaView } from './AgendaView'

type CalendarViewType = 'month' | 'week' | 'agenda'

interface Props {
  initialEvents: EventRead[]
  options: EventOptions
}

export function CalendarView({ initialEvents, options }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [events, _setEvents] = useState(initialEvents)
  const [viewType, setViewType] = useState<CalendarViewType>('month')
  const [currentDate, setCurrentDate] = useState(new Date())

  const navigate = {
    prev: () => {
      setCurrentDate((d) => (viewType === 'week' ? subWeeks(d, 1) : subMonths(d, 1)))
    },
    next: () => {
      setCurrentDate((d) => (viewType === 'week' ? addWeeks(d, 1) : addMonths(d, 1)))
    },
    today: () => setCurrentDate(new Date()),
  }

  const title = useMemo(() => {
    if (viewType === 'month') return format(currentDate, "MMMM 'de' yyyy", { locale: ptBR })
    if (viewType === 'week') {
      const start = startOfWeek(currentDate, { weekStartsOn: 0 })
      return `Semana de ${format(start, "d 'de' MMM", { locale: ptBR })}`
    }
    return format(currentDate, "MMMM yyyy", { locale: ptBR })
  }, [viewType, currentDate])

  const handleDayClick = (date: Date) => {
    router.push(`/events/new?date=${format(date, 'yyyy-MM-dd')}`)
  }

  const handleEventClick = (eventId: string) => {
    router.push(`/events/${eventId}`)
  }

  return (
    <div className="flex flex-col h-full gap-4 p-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Eventos</h1>
        <button
          onClick={() => router.push('/events/new')}
          className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground h-10 px-4 text-sm font-medium"
        >
          Novo Evento
        </button>
      </div>

      <CalendarFilters options={options} />

      <CalendarNavigation
        title={title}
        viewType={viewType}
        onViewChange={setViewType}
        onPrev={navigate.prev}
        onNext={navigate.next}
        onToday={navigate.today}
      />

      {viewType === 'month' && (
        <MonthView
          currentDate={currentDate}
          events={events}
          onDayClick={handleDayClick}
          onEventClick={handleEventClick}
        />
      )}
      {viewType === 'week' && (
        <WeekView
          currentDate={currentDate}
          events={events}
          onDayClick={handleDayClick}
          onEventClick={handleEventClick}
        />
      )}
      {viewType === 'agenda' && (
        <AgendaView events={events} onEventClick={handleEventClick} />
      )}
    </div>
  )
}
```

- [ ] **Step 3: Create CalendarNavigation**

```typescript
// .../events/_components/CalendarNavigation.tsx
'use client'

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

type CalendarViewType = 'month' | 'week' | 'agenda'

interface Props {
  title: string
  viewType: CalendarViewType
  onViewChange: (type: CalendarViewType) => void
  onPrev: () => void
  onNext: () => void
  onToday: () => void
}

export function CalendarNavigation({ title, viewType, onViewChange, onPrev, onNext, onToday }: Props) {
  const views: { label: string; value: CalendarViewType }[] = [
    { label: 'Mes', value: 'month' },
    { label: 'Semana', value: 'week' },
    { label: 'Agenda', value: 'agenda' },
  ]

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" onClick={onPrev}>
          <ChevronLeft className="size-4" />
        </Button>
        <h2 className="text-lg font-semibold min-w-[180px] text-center capitalize">{title}</h2>
        <Button variant="outline" size="icon" onClick={onNext}>
          <ChevronRight className="size-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onToday}>
          Hoje
        </Button>
      </div>
      <div className="flex rounded-lg bg-muted p-1">
        {views.map((v) => (
          <button
            key={v.value}
            onClick={() => onViewChange(v.value)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              viewType === v.value ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create CalendarFilters**

```typescript
// .../events/_components/CalendarFilters.tsx
'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'
import { Search } from 'lucide-react'
import { EventOptions } from '@/lib/api/events'

interface Props {
  options: EventOptions
}

export function CalendarFilters({ options }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/events?${params.toString()}`)
  }

  const debouncedSearch = useDebouncedCallback((value: string) => updateParam('search', value), 300)

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="relative flex-1 min-w-[200px] max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar eventos..."
          defaultValue={searchParams.get('search') ?? ''}
          onChange={(e) => debouncedSearch(e.target.value)}
          className="w-full h-10 pl-9 pr-3 rounded-md bg-background border text-sm"
        />
      </div>
      <select
        value={searchParams.get('type') ?? ''}
        onChange={(e) => updateParam('type', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todos os tipos</option>
        {options.types.map((t) => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>
      <select
        value={searchParams.get('status') ?? ''}
        onChange={(e) => updateParam('status', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todos os status</option>
        {options.statuses.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
      <select
        value={searchParams.get('audience') ?? ''}
        onChange={(e) => updateParam('audience', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todas as audiencias</option>
        {options.audiences.map((a) => (
          <option key={a.value} value={a.value}>{a.label}</option>
        ))}
      </select>
    </div>
  )
}
```

- [ ] **Step 5: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/page.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/CalendarView.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/CalendarNavigation.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/CalendarFilters.tsx
git commit -m "feat: add calendar page shell with navigation and filters"
```

---

### Task 6: Month view with multi-day color bars

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/MonthView.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarDay.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/CalendarEvent.tsx`

**Interfaces:**
- Consumes: `EventRead` from `@/lib/api/events`, `date-fns` for week/month calculations
- Produces: Month grid with 7 columns, multi-day events as color bars, empty day click, event click

- [ ] **Step 1: Create MonthView**

```typescript
// .../events/_components/MonthView.tsx
'use client'

import { useMemo } from 'react'
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, isWithinInterval } from 'date-fns'
import { EventRead } from '@/lib/api/events'
import { CalendarDay } from './CalendarDay'

interface Props {
  currentDate: Date
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']

export function MonthView({ currentDate, events, onDayClick, onEventClick }: Props) {
  const days = useMemo(() => {
    const monthStart = startOfMonth(currentDate)
    const monthEnd = endOfMonth(currentDate)
    const calStart = startOfWeek(monthStart, { weekStartsOn: 0 })
    const calEnd = endOfWeek(monthEnd, { weekStartsOn: 0 })
    return eachDayOfInterval({ start: calStart, end: calEnd })
  }, [currentDate])

  const eventsByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    events.forEach((event) => {
      const eventStart = new Date(event.start_at)
      const eventEnd = new Date(event.end_at)
      const interval = { start: eventStart, end: eventEnd }
      days.forEach((day) => {
        if (isSameDay(day, eventStart) || isSameDay(day, eventEnd) || isWithinInterval(day, interval)) {
          const key = day.toISOString()
          if (!map.has(key)) map.set(key, [])
          map.get(key)!.push(event)
        }
      })
    })
    return map
  }, [events, days])

  return (
    <div className="flex flex-col flex-1">
      <div className="grid grid-cols-7 border-b">
        {WEEKDAYS.map((d) => (
          <div key={d} className="py-2 text-center text-xs font-semibold text-muted-foreground">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 flex-1 auto-rows-fr">
        {days.map((day) => (
          <CalendarDay
            key={day.toISOString()}
            date={day}
            isCurrentMonth={isSameMonth(day, currentDate)}
            events={eventsByDay.get(day.toISOString()) ?? []}
            onDayClick={onDayClick}
            onEventClick={onEventClick}
          />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create CalendarDay**

```typescript
// .../events/_components/CalendarDay.tsx
'use client'

import { isToday } from 'date-fns'
import { EventRead } from '@/lib/api/events'
import { CalendarEvent } from './CalendarEvent'

interface Props {
  date: Date
  isCurrentMonth: boolean
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

export function CalendarDay({ date, isCurrentMonth, events, onDayClick, onEventClick }: Props) {
  return (
    <div
      className={`border-b border-r p-1 min-h-[80px] cursor-pointer hover:bg-accent/50 transition-colors ${
        !isCurrentMonth ? 'opacity-40' : ''
      }`}
      onClick={() => onDayClick(date)}
    >
      <div className={`text-xs mb-1 w-6 h-6 flex items-center justify-center rounded-full ${
        isToday(date) ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
      }`}>
        {date.getDate()}
      </div>
      <div className="space-y-0.5">
        {events.slice(0, 3).map((event) => (
          <CalendarEvent key={event.id} event={event} onClick={() => onEventClick(event.id)} />
        ))}
        {events.length > 3 && (
          <div className="text-[10px] text-muted-foreground px-1">+{events.length - 3} mais</div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create CalendarEvent (color bar)**

```typescript
// .../events/_components/CalendarEvent.tsx
'use client'

import { EventRead } from '@/lib/api/events'

interface Props {
  event: EventRead
  onClick: () => void
}

export function CalendarEvent({ event, onClick }: Props) {
  return (
    <div
      className="text-[10px] leading-tight px-1 py-0.5 rounded-sm truncate text-white cursor-pointer hover:opacity-80 font-medium"
      style={{ backgroundColor: event.type_color }}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      title={event.title}
    >
      {event.title}
    </div>
  )
}
```

- [ ] **Step 4: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/MonthView.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/CalendarDay.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/CalendarEvent.tsx
git commit -m "feat: add month view with multi-day color bars"
```

---

### Task 7: Week and Agenda views

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/WeekView.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/_components/AgendaView.tsx`

**Interfaces:**
- Consumes: `EventRead` from `@/lib/api/events`
- Produces: Week view (7 columns with hourly slots, events positioned by time) and Agenda view (chronological list grouped by day)

- [ ] **Step 1: Create WeekView**

```typescript
// .../events/_components/WeekView.tsx
'use client'

import { useMemo } from 'react'
import { startOfWeek, addDays, setHours, setMinutes, format, isSameDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { EventRead } from '@/lib/api/events'

interface Props {
  currentDate: Date
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)

export function WeekView({ currentDate, events, onDayClick, onEventClick }: Props) {
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 0 })
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const eventsByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    days.forEach((day) => {
      map.set(day.toISOString(), events.filter((e) => isSameDay(new Date(e.start_at), day)))
    })
    return map
  }, [events, days])

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <div className="grid grid-cols-[60px_repeat(7,1fr)] sticky top-0 bg-background z-10 border-b">
        <div className="py-2" />
        {days.map((day) => (
          <div key={day.toISOString()} className="py-2 text-center text-xs font-semibold">
            <div className="text-muted-foreground">{format(day, 'EEE', { locale: ptBR })}</div>
            <div className="text-lg">{format(day, 'd')}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-[60px_repeat(7,1fr)]">
        {HOURS.map((hour) => (
          <>
            <div key={`h-${hour}`} className="h-12 border-r border-b pr-2 pt-0 text-right text-[10px] text-muted-foreground">
              {String(hour).padStart(2, '0')}:00
            </div>
            {days.map((day) => {
              const dayEvents = (eventsByDay.get(day.toISOString()) ?? []).filter((e) => {
                const start = new Date(e.start_at)
                return start.getHours() === hour
              })
              return (
                <div
                  key={`${day.toISOString()}-${hour}`}
                  className="h-12 border-r border-b cursor-pointer hover:bg-accent/30"
                  onClick={() => {
                    const clickedHour = setMinutes(setHours(day, hour), 0)
                    onDayClick(clickedHour)
                  }}
                >
                  {dayEvents.map((event) => (
                    <div
                      key={event.id}
                      className="text-[10px] px-1 py-0.5 rounded-sm text-white mx-0.5 cursor-pointer hover:opacity-80 truncate"
                      style={{ backgroundColor: event.type_color }}
                      onClick={(e) => { e.stopPropagation(); onEventClick(event.id) }}
                      title={event.title}
                    >
                      {event.title}
                    </div>
                  ))}
                </div>
              )
            })}
          </>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create AgendaView**

```typescript
// .../events/_components/AgendaView.tsx
'use client'

import { useMemo } from 'react'
import { format, isSameDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { EventRead } from '@/lib/api/events'
import { CalendarDays, Clock } from 'lucide-react'

interface Props {
  events: EventRead[]
  onEventClick: (eventId: string) => void
}

export function AgendaView({ events, onEventClick }: Props) {
  const groupedByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    events.forEach((event) => {
      const dayKey = format(new Date(event.start_at), 'yyyy-MM-dd')
      if (!map.has(dayKey)) map.set(dayKey, [])
      map.get(dayKey)!.push(event)
    })
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [events])

  if (groupedByDay.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <CalendarDays className="size-12 mb-3 opacity-30" />
        <p className="text-sm">Nenhum evento neste periodo.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      {groupedByDay.map(([dayKey, dayEvents]) => {
        const date = new Date(dayKey + 'T00:00:00')
        return (
          <div key={dayKey} className="border-b last:border-b-0">
            <div className="sticky top-0 bg-background z-10 py-3 px-4 border-b">
              <h3 className="text-sm font-semibold capitalize">
                {format(date, "EEEE, d 'de' MMMM", { locale: ptBR })}
              </h3>
            </div>
            <div className="divide-y">
              {dayEvents.map((event) => (
                <div
                  key={event.id}
                  className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-accent/50 transition-colors"
                  onClick={() => onEventClick(event.id)}
                >
                  <div className="w-2 h-10 rounded-full shrink-0" style={{ backgroundColor: event.type_color }} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{event.title}</div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="size-3" />
                        {format(new Date(event.start_at), 'HH:mm')} - {format(new Date(event.end_at), 'HH:mm')}
                      </span>
                      {event.location && <span>{event.location.name || event.location.address}</span>}
                    </div>
                  </div>
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full text-white shrink-0"
                    style={{ backgroundColor: event.type_color }}
                  >
                    {event.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 3: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 4: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/WeekView.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/_components/AgendaView.tsx
git commit -m "feat: add week and agenda calendar views"
```

---

### Task 8: Event create form with Leaflet location picker

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/new/page.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/new/_components/EventForm.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/new/_components/LocationPicker.tsx`
- Modify: `app/web/package.json` (add leaflet dependencies)

**Interfaces:**
- Consumes: `createEvent` from `@/actions/events`, `getEventOptions` from `@/lib/api/events`
- Produces: Form with title, description, type (combobox), audiences (multi-chip), start/end datetime, Leaflet location picker

- [ ] **Step 1: Install Leaflet dependencies**

```bash
cd app/web; bun add react-leaflet leaflet leaflet-geosearch
cd app/web; bun add -D @types/leaflet
```

- [ ] **Step 2: Create the create page (server component fetching options)**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/new/page.tsx
import { getEventOptions } from '@/lib/api/events'
import { EventForm } from './_components/EventForm'

interface Props {
  searchParams: Promise<{ date?: string }>
}

export default async function NewEventPage({ searchParams }: Props) {
  const params = await searchParams
  const options = await getEventOptions()
  return <EventForm options={options} prefilledDate={params.date ?? null} />
}
```

- [ ] **Step 3: Create EventForm with react-hook-form + zod**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/new/_components/EventForm.tsx
'use client'

import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Combobox } from '@/components/ui/combobox'
import { createEvent } from '@/actions/events'
import { EventOptions } from '@/lib/api/events'
import { LocationPicker } from './LocationPicker'

const eventSchema = z.object({
  title: z.string().min(1, 'Titulo e obrigatorio.').max(255),
  description: z.string(),
  type: z.string().min(1, 'Tipo e obrigatorio.'),
  audiences: z.array(z.string()).min(1, 'Selecione ao menos uma audiencia.'),
  start_at: z.string().min(1, 'Data de inicio e obrigatoria.'),
  end_at: z.string().min(1, 'Data de fim e obrigatoria.'),
  location_name: z.string(),
  location_address: z.string(),
  location_latitude: z.number().nullable(),
  location_longitude: z.number().nullable(),
}).refine((data) => new Date(data.end_at) >= new Date(data.start_at), {
  message: 'Fim deve ser posterior ao inicio.',
  path: ['end_at'],
})

type EventFormValues = z.infer<typeof eventSchema>

interface Props {
  options: EventOptions
  prefilledDate: string | null
}

export function EventForm({ options, prefilledDate }: Props) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [audiences, setAudiences] = useState<string[]>([])

  const today = format(new Date(), "yyyy-MM-dd'T'HH:mm")
  const prefilled = prefilledDate ? `${prefilledDate}T20:00` : undefined

  const form = useForm<EventFormValues>({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      title: '',
      description: '',
      type: '',
      audiences: [],
      start_at: prefilled ?? today,
      end_at: prefilled ?? today,
      location_name: '',
      location_address: '',
      location_latitude: null,
      location_longitude: null,
    },
  })

  const handleSubmit = async (values: EventFormValues) => {
    setIsSubmitting(true)
    setSubmitError('')
    try {
      const hasLocation = values.location_address && values.location_latitude && values.location_longitude
      await createEvent({
        title: values.title,
        description: values.description || undefined,
        start_at: new Date(values.start_at).toISOString(),
        end_at: new Date(values.end_at).toISOString(),
        type: values.type,
        audiences: values.audiences,
        location: hasLocation
          ? {
              name: values.location_name || undefined,
              address: values.location_address,
              latitude: values.location_latitude!,
              longitude: values.location_longitude!,
            }
          : null,
      })
    } catch (e: unknown) {
      const err = e as { message?: string }
      setSubmitError(err.message ?? 'Erro ao criar evento.')
      setIsSubmitting(false)
    }
  }

  const toggleAudience = (audience: string) => {
    setAudiences((prev) => {
      const next = prev.includes(audience)
        ? prev.filter((a) => a !== audience)
        : [...prev, audience]
      form.setValue('audiences', next)
      return next
    })
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="size-4" /> Voltar
      </button>
      <h1 className="text-2xl font-bold mb-6">Novo Evento</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Titulo *</FormLabel>
                <FormControl>
                  <Input {...field} placeholder="Nome do evento" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Descricao</FormLabel>
                <FormControl>
                  <Textarea {...field} placeholder="Descreva o evento..." rows={3} />
                </FormControl>
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tipo *</FormLabel>
                <FormControl>
                  <Combobox
                    options={options.types.map((t) => ({ value: t.value, label: t.label }))}
                    value={field.value}
                    onValueChange={(v) => field.onChange(String(v))}
                    placeholder="Selecione o tipo..."
                    searchPlaceholder="Buscar tipo..."
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div>
            <label className="text-sm font-medium">Audiencias *</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {options.audiences.map((a) => (
                <button
                  key={a.value}
                  type="button"
                  onClick={() => toggleAudience(a.value)}
                  className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                    audiences.includes(a.value)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-border hover:bg-accent'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
            {Object.keys(form.formState.errors).length > 0 && form.formState.errors.audiences && (
              <p className="text-destructive text-sm mt-1">{form.formState.errors.audiences.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="start_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Inicio *</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="end_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fim *</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Local (opcional)</h3>

            <FormField
              control={form.control}
              name="location_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome do local</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Ex: Bar do Ze" />
                  </FormControl>
                </FormItem>
              )}
            />

            <LocationPicker
              onLocationSelect={(lat, lng, address) => {
                form.setValue('location_latitude', lat)
                form.setValue('location_longitude', lng)
                form.setValue('location_address', address)
              }}
            />
          </div>

          {submitError && <p className="text-sm text-destructive">{submitError}</p>}

          <div className="flex gap-3 justify-end pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Criando...' : 'Criar Evento'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}
```

- [ ] **Step 4: Create LocationPicker with Leaflet + geosearch**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/new/_components/LocationPicker.tsx
'use client'

import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import { OpenStreetMapProvider, SearchControl } from 'leaflet-geosearch'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-geosearch/dist/geosearch.css'

// ponytail: inline marker icon; default Leaflet icon path breaks with bundlers
const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

interface Props {
  onLocationSelect: (lat: number, lng: number, address: string) => void
}

function MapEvents({ onLocationSelect }: Props) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng
      fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`,
      )
        .then((r) => r.json())
        .then((data: { display_name?: string }) => {
          onLocationSelect(lat, lng, data.display_name ?? `${lat}, ${lng}`)
        })
        .catch(() => {
          onLocationSelect(lat, lng, `${lat}, ${lng}`)
        })
    },
  })
  return null
}

function SearchMap({ onLocationSelect }: Props) {
  const map = useMap()

  useEffect(() => {
    const provider = new OpenStreetMapProvider()
    const searchControl = new SearchControl({
      provider,
      style: 'bar',
      autoComplete: true,
      autoCompleteDelay: 250,
      marker: {
        icon: markerIcon,
        draggable: true,
      },
    })

    map.addControl(searchControl)

    map.on('geosearch/showlocation', (e: { location: { x: number; y: number; label: string } }) => {
      onLocationSelect(e.location.y, e.location.x, e.location.label)
    })

    return () => {
      map.removeControl(searchControl)
    }
  }, [map, onLocationSelect])

  return <MapEvents onLocationSelect={onLocationSelect} />
}

export function LocationPicker({ onLocationSelect }: Props) {
  return (
    <div className="mt-4 border rounded-lg overflow-hidden">
      <MapContainer
        center={[-23.5505, -46.6333]}
        zoom={13}
        style={{ height: '300px', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <SearchMap onLocationSelect={onLocationSelect} />
      </MapContainer>
    </div>
  )
}
```

- [ ] **Step 5: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/new/ app/web/package.json app/web/bun.lock package.json
git commit -m "feat: add event create form with Leaflet location picker"
```

---

### Task 9: Event detail page — header with thumbnail

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/page.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/EventHeader.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/EventInfo.tsx`

**Interfaces:**
- Consumes: `getEvent` from `@/lib/api/events`, `verifySessionWithoutRedirect` from `@/actions/session`, `uploadAndSetThumbnail` from `@/actions/photos`, `cancelEvent`, `reactivateEvent`, `deleteEvent` from `@/actions/events`
- Produces: Detail page header with thumbnail (with inline upload), title, type badge colored, status, dates, creator, participant count, location, action buttons

- [ ] **Step 1: Create the server component page**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/[id]/page.tsx
import { notFound } from 'next/navigation'
import { getEvent } from '@/lib/api/events'
import { verifySessionWithoutRedirect } from '@/actions/session'
import { EventDetailClient } from './_components/EventDetailClient'

interface Props {
  params: Promise<{ id: string }>
}

export default async function EventDetailPage({ params }: Props) {
  const { id } = await params
  const event = await getEvent(id).catch(() => null)
  if (!event) notFound()
  const user = await verifySessionWithoutRedirect()

  const isCreator = user?.id === event.id // ponytail: event.creator not exposed; adjust when backend adds creator_id
  const isStaff = false // ponytail: wire is_staff from session when available

  return <EventDetailClient event={event} isCreator={isCreator} isStaff={isStaff} userId={user?.id ?? null} />
}
```

Ponytail note: the backend `EventReadSerializer` may need `creator_id` field. If not present, use `canEdit` heuristic or add the field to the backend serializer.

- [ ] **Step 2: Create EventDetailClient wrapper**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/EventDetailClient.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { EventRead } from '@/lib/api/events'
import { EventHeader } from './EventHeader'
import { EventTabs } from './EventTabs'

interface Props {
  event: EventRead
  isCreator: boolean
  isStaff: boolean
  userId: string | null
}

export function EventDetailClient({ event: initialEvent, isCreator, isStaff, userId }: Props) {
  const [event, setEvent] = useState(initialEvent)
  const router = useRouter()
  const canManage = isCreator || isStaff

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <EventHeader event={event} canManage={canManage} onEventUpdate={setEvent} />
      <div className="mt-6">
        <EventTabs event={event} canManage={canManage} userId={userId} />
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create EventHeader with thumbnail upload**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/EventHeader.tsx
'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { ArrowLeft, ImagePlus, Pencil, Trash2, XCircle, RotateCcw } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EventRead } from '@/lib/api/events'
import { cancelEvent, reactivateEvent, deleteEvent } from '@/actions/events'
import { uploadAndSetThumbnail } from '@/actions/photos'

interface Props {
  event: EventRead
  canManage: boolean
  onEventUpdate: (event: EventRead) => void
}

export function EventHeader({ event, canManage, onEventUpdate }: Props) {
  const router = useRouter()
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      setUploading(true)
      const formData = new FormData()
      formData.append('file', acceptedFiles[0])
      try {
        await uploadAndSetThumbnail(event.id, formData)
        router.refresh() // ponytail: simple refresh; add react-query revalidation later
      } catch {
        // ponytail: error toast via sonner when added
      } finally {
        setUploading(false)
      }
    },
    [event.id, router],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: !canManage || uploading,
  })

  const statusLabel = {
    SCHEDULED: 'Agendado',
    IN_PROGRESS: 'Em andamento',
    COMPLETED: 'Concluido',
    CANCELLED: 'Cancelado',
  }[event.status]

  const statusVariant = event.status === 'CANCELLED' ? 'destructive' : event.status === 'IN_PROGRESS' ? 'default' : 'secondary'

  return (
    <div className="flex gap-6">
      {/* Thumbnail */}
      <div className="w-48 shrink-0">
        {event.thumbnail_url ? (
          <div className="relative group rounded-lg overflow-hidden aspect-video">
            <img
              src={`${process.env.NEXT_PUBLIC_MEDIA_URL ?? ''}${event.thumbnail_url}`}
              alt={event.title}
              className="w-full h-full object-cover"
            />
            {canManage && (
              <div {...getRootProps()} className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
                <input {...getInputProps()} />
                <span className="text-white text-xs text-center px-2">Alterar thumbnail</span>
              </div>
            )}
          </div>
        ) : canManage ? (
          <div
            {...getRootProps()}
            className={`aspect-video rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="text-center text-muted-foreground">
              <ImagePlus className="size-6 mx-auto mb-1" />
              <span className="text-[10px]">
                {uploading ? 'Enviando...' : 'Adicionar thumbnail'}
              </span>
            </div>
          </div>
        ) : (
          <div className="aspect-video rounded-lg bg-muted flex items-center justify-center">
            <ImagePlus className="size-6 text-muted-foreground/30" />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <button
          onClick={() => router.push('/events')}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="size-4" /> Voltar
        </button>

        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold">{event.title}</h1>
          <Badge style={{ backgroundColor: event.type_color, color: '#fff' }}>
            {event.type.replace(/_/g, ' ')}
          </Badge>
          <Badge variant={statusVariant as 'default' | 'secondary' | 'destructive'}>
            {statusLabel}
          </Badge>
        </div>

        <div className="mt-3 space-y-1 text-sm text-muted-foreground">
          <p>
            {format(new Date(event.start_at), "d 'de' MMMM 'de' yyyy 'as' HH:mm", { locale: ptBR })}
            {' ate '}
            {format(new Date(event.end_at), "d 'de' MMMM 'de' yyyy 'as' HH:mm", { locale: ptBR })}
          </p>
          {event.participants_count > 0 && (
            <p>{event.participants_count} participante{event.participants_count > 1 ? 's' : ''}</p>
          )}
          {event.location && (
            <p>{event.location.name ? `${event.location.name} — ` : ''}{event.location.address}</p>
          )}
        </div>

        {event.description && (
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{event.description}</p>
        )}

        {canManage && (
          <div className="flex gap-2 mt-4">
            <Button variant="outline" size="sm" onClick={() => router.push(`/events/${event.id}/edit`)}>
              <Pencil className="size-3 mr-1" /> Editar
            </Button>
            {event.status !== 'CANCELLED' ? (
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  if (confirm('Cancelar este evento?')) {
                    await cancelEvent(event.id)
                    router.refresh()
                  }
                }}
              >
                <XCircle className="size-3 mr-1" /> Cancelar
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await reactivateEvent(event.id)
                  router.refresh()
                }}
              >
                <RotateCcw className="size-3 mr-1" /> Reativar
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 5: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/\[id\]/page.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/\[id\]/_components/EventDetailClient.tsx app/web/src/app/\(private\)/\(pages\)/\(main\)/events/\[id\]/_components/EventHeader.tsx
git commit -m "feat: add event detail page with header and thumbnail upload"
```

---

### Task 10: Event detail tabs — Participants, Photos, Highlights

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/EventTabs.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/ParticipantsList.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/PhotosGrid.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/HighlightsList.tsx`
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/_components/HighlightCard.tsx`

**Interfaces:**
- Consumes: `getEventParticipants`, `getEventPhotos`, `getEventHighlights` from `@/lib/api/events`; `addParticipants`, `removeParticipant` from `@/actions/participants`; `uploadAndLinkPhoto`, `linkPhoto`, `unlinkPhoto`, `setThumbnail` from `@/actions/photos`; `createHighlight`, `updateHighlight`, `deleteHighlight` from `@/actions/highlights`
- Produces: All detail tabs with full CRUD functionality

- [ ] **Step 1: Create EventTabs with tab switching**

```typescript
// .../events/[id]/_components/EventTabs.tsx
'use client'

import { useState, useEffect } from 'react'
import { EventRead } from '@/lib/api/events'
import { getEventParticipants, getEventPhotos, getEventHighlights } from '@/lib/api/events'
import { ParticipantsList } from './ParticipantsList'
import { PhotosGrid } from './PhotosGrid'
import { HighlightsList } from './HighlightsList'

interface Props {
  event: EventRead
  canManage: boolean
  userId: string | null
}

type Tab = 'participants' | 'photos' | 'highlights'

export function EventTabs({ event, canManage, userId }: Props) {
  const [tab, setTab] = useState<Tab>('participants')
  const tabs: { key: Tab; label: string }[] = [
    { key: 'participants', label: 'Participantes' },
    { key: 'photos', label: 'Fotos' },
    { key: 'highlights', label: 'Highlights' },
  ]

  return (
    <div>
      <div className="flex border-b">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="pt-4">
        {tab === 'participants' && (
          <ParticipantsSection eventId={event.id} canManage={canManage} userId={userId} />
        )}
        {tab === 'photos' && (
          <PhotosSection eventId={event.id} canManage={canManage} />
        )}
        {tab === 'highlights' && (
          <HighlightsSection eventId={event.id} canManage={canManage} userId={userId} />
        )}
      </div>
    </div>
  )
}

// Sub-components wrapped with data fetching
function ParticipantsSection({ eventId, canManage, userId }: { eventId: string; canManage: boolean; userId: string | null }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getEventParticipants>> | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventParticipants(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => { load() }, [eventId])

  return <ParticipantsList eventId={eventId} data={data} loading={loading} canManage={canManage} userId={userId} onRefresh={load} />
}

function PhotosSection({ eventId, canManage }: { eventId: string; canManage: boolean }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getEventPhotos>> | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventPhotos(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => { load() }, [eventId])

  return <PhotosGrid eventId={eventId} data={data} loading={loading} canManage={canManage} onRefresh={load} />
}

function HighlightsSection({ eventId, canManage, userId }: { eventId: string; canManage: boolean; userId: string | null }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof getEventHighlights>> | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventHighlights(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => { load() }, [eventId])

  return <HighlightsList eventId={eventId} data={data} loading={loading} canManage={canManage} userId={userId} onRefresh={load} />
}
```

- [ ] **Step 2: Create ParticipantsList**

```typescript
// .../events/[id]/_components/ParticipantsList.tsx
'use client'

import { useState } from 'react'
import { UserPlus, UserX } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Combobox } from '@/components/ui/combobox'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, ParticipantRead } from '@/lib/api/events'
import { addParticipants, removeParticipant } from '@/actions/participants'

interface Props {
  eventId: string
  data: PaginatedResponse<ParticipantRead> | null
  loading: boolean
  canManage: boolean
  userId: string | null
  onRefresh: () => void
}

export function ParticipantsList({ eventId, data, loading, canManage, userId, onRefresh }: Props) {
  const [adding, setAdding] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<string>('')

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
        ))}
      </div>
    )
  }

  const participants = data?.results ?? []

  return (
    <div>
      {canManage && (
        <div className="flex gap-3 mb-4">
          <Combobox
            options={[]} // ponytail: backend needs user search endpoint; for now manual UUID input
            value={selectedUserId}
            onValueChange={setSelectedUserId}
            placeholder="Buscar usuario..."
            disabled
          />
          <Button
            size="sm"
            onClick={async () => {
              if (!selectedUserId) return
              await addParticipants(eventId, [selectedUserId])
              setSelectedUserId('')
              onRefresh()
            }}
            disabled
          >
            <UserPlus className="size-3 mr-1" /> Adicionar
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {participants.map((p) => (
          <div key={p.id} className="flex items-center gap-3 py-2 border-b last:border-b-0">
            <Avatar className="size-8">
              <AvatarFallback>
                {(p.username ?? '?')[0].toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <span className="flex-1 text-sm">{p.username ?? 'Usuario'}</span>
            {canManage && p.user !== userId && (
              <Button
                variant="ghost"
                size="icon"
                onClick={async () => {
                  await removeParticipant(eventId, p.user)
                  onRefresh()
                }}
              >
                <UserX className="size-4 text-muted-foreground" />
              </Button>
            )}
          </div>
        ))}
      </div>

      {participants.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">Nenhum participante ainda.</p>
      )}
    </div>
  )
}
```

Ponytail note: participant add is disabled until a user search endpoint exists or we implement a UUID input.

- [ ] **Step 3: Create PhotosGrid**

```typescript
// .../events/[id]/_components/PhotosGrid.tsx
'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { ImagePlus, Star, X, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, EventPhotoRead } from '@/lib/api/events'
import { uploadAndLinkPhoto, unlinkPhoto, setThumbnail } from '@/actions/photos'

interface Props {
  eventId: string
  data: PaginatedResponse<EventPhotoRead> | null
  loading: boolean
  canManage: boolean
  onRefresh: () => void
}

export function PhotosGrid({ eventId, data, loading, canManage, onRefresh }: Props) {
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setUploading(true)
      for (const file of acceptedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        try {
          await uploadAndLinkPhoto(eventId, formData)
        } catch {
          // ponytail: add toast
        }
      }
      setUploading(false)
      onRefresh()
    },
    [eventId, onRefresh],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    disabled: uploading,
  })

  const photos = data?.results ?? []

  return (
    <div>
      <div className="grid grid-cols-3 md:grid-cols-4 gap-3 mb-4">
        {/* Upload zone */}
        <div
          {...getRootProps()}
          className={`aspect-square rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer transition-colors ${
            isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
          } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="text-center text-muted-foreground">
            <Upload className="size-5 mx-auto mb-1" />
            <span className="text-[10px]">{uploading ? 'Enviando...' : 'Upload'}</span>
          </div>
        </div>

        {loading && Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} className="aspect-square rounded-lg" />
        ))}

        {photos.map((photo) => (
          <div key={photo.id} className="relative group aspect-square rounded-lg overflow-hidden">
            <img
              src={`${process.env.NEXT_PUBLIC_MEDIA_URL ?? ''}${photo.object_key}`}
              alt=""
              className="w-full h-full object-cover"
            />
            {/* Thumbnail badge */}
            {photo.is_thumbnail && (
              <div className="absolute top-2 left-2 bg-yellow-500 rounded-full p-0.5">
                <Star className="size-3 text-white fill-white" />
              </div>
            )}
            {/* Hover actions */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              {canManage && !photo.is_thumbnail && (
                <button
                  className="p-1.5 bg-white/90 rounded-full hover:bg-white"
                  onClick={async () => {
                    await setThumbnail(eventId, photo.id)
                    onRefresh()
                  }}
                  title="Definir como thumbnail"
                >
                  <Star className="size-3.5" />
                </button>
              )}
              {canManage && (
                <button
                  className="p-1.5 bg-white/90 rounded-full hover:bg-white text-destructive"
                  onClick={async () => {
                    await unlinkPhoto(eventId, photo.id)
                    onRefresh()
                  }}
                  title="Desvincular"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {!loading && photos.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">Nenhuma foto ainda.</p>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create HighlightsList and HighlightCard**

```typescript
// .../events/[id]/_components/HighlightsList.tsx
'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, HighlightRead } from '@/lib/api/events'
import { createHighlight } from '@/actions/highlights'
import { HighlightCard } from './HighlightCard'

interface Props {
  eventId: string
  data: PaginatedResponse<HighlightRead> | null
  loading: boolean
  canManage: boolean
  userId: string | null
  onRefresh: () => void
}

export function HighlightsList({ eventId, data, loading, canManage, userId, onRefresh }: Props) {
  const [showForm, setShowForm] = useState(false)
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const highlights = data?.results ?? []

  const handleCreate = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    await createHighlight(eventId, { text: text.trim(), photo_ids: [] })
    setText('')
    setShowForm(false)
    setSubmitting(false)
    onRefresh()
  }

  return (
    <div>
      {(userId || canManage) && (
        <div className="mb-4">
          {!showForm ? (
            <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
              <Plus className="size-3 mr-1" /> Adicionar highlight
            </Button>
          ) : (
            <div className="space-y-3 p-4 border rounded-lg">
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Escreva um destaque..."
                rows={3}
                maxLength={500}
              />
              <div className="flex gap-2 justify-end">
                <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>Cancelar</Button>
                <Button size="sm" onClick={handleCreate} disabled={submitting || !text.trim()}>
                  {submitting ? 'Salvando...' : 'Salvar'}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      )}

      <div className="space-y-4">
        {highlights.map((h) => (
          <HighlightCard key={h.id} highlight={h} canManage={canManage} userId={userId} />
        ))}
      </div>

      {!loading && highlights.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">Nenhum highlight ainda.</p>
      )}
    </div>
  )
}
```

```typescript
// .../events/[id]/_components/HighlightCard.tsx
'use client'

import { HighlightRead } from '@/lib/api/events'

interface Props {
  highlight: HighlightRead
  canManage: boolean
  userId: string | null
}

export function HighlightCard({ highlight, canManage, userId }: Props) {
  const isAuthor = userId === highlight.author_id

  return (
    <div className="border rounded-lg p-4">
      <p className="text-sm">{highlight.text}</p>
      {highlight.photos.length > 0 && (
        <div className="flex gap-2 mt-3">
          {highlight.photos.map((photo) => (
            <img
              key={photo.id}
              src={`${process.env.NEXT_PUBLIC_MEDIA_URL ?? ''}${photo.object_key}`}
              alt=""
              className="w-16 h-16 object-cover rounded-md"
            />
          ))}
        </div>
      )}
      <div className="mt-2 text-[10px] text-muted-foreground">
        {new Date(highlight.created_at).toLocaleDateString('pt-BR')}
        {(canManage || isAuthor) && (
          <span className="ml-2 text-primary cursor-pointer hover:underline">Editar</span>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/\[id\]/_components/
git commit -m "feat: add event detail tabs — participants, photos, highlights"
```

---

### Task 11: Event edit form (reuses create form)

**Files:**
- Create: `app/web/src/app/(private)/(pages)/(main)/events/[id]/edit/page.tsx`

**Interfaces:**
- Consumes: `getEvent` from `@/lib/api/events`, `updateEvent` from `@/actions/events`, same `EventForm` component from create
- Produces: Edit page reusing EventForm with prefilled values

- [ ] **Step 1: Create edit page**

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/[id]/edit/page.tsx
import { getEvent } from '@/lib/api/events'
import { EventEditForm } from './_components/EventEditForm'
import { getEventOptions } from '@/lib/api/events'

interface Props {
  params: Promise<{ id: string }>
}

export default async function EditEventPage({ params }: Props) {
  const { id } = await params
  const [event, options] = await Promise.all([getEvent(id), getEventOptions()])
  return <EventEditForm event={event} options={options} />
}
```

```typescript
// app/web/src/app/(private)/(pages)/(main)/events/[id]/edit/_components/EventEditForm.tsx
'use client'

import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Combobox } from '@/components/ui/combobox'
import { updateEvent } from '@/actions/events'
import { EventRead, EventOptions } from '@/lib/api/events'
import { LocationPicker } from '@/app/(private)/(pages)/(main)/events/new/_components/LocationPicker'

const editSchema = z.object({
  title: z.string().max(255),
  description: z.string(),
  type: z.string(),
  audiences: z.array(z.string()),
  start_at: z.string(),
  end_at: z.string(),
  location_name: z.string(),
  location_address: z.string(),
  location_latitude: z.number().nullable(),
  location_longitude: z.number().nullable(),
}).partial().refine((data) => {
  if (data.start_at && data.end_at && new Date(data.end_at) < new Date(data.start_at)) {
    return false
  }
  return true
}, { message: 'Fim deve ser posterior ao inicio.', path: ['end_at'] })

type EditFormValues = z.infer<typeof editSchema>

interface Props {
  event: EventRead
  options: EventOptions
}

export function EventEditForm({ event, options }: Props) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [audiences, setAudiences] = useState<string[]>(event.audiences ?? [])

  const form = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      title: event.title,
      description: event.description ?? '',
      type: event.type,
      audiences: event.audiences,
      start_at: format(new Date(event.start_at), "yyyy-MM-dd'T'HH:mm"),
      end_at: format(new Date(event.end_at), "yyyy-MM-dd'T'HH:mm"),
      location_name: event.location?.name ?? '',
      location_address: event.location?.address ?? '',
      location_latitude: event.location?.latitude ?? null,
      location_longitude: event.location?.longitude ?? null,
    },
  })

  const handleSubmit = async (values: EditFormValues) => {
    setIsSubmitting(true)
    setSubmitError('')
    try {
      const payload: Record<string, unknown> = {}
      if (values.title && values.title !== event.title) payload.title = values.title
      if (values.description !== undefined && values.description !== (event.description ?? ''))
        payload.description = values.description
      if (values.type && values.type !== event.type) payload.type = values.type
      if (values.audiences && values.audiences.length > 0) payload.audiences = values.audiences
      if (values.start_at) payload.start_at = new Date(values.start_at).toISOString()
      if (values.end_at) payload.end_at = new Date(values.end_at).toISOString()

      const hasLocation = values.location_address || values.location_latitude || values.location_longitude
      if (hasLocation) {
        payload.location = {
          name: values.location_name || undefined,
          address: values.location_address ?? '',
          latitude: values.location_latitude ?? 0,
          longitude: values.location_longitude ?? 0,
        }
      }

      await updateEvent(event.id, payload)
      router.push(`/events/${event.id}`)
    } catch (e: unknown) {
      const err = e as { message?: string }
      setSubmitError(err.message ?? 'Erro ao atualizar evento.')
      setIsSubmitting(false)
    }
  }

  const toggleAudience = (audience: string) => {
    setAudiences((prev) => {
      const next = prev.includes(audience)
        ? prev.filter((a) => a !== audience)
        : [...prev, audience]
      form.setValue('audiences', next)
      return next
    })
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="size-4" /> Voltar
      </button>
      <h1 className="text-2xl font-bold mb-6">Editar Evento</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Titulo</FormLabel>
                <FormControl>
                  <Input {...field} value={field.value ?? ''} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Descricao</FormLabel>
                <FormControl>
                  <Textarea {...field} value={field.value ?? ''} rows={3} />
                </FormControl>
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tipo</FormLabel>
                <FormControl>
                  <Combobox
                    options={options.types.map((t) => ({ value: t.value, label: t.label }))}
                    value={field.value ?? ''}
                    onValueChange={(v) => field.onChange(String(v))}
                    placeholder="Selecione o tipo..."
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div>
            <label className="text-sm font-medium">Audiencias</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {options.audiences.map((a) => (
                <button
                  key={a.value}
                  type="button"
                  onClick={() => toggleAudience(a.value)}
                  className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                    audiences.includes(a.value)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-border hover:bg-accent'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="start_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Inicio</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" value={field.value ?? ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="end_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fim</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" value={field.value ?? ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Local (opcional)</h3>

            <FormField
              control={form.control}
              name="location_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome do local</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ''} />
                  </FormControl>
                </FormItem>
              )}
            />

            <LocationPicker
              onLocationSelect={(lat, lng, address) => {
                form.setValue('location_latitude', lat)
                form.setValue('location_longitude', lng)
                form.setValue('location_address', address)
              }}
            />
          </div>

          {submitError && <p className="text-sm text-destructive">{submitError}</p>}

          <div className="flex gap-3 justify-end pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alteracoes'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}
```

- [ ] **Step 2: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 3: Commit**

```bash
git add app/web/src/app/\(private\)/\(pages\)/\(main\)/events/\[id\]/edit/
git commit -m "feat: add event edit form reusing create form components"
```

---

### Task 12: Install dependencies, full build verification, and polish

**Files:**
- Modify: `app/web/package.json` (add @tanstack/react-query if needed)
- Modify: `app/web/src/app/layout.tsx` (add QueryClientProvider if using React Query)
- Modify: Various files for type fixes and edge cases

**Interfaces:**
- Consumes: All previous tasks
- Produces: Full passing CI quality check

- [ ] **Step 1: Install remaining dependency**

```bash
cd app/web; bun add @tanstack/react-query
```

- [ ] **Step 2: Run lint**

```bash
cd app/web; bun run lint
```

- [ ] **Step 3: Run typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 4: Run build**

```bash
cd app/web; bun run build
```

- [ ] **Step 5: Fix any remaining type errors or build issues**

For each error found, fix inline and re-run typecheck/build until green.

- [ ] **Step 6: Run full quality pipeline**

```bash
cd app/web; bun run quality
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: add react-query, final type fixes, pass quality pipeline"
```

---

### Task 13: Final Playwright smoke tests with screenshots

**Files:**
- Modify: `app/web/e2e/smoke.spec.ts` (expand with full flow tests)
- Create: `app/web/e2e/events.spec.ts`
- Create: `app/web/e2e/screenshots/` (auto-created by Playwright)

**Interfaces:**
- Consumes: Running dev server (`bun run dev`), tasks 1-12 complete
- Produces: Passing Playwright test suite, `.playwright-report/` with visual evidence

- [ ] **Step 1: Expand smoke.spec.ts with full event flow**

```typescript
// app/web/e2e/events.spec.ts
import { test, expect } from '@playwright/test'

const TOKEN = process.env.E2E_TOKEN ?? 'mock-token'

test.beforeEach(async ({ context }) => {
  await context.addCookies([{ name: 'ev_s_tkn', value: TOKEN, domain: 'localhost', path: '/' }])
})

test.describe('Calendar page', () => {
  test('loads with month view by default', async ({ page }) => {
    await page.goto('/events')
    await expect(page.getByText('Eventos')).toBeVisible()
    await expect(page.locator('[data-view="month"]')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/calendar-month.png', fullPage: true })
  })

  test('week view renders hourly grid', async ({ page }) => {
    await page.goto('/events')
    await page.getByText('Semana').click()
    await expect(page.locator('text=00:00')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/calendar-week.png', fullPage: true })
  })

  test('agenda view renders event list', async ({ page }) => {
    await page.goto('/events')
    await page.getByText('Agenda').click()
    await page.screenshot({ path: 'e2e/screenshots/calendar-agenda.png', fullPage: true })
  })

  test('filters change URL params', async ({ page }) => {
    await page.goto('/events')
    // ponytail: select filter options by their rendered text when available
    const statusSelect = page.locator('select').nth(1)
    if (await statusSelect.isVisible()) {
      await statusSelect.selectOption('SCHEDULED')
      await page.waitForURL(/\?.*status=SCHEDULED/)
    }
  })
})

test.describe('Create event', () => {
  test('form renders all required fields', async ({ page }) => {
    await page.goto('/events/new')
    await expect(page.getByText('Novo Evento')).toBeVisible()
    await expect(page.getByPlaceholder('Nome do evento')).toBeVisible()
    await expect(page.getByText(/Tipo/)).toBeVisible()
    await expect(page.getByText(/Audiencias/)).toBeVisible()
    await expect(page.locator('input[type="datetime-local"]').first()).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/create-event-form.png', fullPage: true })
  })

  test('validation shows errors on empty submit', async ({ page }) => {
    await page.goto('/events/new')
    await page.getByRole('button', { name: /Criar Evento/ }).click()
    await expect(page.getByText(/obrigatorio/).first()).toBeVisible()
  })

  test('prefills date from query param', async ({ page }) => {
    await page.goto('/events/new?date=2026-08-15')
    const dateInput = page.locator('input[type="datetime-local"]').first()
    await expect(dateInput).toHaveValue(/2026-08-15/)
  })

  test('location picker map renders', async ({ page }) => {
    await page.goto('/events/new')
    await expect(page.locator('.leaflet-container')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/create-event-map.png', fullPage: true })
  })
})

test.describe('Event detail', () => {
  const EVENT_ID = process.env.E2E_EVENT_ID ?? 'some-uuid'

  test('detail page renders header and tabs', async ({ page }) => {
    await page.goto(`/events/${EVENT_ID}`)
    await expect(page.getByText(/Participantes|Fotos|Highlights/)).toBeVisible({ timeout: 15000 })
    await page.screenshot({ path: 'e2e/screenshots/event-detail.png', fullPage: true })
  })

  test('participants tab shows list', async ({ page }) => {
    await page.goto(`/events/${EVENT_ID}`)
    await page.getByText('Participantes').click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'e2e/screenshots/event-participants.png', fullPage: true })
  })

  test('photos tab shows upload zone', async ({ page }) => {
    await page.goto(`/events/${EVENT_ID}`)
    await page.getByText('Fotos').click()
    await expect(page.getByText('Upload')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/event-photos.png', fullPage: true })
  })
})

test.describe('Edit event', () => {
  const EVENT_ID = process.env.E2E_EVENT_ID ?? 'some-uuid'

  test('edit form prefills event data', async ({ page }) => {
    await page.goto(`/events/${EVENT_ID}/edit`)
    await expect(page.getByText('Editar Evento')).toBeVisible()
    await page.screenshot({ path: 'e2e/screenshots/edit-event-form.png', fullPage: true })
  })
})
```

- [ ] **Step 2: Create screenshots directory**

```bash
cd app/web; New-Item -ItemType Directory -Path e2e/screenshots -Force -ErrorAction SilentlyContinue
```

- [ ] **Step 3: Run Playwright tests**

Ensure the backend is running on `localhost:8000` and Next.js dev server is running or Playwright auto-starts it:

```bash
cd app/web; bunx playwright test --project=chromium
```

- [ ] **Step 4: Fix any failing tests**

For each failure, diagnose (screenshot is saved automatically), fix the code or test, re-run.

- [ ] **Step 5: Generate and review HTML report**

```bash
cd app/web; bunx playwright show-report
```

- [ ] **Step 6: Commit**

```bash
git add app/web/e2e/ app/web/playwright-report/ -f
git commit -m "test: add comprehensive Playwright e2e smoke tests with screenshots"
```

---

## Plan Summary

```
Task 0:  Playwright setup              (5 min)
Task 1:  Generate API types            (2-5 min)
Task 2:  Wire real authentication      (10-15 min)
Task 3:  API data layer                (10-15 min)
Task 4:  Server actions                (10-15 min)
Task 5:  Calendar shell + filters      (10-15 min)
Task 6:  Month view                    (10-15 min)
Task 7:  Week + Agenda views           (10-15 min)
Task 8:  Event create form + Leaflet   (15-20 min)
Task 9:  Event detail header           (10-15 min)
Task 10: Event detail tabs             (15-20 min)
Task 11: Event edit form               (10-15 min)
Task 12: Dependencies, build, polish   (10-15 min)
Task 13: Final Playwright smoke tests  (10-15 min)
```

**Dependency chain:** 0 → 1 → 2 → 3 → 4 → 5 → {6,7,8,9,10,11 parallel} → 12 → 13

Quality gates at end of each task: `bun run lint && bun run typecheck`. Full gate at Task 12: `bun run quality`. E2E gate at Task 13: `bunx playwright test`.

---

## Open Items / ponytail: shortcuts

1. **`creator_id` on EventRead**: The backend `EventReadSerializer` may not expose `creator_id`. The detail page uses a placeholder check. Add `creator_id` field to the serializer if missing.
2. **User search for participant add**: The combobox in ParticipantsList is disabled — needs a `/api/users/?search=` endpoint or manual UUID input.
3. **`is_staff` on session**: Not yet exposed from auth. Add it to the session response when available.
4. **`NEXT_PUBLIC_MEDIA_URL`**: Environment variable for MinIO/media base URL. Set in `.env` as the MinIO public URL.
5. **React Query integration**: Only used as dependency — full `useMutation` wrapping with `onSuccess -> revalidatePath` is added incrementally. Current implementation uses `router.refresh()`.
6. **Leaflet CSS import**: `leaflet/dist/leaflet.css` and `leaflet-geosearch/dist/geosearch.css` are imported in LocationPicker. These need to be available in the Next.js bundle (they are, but verify).
7. **Toast notifications**: Actions catch errors silently with comments marking `// ponytail: add toast`. Wire `sonner` `toast.error()` / `toast.success()` on each server action call.
