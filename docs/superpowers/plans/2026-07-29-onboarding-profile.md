# Onboarding, Profile & Anfitriao — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build onboarding wizard, user profile page, and event host (anfitriao) feature — backend model + frontend UI.

**Architecture:** Backend: add `hosts` M2M to Event model, update serializers/services/filters. Frontend: onboarding wizard (5-step react-hook-form), profile page (Server Component + tabs), host selector in event forms, navigation updates.

**Tech Stack:** Django + DRF (backend), Next.js 16 + React 19 + Tailwind v4 + shadcn/ui (frontend)

## Global Constraints

- Backend: `cd service` for all commands, `uv run pytest` for tests, `uv run python manage.py` for Django commands
- Backend: no editing generated migrations, ruff line-length 100, no type-checking migrations
- Frontend: `cd app/web` for all commands, `bun` package manager
- Frontend: `'use server'` imports start with `'use server'` + `'server-only'`, no `any` types
- Frontend: Portuguese labels, Tailwind only, page-exclusive components in `_components/`
- Backend quality: `uv run ruff check . && uv run mypy . && uv run pytest --tb=short -q`
- Frontend quality: `bun run lint && bun run typecheck && bun run build && bun run test:coverage`

---

### Task 1: Backend — Add hosts M2M to Event model

**Files:**
- Modify: `service/events/models.py`
- Create: `service/events/migrations/XXXX_add_hosts.py` (auto-generated)

**Interfaces:**
- Consumes: Existing `Event` model, `User` model
- Produces: `Event.hosts` ManyToManyField(User, related_name='hosted_events', blank=True)

- [ ] **Step 1: Add hosts field to Event model**

Edit `service/events/models.py`. Add after the `creator` field:

```python
hosts = models.ManyToManyField(
    settings.AUTH_USER_MODEL,
    related_name="hosted_events",
    blank=True,
)
```

- [ ] **Step 2: Generate migration**

```bash
cd service
uv run python manage.py makemigrations events --name add_hosts
```

- [ ] **Step 3: Run migration on local DB**

```bash
cd service
$env:DATABASE__HOST="localhost"
$env:DATABASE__PORT="5433"
$env:REDIS__URL="redis://localhost:6380/1"
$env:SECRET_KEY="dev-secret-key-for-local"
uv run python manage.py migrate events
```

- [ ] **Step 4: Verify model loads correctly**

```bash
cd service
$env:DATABASE__HOST="localhost"
$env:DATABASE__PORT="5433"
$env:REDIS__URL="redis://localhost:6380/1"
$env:SECRET_KEY="dev-secret-key-for-local"
uv run python manage.py check
```

- [ ] **Step 5: Commit**

```bash
git add service/events/models.py service/events/migrations/
git commit -m "feat: add hosts M2M field to Event model"
```

---

### Task 2: Backend — Update serializers for hosts

**Files:**
- Modify: `service/events/serializers.py`

**Interfaces:**
- Consumes: `Event.hosts` M2M field from Task 1
- Produces: `EventReadSerializer.get_hosts()`, `host_ids` in create/update serializers

- [ ] **Step 1: Add host_ids to EventCreateSerializer**

In `EventCreateSerializer`, add a new field after `audiences`:

```python
host_ids = serializers.ListField(
    child=serializers.UUIDField(),
    required=False,
    default=list,
    write_only=True,
)
```

- [ ] **Step 2: Add host_ids to EventUpdateSerializer**

In `EventUpdateSerializer`, add after `audiences`:

```python
host_ids = serializers.ListField(
    child=serializers.UUIDField(),
    required=False,
    write_only=True,
)
```

- [ ] **Step 3: Add hosts to EventReadSerializer**

Add a `hosts` SerializerMethodField:

```python
hosts = serializers.SerializerMethodField()

def get_hosts(self, obj):
    return [
        {"id": str(u.id), "username": u.username}
        for u in obj.hosts.all()
    ]
```

Add `"hosts"` to the `fields` list or `Meta.fields`.

- [ ] **Step 4: Add HostReadSerializer for the nested list (optional, cleaner)**

```python
class HostReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
```

Then in EventReadSerializer:

```python
hosts = HostReadSerializer(many=True, read_only=True, source="hosts.all")
```

- [ ] **Step 5: Commit**

```bash
git add service/events/serializers.py
git commit -m "feat: add hosts to event serializers"
```

---

### Task 3: Backend — Update services and filter for hosts

**Files:**
- Modify: `service/events/services/events.py`
- Modify: `service/events/filters.py`

**Interfaces:**
- Consumes: `host_ids` from serializers (Task 2), `Event.hosts` (Task 1)
- Produces: `create_event` / `update_event` handle hosts + auto-participant, `EventFilter.host`

- [ ] **Step 1: Update create_event to handle hosts**

In `service/events/services/events.py`, in `create_event` function, after creating the event and participants, add:

```python
host_ids = data.get("host_ids", [])
if host_ids:
    event.hosts.set(host_ids)
    add_participants(event, host_ids)
```

- [ ] **Step 2: Update update_event to handle hosts**

In `update_event`, after updating fields, add:

```python
if "host_ids" in data:
    host_ids = data["host_ids"]
    event.hosts.set(host_ids)
    add_participants(event, host_ids)
```

Ensure `add_participants` is imported from `.relations`.

- [ ] **Step 3: Add host filter**

In `service/events/filters.py`, add:

```python
host = UUIDFilter(method="filter_by_host")

def filter_by_host(self, queryset, name, value):
    return queryset.filter(hosts__id=value)
```

Also import `UUIDFilter` from `django_filters` if not already imported.

- [ ] **Step 4: Commit**

```bash
git add service/events/services/events.py service/events/filters.py
git commit -m "feat: handle hosts in event services and add host filter"
```

---

### Task 4: Backend — Tests and quality

**Files:**
- Modify: `service/events/tests/` — add tests for host functionality

**Interfaces:**
- Consumes: All host-related backend changes (Tasks 1-3)
- Produces: Passing test suite

- [ ] **Step 1: Run existing event tests to verify nothing broke**

```bash
cd service
$env:DATABASE__HOST="localhost"
$env:DATABASE__PORT="5433"
$env:REDIS__URL="redis://localhost:6380/1"
$env:SECRET_KEY="dev-secret-key-for-local"
uv run pytest events/tests/ -q --tb=short
```

- [ ] **Step 2: Run ruff and mypy**

```bash
cd service
uv run ruff check events/
uv run mypy events/
```

- [ ] **Step 3: Commit (if all green)**

```bash
git add -A
git commit -m "test: verify existing tests pass after hosts feature"
```

---

### Task 5: Frontend — Session redirect for onboarding

**Files:**
- Modify: `app/web/actions/session.ts`

**Interfaces:**
- Consumes: `fetchSession` from `@/lib/api/auth`
- Produces: `verifySession()` redirects to `/onboarding` if onboarding not completed

- [ ] **Step 1: Update verifySession to check onboarding**

Edit `app/web/actions/session.ts`. Update `verifySession`:

```typescript
export async function verifySession(): Promise<SessionUser> {
  const user = await fetchSession()
  if (!user) {
    redirect('/login')
  }
  if (!user.onboarding_completed_at) {
    redirect('/onboarding')
  }
  return user
}
```

Update the `SessionUser` type to include `onboarding_completed_at`:

```typescript
type SessionUser = {
  id: string
  email: string
  username: string
  is_staff: boolean
  onboarding_completed_at: string | null
}
```

- [ ] **Step 2: Update fetchSession return type in lib/api/auth.ts**

In `app/web/lib/api/auth.ts`, update `SessionUser` to include `onboarding_completed_at: string | null`.

- [ ] **Step 3: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 4: Commit**

```bash
git add app/web/actions/session.ts app/web/lib/api/auth.ts
git commit -m "feat: redirect to onboarding when onboarding not completed"
```

---

### Task 6: Frontend — Onboarding wizard shell + progress bar

**Files:**
- Modify: `app/web/app/(onboarding)/layout.tsx`
- Modify: `app/web/app/(onboarding)/onboarding/page.tsx`
- Create: `app/web/app/(onboarding)/onboarding/_components/OnboardingWizard.tsx`
- Create: `app/web/app/(onboarding)/onboarding/_components/OnboardingProgress.tsx`

**Interfaces:**
- Consumes: Session check from Task 5
- Produces: Wizard shell with step management, progress bar, react-hook-form context

- [ ] **Step 1: Update onboarding page to check session**

```typescript
// app/web/app/(onboarding)/onboarding/page.tsx
import { verifySessionWithoutRedirect } from '@/actions/session'
import { redirect } from 'next/navigation'
import { OnboardingWizard } from './_components/OnboardingWizard'

export default async function OnboardingPage() {
  const user = await verifySessionWithoutRedirect()
  if (user?.onboarding_completed_at) {
    redirect('/')
  }
  return <OnboardingWizard />
}
```

- [ ] **Step 2: Create OnboardingWizard (state manager)**

```typescript
// app/web/app/(onboarding)/onboarding/_components/OnboardingWizard.tsx
'use client'

import { useState } from 'react'
import { useForm, FormProvider } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { OnboardingProgress } from './OnboardingProgress'
import { StepProfile } from './StepProfile'
import { StepBio } from './StepBio'
import { StepContact } from './StepContact'
import { StepPassword } from './StepPassword'
import { StepPreview } from './StepPreview'
import { completeOnboarding } from '@/actions/onboarding'

const onboardingSchema = z.object({
  first_name: z.string().min(1, 'Nome e obrigatorio.'),
  last_name: z.string().min(1, 'Sobrenome e obrigatorio.'),
  username: z.string().min(3, 'Username deve ter pelo menos 3 caracteres.'),
  avatar_key: z.string().optional(),
  banner_key: z.string().optional(),
  bio: z.string().optional(),
  email: z.string().email('Email invalido.').min(1, 'Email e obrigatorio.'),
  discord_username: z.string().optional(),
  phone_number: z.string().optional(),
  new_password: z.string().min(8, 'Senha deve ter pelo menos 8 caracteres.'),
})

export type OnboardingFormValues = z.infer<typeof onboardingSchema>

const STEPS = [
  { id: 1, label: 'Perfil' },
  { id: 2, label: 'Bio' },
  { id: 3, label: 'Contato' },
  { id: 4, label: 'Senha' },
  { id: 5, label: 'Confirmar' },
]

export function OnboardingWizard() {
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      username: '',
      bio: '',
      email: '',
      discord_username: '',
      phone_number: '',
      new_password: '',
    },
    mode: 'onChange',
  })

  const handleComplete = async () => {
    setSubmitting(true)
    setError('')
    try {
      const values = form.getValues()
      await completeOnboarding({
        first_name: values.first_name,
        last_name: values.last_name,
        username: values.username,
        bio: values.bio || undefined,
        email: values.email,
        discord_username: values.discord_username || undefined,
        phone_number: values.phone_number || undefined,
        new_password: values.new_password,
        avatar_key: values.avatar_key || undefined,
        banner_key: values.banner_key || undefined,
      })
      router.push('/')
    } catch (e: unknown) {
      const err = e as { message?: string }
      setError(err.message ?? 'Erro ao completar onboarding.')
      setSubmitting(false)
    }
  }

  return (
    <FormProvider {...form}>
      <div className="w-full max-w-md mx-auto space-y-6">
        <OnboardingProgress steps={STEPS} currentStep={step} />

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {step === 1 && <StepProfile onNext={() => setStep(2)} />}
            {step === 2 && <StepBio onNext={() => setStep(3)} onBack={() => setStep(1)} />}
            {step === 3 && <StepContact onNext={() => setStep(4)} onBack={() => setStep(2)} />}
            {step === 4 && <StepPassword onNext={() => setStep(5)} onBack={() => setStep(3)} />}
            {step === 5 && (
              <StepPreview
                onBack={() => setStep(4)}
                onComplete={handleComplete}
                submitting={submitting}
                error={error}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </FormProvider>
  )
}
```

- [ ] **Step 3: Create OnboardingProgress**

```typescript
// app/web/app/(onboarding)/onboarding/_components/OnboardingProgress.tsx
'use client'

interface Step {
  id: number
  label: string
}

interface Props {
  steps: Step[]
  currentStep: number
}

export function OnboardingProgress({ steps, currentStep }: Props) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{currentStep} de {steps.length}</span>
      </div>
      <div className="flex gap-1">
        {steps.map((s) => (
          <div
            key={s.id}
            className={`h-1 flex-1 rounded-full transition-colors ${
              s.id <= currentStep ? 'bg-primary' : 'bg-muted'
            }`}
          />
        ))}
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
git add app/web/app/\(onboarding\)/
git commit -m "feat: add onboarding wizard shell with progress bar"
```

---

### Task 7: Frontend — Onboarding steps 1-2 (Profile + Bio)

**Files:**
- Create: `app/web/app/(onboarding)/onboarding/_components/StepProfile.tsx`
- Create: `app/web/app/(onboarding)/onboarding/_components/StepBio.tsx`

**Interfaces:**
- Consumes: react-hook-form context from OnboardingWizard
- Produces: Profile step (name, username, avatar, banner upload) and Bio step (textarea)

- [ ] **Step 1: Create StepProfile**

```typescript
// app/web/app/(onboarding)/onboarding/_components/StepProfile.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
}

export function StepProfile({ onNext }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

  const handleNext = async () => {
    const valid = await trigger(['first_name', 'last_name', 'username'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Quem e voce?</h2>
        <p className="text-sm text-muted-foreground mt-1">Conte um pouco sobre voce.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Nome completo *</label>
          <div className="flex gap-3 mt-1">
            <Input {...register('first_name')} placeholder="Nome" error={errors.first_name?.message} />
            <Input {...register('last_name')} placeholder="Sobrenome" error={errors.last_name?.message} />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">Username *</label>
          <Input
            {...register('username')}
            placeholder="@seunome"
            className="mt-1"
            error={errors.username?.message}
          />
        </div>

        <div>
          <label className="text-sm font-medium">Foto de perfil</label>
          <p className="text-xs text-muted-foreground mt-1">ponytail: avatar upload via signed-url — skip for now, add later</p>
        </div>
      </div>

      <Button onClick={handleNext} className="w-full">Continuar</Button>
    </div>
  )
}
```

- [ ] **Step 2: Create StepBio**

```typescript
// app/web/app/(onboarding)/onboarding/_components/StepBio.tsx
'use client'

import { useFormContext } from 'react-hook-form'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepBio({ onNext, onBack }: Props) {
  const { register } = useFormContext<OnboardingFormValues>()

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Conte sobre voce</h2>
        <p className="text-sm text-muted-foreground mt-1">Uma breve descricao para seu perfil.</p>
      </div>

      <Textarea
        {...register('bio')}
        placeholder="Escreva algo sobre voce..."
        rows={4}
        maxLength={500}
      />

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={onNext} className="flex-1">Continuar</Button>
      </div>
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
git add app/web/app/\(onboarding\)/onboarding/_components/StepProfile.tsx app/web/app/\(onboarding\)/onboarding/_components/StepBio.tsx
git commit -m "feat: add onboarding steps 1-2 (profile + bio)"
```

---

### Task 8: Frontend — Onboarding steps 3-5 (Contact, Password, Preview)

**Files:**
- Create: `app/web/app/(onboarding)/onboarding/_components/StepContact.tsx`
- Create: `app/web/app/(onboarding)/onboarding/_components/StepPassword.tsx`
- Create: `app/web/app/(onboarding)/onboarding/_components/StepPreview.tsx`

**Interfaces:**
- Consumes: react-hook-form context
- Produces: Contact step (email, discord, phone), Password step, Preview step (profile card + confirm)

- [ ] **Step 1: Create StepContact**

```typescript
'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepContact({ onNext, onBack }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

  const handleNext = async () => {
    const valid = await trigger(['email'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Como te encontram?</h2>
        <p className="text-sm text-muted-foreground mt-1">Seus contatos.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Email *</label>
          <Input {...register('email')} placeholder="seu@email.com" className="mt-1" error={errors.email?.message} type="email" />
        </div>
        <div>
          <label className="text-sm font-medium">Discord</label>
          <Input {...register('discord_username')} placeholder="usuario#0000" className="mt-1" />
        </div>
        <div>
          <label className="text-sm font-medium">Telefone</label>
          <Input {...register('phone_number')} placeholder="(11) 99999-9999" className="mt-1" />
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={handleNext} className="flex-1">Continuar</Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create StepPassword**

```typescript
'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepPassword({ onNext, onBack }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

  const handleNext = async () => {
    const valid = await trigger(['new_password'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Sua senha</h2>
        <p className="text-sm text-muted-foreground mt-1">Crie uma senha segura para sua conta.</p>
      </div>

      <Input
        {...register('new_password')}
        type="password"
        placeholder="Minimo 8 caracteres"
        error={errors.new_password?.message}
      />

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={handleNext} className="flex-1">Continuar</Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create StepPreview**

```typescript
'use client'

import { useFormContext } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card } from '@/components/ui/card'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onBack: () => void
  onComplete: () => void
  submitting: boolean
  error: string
}

export function StepPreview({ onBack, onComplete, submitting, error }: Props) {
  const { getValues } = useFormContext<OnboardingFormValues>()
  const values = getValues()
  const initials = `${values.first_name?.[0] ?? ''}${values.last_name?.[0] ?? ''}`.toUpperCase()

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Seu perfil</h2>
        <p className="text-sm text-muted-foreground mt-1">Assim que voce vai aparecer.</p>
      </div>

      <Card className="p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Avatar className="size-16">
            <AvatarFallback className="text-lg">{initials || '?'}</AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold text-lg">{values.first_name} {values.last_name}</h3>
            <p className="text-sm text-muted-foreground">@{values.username}</p>
          </div>
        </div>
        {values.bio && <p className="text-sm">{values.bio}</p>}
        <div className="text-xs text-muted-foreground space-y-0.5">
          <p>{values.email}</p>
          {values.discord_username && <p>Discord: {values.discord_username}</p>}
          {values.phone_number && <p>Tel: {values.phone_number}</p>}
        </div>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={onComplete} disabled={submitting} className="flex-1">
          {submitting ? 'Salvando...' : 'Concluir!'}
        </Button>
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
git add app/web/app/\(onboarding\)/onboarding/_components/
git commit -m "feat: add onboarding steps 3-5 (contact, password, preview)"
```

---

### Task 9: Frontend — Onboarding complete server action

**Files:**
- Create: `app/web/actions/onboarding.ts`

**Interfaces:**
- Consumes: `api` from `@/lib/api`
- Produces: `completeOnboarding(data)` → POST `/api/auth/onboarding/complete/`

- [ ] **Step 1: Create onboarding action**

```typescript
// app/web/actions/onboarding.ts
'use server'

import 'server-only'
import { api } from '@/lib/api'
import { revalidatePath } from 'next/cache'

interface OnboardingData {
  first_name: string
  last_name: string
  username: string
  email: string
  new_password: string
  bio?: string
  discord_username?: string
  phone_number?: string
  avatar_key?: string
  banner_key?: string
}

export async function completeOnboarding(data: OnboardingData) {
  await api.post('api/auth/onboarding/complete/', { json: data }).json()
  revalidatePath('/')
}
```

- [ ] **Step 2: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 3: Commit**

```bash
git add app/web/actions/onboarding.ts
git commit -m "feat: add onboarding complete server action"
```

---

### Task 10: Frontend — User profile page (header + info + edit)

**Files:**
- Create: `app/web/app/(private)/(pages)/(main)/users/[id]/page.tsx`
- Create: `app/web/app/(private)/(pages)/(main)/users/[id]/_components/ProfileHeader.tsx`
- Create: `app/web/app/(private)/(pages)/(main)/users/[id]/_components/ProfileInfo.tsx`
- Create: `app/web/app/(private)/(pages)/(main)/users/[id]/_components/ProfileEditSheet.tsx`
- Create: `app/web/lib/api/users.ts`

**Interfaces:**
- Consumes: `GET /api/users/{id}/` for profile data, `api` from `@/lib/api`
- Produces: Profile page with banner, avatar, bio, links, edit sheet

- [ ] **Step 1: Create users API fetch**

```typescript
// app/web/lib/api/users.ts
'use server'

import 'server-only'
import { api } from '@/lib/api'

export interface UserProfile {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  bio: string
  avatar: string | null
  banner: string | null
  discord_username: string
  phone_number: string
  is_active: boolean
}

export async function getUser(id: string): Promise<UserProfile> {
  return api.get(`api/users/${id}/`).json<UserProfile>()
}
```

- [ ] **Step 2: Create profile page (server component)**

```typescript
// app/web/app/(private)/(pages)/(main)/users/[id]/page.tsx
import { getUser } from '@/lib/api/users'
import { verifySessionWithoutRedirect } from '@/actions/session'
import { ProfileClient } from './_components/ProfileClient'
import { notFound } from 'next/navigation'

interface Props {
  params: Promise<{ id: string }>
}

export default async function UserProfilePage({ params }: Props) {
  const { id } = await params
  const [profile, sessionUser] = await Promise.all([
    getUser(id).catch(() => null),
    verifySessionWithoutRedirect(),
  ])
  if (!profile) notFound()
  const isOwn = sessionUser?.id === profile.id
  return <ProfileClient profile={profile} isOwn={isOwn} />
}
```

- [ ] **Step 3: Create ProfileClient + ProfileHeader + ProfileInfo**

Create `ProfileClient.tsx`: wraps ProfileHeader and ProfileInfo in a client component, passes profile data + isOwn.

Create `ProfileHeader.tsx`: banner background (3:1), avatar overlapping left side, name + @username. Banner/avatar URLs use `NEXT_PUBLIC_MEDIA_URL` prefix.

Create `ProfileInfo.tsx`: bio text, contact links (Discord, phone), edit button (if isOwn) that opens ProfileEditSheet.

- [ ] **Step 4: Create ProfileEditSheet**

Sheet/Dialog with form for editing: first_name, last_name, bio, discord_username, phone_number. Submit via `PATCH /api/users/{id}/`.

- [ ] **Step 5: Check typecheck + build**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 6: Commit**

```bash
git add app/web/lib/api/users.ts app/web/app/\(private\)/\(pages\)/\(main\)/users/
git commit -m "feat: add user profile page with edit sheet"
```

---

### Task 11: Frontend — Profile activity tabs

**Files:**
- Create: `app/web/app/(private)/(pages)/(main)/users/[id]/_components/ProfileTabs.tsx`
- Modify: `app/web/lib/api/users.ts` (add activity fetch functions)

**Interfaces:**
- Consumes: `GET /api/events/?creator={id}` and `GET /api/events/?participant={id}`
- Produces: Tabs with event mini-cards

- [ ] **Step 1: Add activity fetch to users API**

In `app/web/lib/api/users.ts`, add:

```typescript
import type { PaginatedResponse, EventRead } from '@/lib/api/events'
import { getEvents } from '@/lib/api/events'

export async function getUserEvents(userId: string, type: 'created' | 'participating') {
  const params = type === 'created' ? { creator: userId } : { participant: userId }
  return getEvents({ ...params, page_size: 10 })
}
```

- [ ] **Step 2: Create ProfileTabs**

Tabs: "Eventos" and "Participando". Each tab fetches events and renders mini cards with: title, date, type badge (colored), status.

Use existing `EventRead` types. Click navigates to `/events/[id]`.

- [ ] **Step 3: Check typecheck**

```bash
cd app/web; bun run typecheck
```

- [ ] **Step 4: Commit**

```bash
git add app/web/lib/api/users.ts app/web/app/\(private\)/\(pages\)/\(main\)/users/
git commit -m "feat: add profile activity tabs (events + participating)"
```

---

### Task 12: Frontend — Anfitriao in event detail and forms

**Files:**
- Modify: `app/web/app/(private)/(pages)/(main)/events/[id]/_components/EventHeader.tsx` (show hosts)
- Modify: `app/web/app/(private)/(pages)/(main)/events/new/_components/EventForm.tsx` (add host selector)
- Modify: `app/web/app/(private)/(pages)/(main)/events/[id]/edit/_components/EventEditForm.tsx` (add host selector)
- Modify: `app/web/lib/api/events.ts` (add `hosts` to `EventRead` type)
- Modify: `app/web/actions/events.ts` (add `host_ids` to `CreateEventInput`)

**Interfaces:**
- Consumes: Backend hosts field (Tasks 1-3)
- Produces: Hosts displayed in event detail, host selector in create/edit forms

- [ ] **Step 1: Update EventRead type**

In `app/web/lib/api/events.ts`, add to `EventRead`:

```typescript
hosts: { id: string; username: string }[]
```

- [ ] **Step 2: Update CreateEventInput**

In `app/web/actions/events.ts`, add to `CreateEventInput`:

```typescript
host_ids?: string[]
```

And pass `host_ids` in the body if present.

- [ ] **Step 3: Update EventHeader to show hosts**

In the detail EventHeader, below the title/type/status line, add:

```tsx
{event.hosts.length > 0 && (
  <p className="text-sm text-muted-foreground">
    Anfitriao: {event.hosts.map((h) => h.username).join(', ')}
  </p>
)}
```

- [ ] **Step 4: Add host selector to create/edit forms**

In EventForm and EventEditForm, add a field for selecting hosts. For now: manual UUID input text field (ponytail: needs user search endpoint). Label: "Anfitrioes".

- [ ] **Step 5: Check typecheck + build**

```bash
cd app/web; bun run typecheck && bun run build
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add anfitriao display and selector to event pages"
```

---

### Task 13: Frontend — Navigation links and polish

**Files:**
- Modify: `app/web/app/(private)/(pages)/(main)/main-layout-client.tsx` (add Meu Perfil)
- Modify: `app/web/components/layout/UserMenu.tsx` (add profile link)
- Modify: `app/web/app/(private)/(pages)/(main)/events/[id]/_components/ParticipantsList.tsx` (link usernames to profiles)

**Interfaces:**
- Consumes: Session user for profile link
- Produces: Profile navigation from sidebar and UserMenu, participant name links

- [ ] **Step 1: Add "Meu Perfil" to sidebar UserMenu or main layout**

Read `UserMenu.tsx` and add a link to `/users/{userId}`. The userId comes from the session user.

- [ ] **Step 2: Make participant names linkable**

In ParticipantsList, wrap `p.username` in `<a href={/users/${p.user}}>`.

- [ ] **Step 3: Check typecheck + build**

```bash
cd app/web; bun run typecheck && bun run build
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add profile navigation links"
```

---

### Task 14: Build verification, shadcn vanilla reset, and polish

**Files:**
- Modify: `app/web/app/globals.css` — reset to shadcn vanilla theme
- Modify: `app/web/components.json` — reset to vanilla shadcn config

**Interfaces:**
- Consumes: All previous tasks
- Produces: Full passing CI quality check with vanilla shadcn theme

- [ ] **Step 1: Reinstall shadcn with vanilla defaults**

```bash
cd app/web
# Initialize fresh shadcn with default zinc/neutral theme
bunx shadcn@latest init --defaults --force
```

This resets `components.json` and `globals.css` to the default shadcn theme while keeping existing components intact.

- [ ] **Step 2: Run full quality pipeline**

```bash
cd app/web; bun run lint && bun run typecheck && bun run build && bun run test:coverage
```

- [ ] **Step 3: Fix any issues**

If shadcn reinit broke any theme variable references, fix them. If build fails, fix systematically.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: reset shadcn to vanilla theme, pass quality pipeline"
```

---

## Plan Summary

```
Task 1:  Backend — Add hosts M2M field     (5 min)
Task 2:  Backend — Serializers for hosts   (5 min)
Task 3:  Backend — Services + filter       (5 min)
Task 4:  Backend — Tests and quality       (5 min)
Task 5:  Frontend — Session redirect       (5 min)
Task 6:  Frontend — Wizard shell           (10 min)
Task 7:  Frontend — Steps 1-2              (10 min)
Task 8:  Frontend — Steps 3-5              (10 min)
Task 9:  Frontend — Onboarding action      (5 min)
Task 10: Frontend — Profile page           (15 min)
Task 11: Frontend — Profile tabs           (10 min)
Task 12: Frontend — Anfitriao UI           (10 min)
Task 13: Frontend — Navigation links       (5 min)
Task 14: Shadcn reset + quality pipeline   (10 min)
```

**Dependency chain:** 1 → 2 → 3 → 4 | 5 → 6 → 7 → 8 → 9 | 10 → 11 | 12 | 13 | 14 (final)
