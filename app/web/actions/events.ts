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
