'use server'

import 'server-only'
import { api } from '@/lib/api'
import { cookieName } from '@/lib/config'
import { cookies } from 'next/headers'

type LoginRequest = { email: string; password: string }
type LoginResponse = { access: string; refresh: string }
type SessionUser = { id: string; email: string; username: string }

export async function loginRequest(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post('api/auth/login/', { json: data })

  const setCookieHeader = response.headers.get('set-cookie')
  if (setCookieHeader) {
    const cookieStore = await cookies()
    const match = setCookieHeader.match(new RegExp(`${cookieName}=([^;]+)`))
    if (match) {
      cookieStore.set(cookieName, match[1], {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24 * 30,
      })
    }
  }

  return response.json() as Promise<LoginResponse>
}

export async function fetchSession(): Promise<SessionUser | null> {
  try {
    return await api.get('api/auth/me/').json<SessionUser>()
  } catch {
    return null
  }
}
