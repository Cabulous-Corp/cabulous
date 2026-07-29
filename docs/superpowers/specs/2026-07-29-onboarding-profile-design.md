# Onboarding, User Profile, and Event Host — Design Doc

**Date**: 2026-07-29
**Status**: Approved

## Scope

Three connected features:

1. **Onboarding wizard** — step-by-step flow for new users to complete their profile before accessing the app
2. **User profile page** — public profile with avatar, banner, bio, links, and activity tabs
3. **Event host (anfitriao)** — new backend field so events show who actually organizes them

## Onboarding Wizard

### Backend (already exists)

- `POST /api/auth/onboarding/complete/` accepts: `first_name`, `last_name`, `username`, `email`, `new_password`, `bio`, `discord_username`, `phone_number`, `avatar_key`, `banner_key`
- Sets `onboarding_completed_at = now` and `password_defined_at = now`
- `GET /api/auth/me/` returns `onboarding_completed_at` — null means pending onboarding

### Frontend flow

```
Login → POST /api/auth/login/ → JWT stored as ev_s_tkn cookie
     → verifySession() calls GET /api/auth/me/
     → onboarding_completed_at == null → redirect /onboarding
     → onboarding_completed_at != null → redirect /
```

### 5 Steps

| Step | Question | Fields | Required |
|------|----------|--------|----------|
| 1 | "Quem e voce?" | `first_name`, `last_name`, `username`, avatar, banner | All except avatar/banner |
| 2 | "Conte sobre voce" | `bio` | No |
| 3 | "Como te encontram?" | `email`, `discord_username`, `phone_number` | email only |
| 4 | "Sua senha" | `new_password` | Yes |
| 5 | Preview | Summary card | Confirm button |

### UI

- Centered card layout (same as current onboarding layout)
- Progress bar at top: `● ○ ○ ○ ○ 1 de 5`
- One question per screen with input(s)
- Animated transitions between steps (framer-motion)
- "Voltar" and "Continuar" buttons
- Avatar/banner: file upload zone with preview
- Step 5: shows a mock profile card with the gathered data
- On confirm: `POST /api/auth/onboarding/complete/` → redirect `/`

### States

- **Loading**: skeleton/spinner while uploading files
- **Validation**: inline errors below each field (zod)
- **Error**: toast on submit failure, retry button
- **Already completed**: if user somehow reaches /onboarding with onboarding completed, redirect to /

## User Profile Page

### Route

`/users/[id]` — Server Component fetching via `GET /api/users/{id}/`

### Layout

```
┌──────────────────────────────────────────┐
│  ┌──────────────────────────────────────┐│
│  │            banner (3:1)              ││
│  │     ┌────┐                           ││
│  │     │ AV │  Nome Completo            ││
│  │     └────┘  @username                ││
│  └──────────────────────────────────────┘│
│                                          │
│  Bio text here...                        │
│                                          │
│  [Discord] [GitHub] [Telefone]           │
│                                          │
│  [Editar perfil]  (own profile only)     │
│                                          │
│  ┌──────────────────────────────────────┐│
│  │ [Eventos] [Participando]             ││
│  ├──────────────────────────────────────┤│
│  │  ┌──────┐ ┌──────┐ ┌──────┐         ││
│  │  │Event │ │Event │ │Event │         ││
│  │  │card  │ │card  │ │card  │         ││
│  │  └──────┘ └──────┘ └──────┘         ││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### Data

- Profile: `GET /api/users/{id}/` → `UserSerializer` fields
- Events created: `GET /api/events/?creator={userId}&page_size=10`
- Participating: `GET /api/events/?participant={userId}&page_size=10`

### Edit Profile (own profile only)

- Button triggers Sheet/Dialog with form
- Editable fields: `first_name`, `last_name`, `bio`, `discord_username`, `phone_number`, avatar, banner
- `avatar_key` / `banner_key` via `POST /api/users/uploads/signed-url/` + upload
- Submit: `PATCH /api/users/{id}/`

### Navigation

- Sidebar UserMenu → "Meu Perfil" links to `/users/{userId}`
- Clicking any user avatar/name (participants list, event header) → `/users/{id}`

## Event Host (Anfitriao)

### Backend changes

**Model** (`service/events/models.py`):
```python
hosts = models.ManyToManyField(User, related_name='hosted_events', blank=True)
```

**Migration**: auto-generated via `makemigrations`

**Serializer changes**:

`EventReadSerializer` — add:
```python
hosts = serializers.SerializerMethodField()
def get_hosts(self, obj):
    return [{"id": u.id, "username": u.username} for u in obj.hosts.all()]
```

`EventCreateSerializer` / `EventUpdateSerializer` — add:
```python
host_ids = serializers.ListField(
    child=serializers.UUIDField(), required=False, default=list
)
```

**Service** (`service/events/services/events.py`):

In `create_event`: after creating the event, add hosts via `event.hosts.set(host_ids)` and auto-add each host as participant.

In `update_event`: if `host_ids` in data, update hosts and ensure all hosts are participants.

**Filter** (`service/events/filters.py`):

Add `host = django_filters.UUIDFilter(method='filter_by_host')` that filters events where the given user is a host.

### Frontend changes

**Create/Edit event form**:

Add "Anfitrioes" field — combobox to search and select users (requires a user search endpoint or manual UUID input for now — ponytail: use manual input or wait for `/api/users/?search=`).

**Event detail header**:

Show hosts below the title/type: "Anfitriao por @user1, @user2".

**Participants tab**:

Hosts get a badge/indicator "Anfitriao" next to their name.

---

## Files

```
app/web/
  app/(onboarding)/
    onboarding/
      page.tsx                         # Server component — checks onboarding status
      _components/
        OnboardingWizard.tsx           # Client — manages step state, progress bar
        StepProfile.tsx                # Step 1: name, username, avatar, banner
        StepBio.tsx                    # Step 2: bio
        StepContact.tsx                # Step 3: email, discord, phone
        StepPassword.tsx               # Step 4: password
        StepPreview.tsx                # Step 5: profile preview + confirm
        OnboardingProgress.tsx         # Progress bar component

  app/(private)/(pages)/(main)/
    users/
      [id]/
        page.tsx                       # Server component — fetches user profile
        _components/
          ProfileHeader.tsx            # Banner, avatar, name, username
          ProfileInfo.tsx              # Bio, links, edit button
          ProfileEditSheet.tsx         # Edit profile form (Sheet)
          ProfileEventsTab.tsx         # Events + Participating tabs

service/
  events/
    models.py                          # Add hosts M2M field
    serializers.py                     # Add hosts to read, host_ids to write
    filters.py                         # Add host filter
    services/
      events.py                        # Auto-add hosts as participants
    migrations/
      XXXX_add_hosts.py                # Auto-generated
```
