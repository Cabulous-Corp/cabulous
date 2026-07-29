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
