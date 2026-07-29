'use server'

import 'server-only'
import { api } from '@/lib/api'
import { getEvents, type PaginatedResponse, type EventRead } from '@/lib/api/events'

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

export async function getUserEvents(
  userId: string,
  type: 'created' | 'participating',
): Promise<PaginatedResponse<EventRead>> {
  const params = type === 'created' ? { creator: userId } : { participant: userId }
  return getEvents({ ...params, page_size: 10 })
}
