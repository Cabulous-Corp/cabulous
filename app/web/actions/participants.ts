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
