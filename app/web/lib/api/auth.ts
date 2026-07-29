'use server'

import 'server-only'
import { api } from '@/lib/api'
import { cookieName } from '@/lib/config'
import { cookies } from 'next/headers'

type LoginRequest = { identifier: string; password: string }
type LoginResponse = { access: string; refresh: string; user: SessionUser }
type SessionUser = {
  id: string
  email: string
  username: string
  is_staff: boolean
  onboarding_completed_at: string | null
}

export async function loginRequest(data: LoginRequest): Promise<LoginResponse> {
  const result = await api.post('api/auth/login/', { json: data }).json<LoginResponse>()

  const cookieStore = await cookies()
  cookieStore.set(cookieName, result.access, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30,
  })

  return result
}

export async function fetchSession(): Promise<SessionUser | null> {
  try {
    return await api.get('api/auth/me/').json<SessionUser>()
  } catch {
    return null
  }
}
