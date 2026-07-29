# Events Frontend — Design Doc

**Date**: 2026-07-29  
**Status**: Approved

## Scope

Full events module for the Next.js 16 frontend consuming the Django backend events API.
Covers both consumer (discover events, view content) and creator (manage events) flows.

### In scope

- Real auth wiring (login via `/api/auth/login/`, JWT cookies, route protection)
- Calendar page at `/events` with 3 views (month, week, agenda)
- Event detail at `/events/[id]` with participants, photos, highlights
- Event creation at `/events/new` and edition at `/events/[id]/edit`
- Photo upload (via `/api/media/`) + linking to events
- Thumbnail management (inline upload in detail header + photo grid badge)
- Highlights CRUD within event detail
- Participants add/remove within event detail
- Filters on calendar (type, status, audience, text search)
- Sidebar with "Eventos" section

### Out of scope

- Real-time features (WebSocket/SSE)
- Dashboards / analytics
- User profiles management

## Architecture

**Approach**: Hybrid — Server Components + Server Actions + React Query for mutations.

- **Server Components**: initial data fetch on listing and detail pages
- **Server Actions**: all mutations (create, update, delete, link, upload)
- **React Query**: wraps mutations in client components for optimistic cache + revalidation via `revalidatePath`
- **Types**: generated from backend OpenAPI schema via `bun run generate-api-types`

## Routes & File Structure

```
app/(private)/(pages)/(main)/
  events/
    page.tsx                         # Server Component — calendar + filters
    new/
      page.tsx                       # Client Component — create form
    [id]/
      page.tsx                       # Server Component — event detail
      edit/
        page.tsx                     # Client Component — edit form
      _components/
        EventHeader.tsx              # Title, type badge, status, thumbnail, actions
        EventInfo.tsx                # Description, date, location
        ParticipantsList.tsx         # Paginated avatar list + add/remove
        PhotosGrid.tsx               # Photo grid + upload zone + thumbnail badge
        HighlightsList.tsx           # Highlight cards (text + photos)
        HighlightCard.tsx
    _components/
      CalendarView.tsx               # Parent — manages view state
      MonthView.tsx                  # 7-column grid with multi-day color bars
      WeekView.tsx                   # 7 columns with hourly time slots
      AgendaView.tsx                 # Chronological list, days with events only
      CalendarFilters.tsx            # Search + type + status + audience dropdowns
      CalendarNavigation.tsx         # Prev/next, today button, view toggle
      CalendarDay.tsx                # Single day cell
      CalendarEvent.tsx              # Event bar/item inside a day cell

src/
  actions/
    auth.ts                          # login, logout, verifySession
    events.ts                        # createEvent, updateEvent, deleteEvent, cancelEvent, reactivateEvent
    participants.ts                  # addParticipants, removeParticipant
    photos.ts                        # uploadPhoto, linkPhoto, unlinkPhoto, setThumbnail
    highlights.ts                    # createHighlight, updateHighlight, deleteHighlight
  lib/
    api/
      events.ts                      # getEvents, getEvent, getEventParticipants, getEventPhotos, getEventHighlights
      photos.ts                      # uploadToMedia, getMediaPhotos
      auth.ts                        # loginRequest, sessionRequest
```

## Pages Detail

### Calendar Page (`/events`)

- **Type**: Client Component (view state, filter state, navigation)
- **Initial data**: Server Component fetches current month events via `starts_from`/`starts_until` + filters from search params
- **Navigation**: updates `starts_from`/`starts_until` query params, triggers client-side refetch
- **Views**:
  - **Month**: 7-column grid. Multi-day events as color bars spanning day cells. Events colored by `type_color` from constants.
  - **Week**: 7 columns, hourly rows (00:00–23:00). Events positioned by start/end time.
  - **Agenda**: list grouped by date, only days that have events. Each item shows title, type badge, time range.
- **Filters**: text search, type (combobox), status (select), audience (select). Synced to URL query params.
- **Empty day click**: navigates to `/events/new?date=YYYY-MM-DD`
- **Event click**: navigates to `/events/[id]`
- **"Novo Evento" button**: top-right of filter bar

### Event Detail (`/events/[id]`)

- **Type**: Server Component (fetch) wrapping Client Component tabs
- **Header**: thumbnail image (16:9, with inline upload zone if none set) to the left, title, `type_color` badge, status pill, date range with time, creator name, participants count, location address, actions (edit, cancel/reactivate — creator/staff only)
- **Thumbnail upload**: small drop zone in header. Uploads to `/api/media/`, links to event, sets as thumbnail in one flow. If thumbnail exists, hover shows "Alterar".
- **Tabs**: Participants | Fotos | Highlights
  - **Participants**: paginated list with avatar + username. Creator/staff sees "Adicionar" button (combobox of users). "Sair" button for self-removal. Creator cannot be removed.
  - **Fotos**: 3–4 column grid of photo thumbnails. Upload zone (drag & drop) at the start of the grid — uploads to `/api/media/` then links to event. Thumbnail photo has highlighted border + badge. Hover shows "Definir thumbnail" (creator/staff) and "Desvincular" (X).
  - **Highlights**: vertical list of cards. Each card has text + mini grid of linked photos. Creator/participant can add highlight (textarea + photo selector from event's linked photos). Author/staff/creator can edit or delete. Edit reuses same form pre-filled.

### Create/Edit Event (`/events/new`, `/events/[id]/edit`)

- **Type**: Client Component
- **Form**: react-hook-form + zod, same pattern as login page
- **Fields**:
  - `title` (required, max 255)
  - `description` (optional, textarea)
  - `type` (required, combobox with EventType enum from `/api/events/options/`)
  - `audiences` (required, min 1, multi-select chips from Audience enum)
  - `start_at` (required, datetime picker, future-only on create)
  - `end_at` (required, must be >= start_at)
  - `location` (optional):
    - `name` (optional input)
    - Address search bar + Leaflet map (see below)
- **Edit mode**: all fields optional, `start_at` must be >= existing `end_at` if changed
- **Query param**: `?date=YYYY-MM-DD` pre-fills `start_at` date
- **On success**: redirect to event detail, toast via sonner
- **On error**: toast with detail message

### Location Picker (Leaflet)

- Uses `react-leaflet` + `leaflet` + `leaflet-geosearch`
- Free, no API keys (OpenStreetMap tiles + Nominatim geocoding)
- Search bar: user types address, selects from autocomplete suggestions
- Map renders with draggable pin at selected location
- `address`, `latitude`, `longitude` captured from geocode result and pin position
- Validated via zod: `latitude` (-90 to 90), `longitude` (-180 to 180)
- Pin draggable for manual fine-tuning

## Data Flow

```
Server Component              Client Component
     │                              │
     ├─ fetch (ky) ──→ backend      │
     │                              │
     ├─ props ────→ data            │
     │                              ├─ Server Action ──→ backend
     │                              ├─ React Query (useMutation)
     │                              │    └─ onSuccess: revalidatePath + toast
     │                              │
     └─ revalidate ←────────────────┘
```

## Auth Flow

1. Login form calls Server Action → `/api/auth/login/` (JWT returned as `ev_s_tkn` cookie)
2. Middleware (`proxy.ts`) checks cookie on `(private)` routes, redirects to `/login` if missing
3. `verifySession()` reads cookie, calls `/api/auth/me/` to validate and return user data
4. Server Components call `verifySession()` to get current user for permission checks
5. Server Actions call `verifySession()` to authorize mutations

## Dependencies

| Package | Purpose |
|---|---|
| `react-leaflet` | React wrapper for Leaflet maps |
| `leaflet` | Map rendering (OpenStreetMap) |
| `leaflet-geosearch` | Address search bar with Nominatim provider |
| `@tanstack/react-query` | Mutation cache + revalidation |
| `ky` | Already installed — server-side API client |

All other dependencies (react-hook-form, zod, sonner, date-fns, radix primitives, lucide-react) are already in the project.

## Backend Endpoints Used

| Endpoint | Method | Usage |
|---|---|---|
| `/api/auth/login/` | POST | Login |
| `/api/auth/me/` | GET | Verify session, get user |
| `/api/events/` | GET | Calendar listing with filters |
| `/api/events/` | POST | Create event |
| `/api/events/{id}/` | GET | Event detail |
| `/api/events/{id}/` | PATCH | Update event |
| `/api/events/{id}/` | DELETE | Soft-delete event |
| `/api/events/{id}/cancel/` | POST | Cancel event |
| `/api/events/{id}/reactivate/` | POST | Reactivate event |
| `/api/events/{id}/participants/` | GET | List participants |
| `/api/events/{id}/participants/` | POST | Add participants |
| `/api/events/{id}/participants/{user_id}/` | DELETE | Remove participant |
| `/api/events/{id}/photos/` | GET | List photos |
| `/api/events/{id}/photos/` | POST | Link photo |
| `/api/events/{id}/photos/{photo_pk}/` | DELETE | Unlink photo |
| `/api/events/{id}/thumbnail/` | PUT / DELETE | Set / clear thumbnail |
| `/api/events/{id}/highlights/` | GET / POST | List / create highlights |
| `/api/events/{id}/highlights/{pk}/` | GET / PATCH / DELETE | Detail / edit / delete highlight |
| `/api/events/options/` | GET | Enums (types, audiences, statuses) |
| `/api/media/` | POST | Upload photo |
