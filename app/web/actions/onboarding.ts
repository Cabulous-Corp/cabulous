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

export async function completeOnboarding(data: OnboardingData): Promise<{ error?: string }> {
  try {
    await api.post('api/auth/onboarding/complete/', { json: data }).json()
    revalidatePath('/')
    return {}
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : ''
    return { error: message || 'Erro ao completar onboarding. Tente novamente.' }
  }
}
