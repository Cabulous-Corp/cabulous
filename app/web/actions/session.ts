'use server'

import 'server-only'

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
