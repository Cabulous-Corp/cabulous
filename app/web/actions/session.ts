'use server'

import 'server-only'

// TODO: Re-implementar as ações de sessão no futuro conforme necessário
/*
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { revalidatePath, revalidateTag } from 'next/cache'
import { isRedirectError } from 'next/dist/client/components/redirect-error'
import { fetchAPI } from '@/lib/api'
import { cookieName, cookieDomain, isProduction } from '@/lib/config'
import { User } from '@/hooks/use-user'

export async function logoutAction() { ... }
export async function verifySessionWithoutRedirect() { ... }
export async function verifySessionForOnboarding() { ... }
export async function verifySession() { ... }
export async function getSessions() { ... }
export async function revokeAllSessionsAction() { ... }
export async function revokeOtherSessionsAction() { ... }
export async function deleteAccountAction() { ... }
export async function getOwnershipsAction() { ... }
*/

export async function logoutAction() {
  console.log('Mock logout')
}

export async function verifySessionWithoutRedirect() {
  return null
}

export async function verifySessionForOnboarding() {
  return { id: 'mock-id', email: 'mock@example.com' }
}

export async function verifySession() {
  return { id: 'mock-id', email: 'mock@example.com' }
}

export async function getSessions() {
  return []
}
