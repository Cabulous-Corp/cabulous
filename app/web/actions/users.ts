'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { api } from '@/lib/api'

interface UpdateProfileInput {
  first_name?: string
  last_name?: string
  bio?: string
  discord_username?: string
  phone_number?: string
}

export async function updateUserProfile(id: string, data: UpdateProfileInput): Promise<void> {
  await api.patch(`api/users/${id}/`, { json: data }).json()
  revalidatePath(`/users/${id}`)
}
