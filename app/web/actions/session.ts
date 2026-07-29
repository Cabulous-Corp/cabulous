'use server'

import 'server-only'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { cookieName } from '@/lib/config'
import { loginRequest, fetchSession } from '@/lib/api/auth'

type LoginRequest = { email: string; password: string }
type SessionUser = { id: string; email: string; username: string }

export async function loginAction(data: LoginRequest): Promise<{ error?: string }> {
  try {
    await loginRequest(data)
    return {}
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    if (err.response?.status === 401) {
      return { error: 'E-mail ou senha invalidos.' }
    }
    return { error: 'Erro inesperado. Tente novamente.' }
  }
}

export async function logoutAction(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(cookieName)
  redirect('/login')
}

export async function verifySession(): Promise<SessionUser> {
  const user = await fetchSession()
  if (!user) {
    redirect('/login')
  }
  return user
}

export async function verifySessionWithoutRedirect(): Promise<SessionUser | null> {
  return fetchSession()
}

export async function verifySessionForOnboarding(): Promise<SessionUser | null> {
  return fetchSession()
}

export async function getSessions(): Promise<SessionUser[]> {
  const user = await fetchSession()
  return user ? [user] : []
}
