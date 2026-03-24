import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { cookieName } from './lib/config'

export function proxy(request: NextRequest) {
  const sessionToken = request.cookies.get(cookieName)?.value
  const { pathname } = request.nextUrl

  // Define public paths that don't require authentication
  const publicPaths = [
    '/login',
    '/privacy-terms',
    '/2fa',
    '/verify',
    // Auth related paths
    '/auth/callback',
    '/api/auth',
  ]

  // Check if the current path is public
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))

  if (isPublicPath) {
    return NextResponse.next()
  }

  // If not public and no session token, redirect to login
  if (!sessionToken) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public images (svg, png, jpg, etc.)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
