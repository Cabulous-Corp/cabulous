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
