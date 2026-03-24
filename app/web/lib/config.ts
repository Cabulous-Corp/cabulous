import 'server-only'

/**
 * Matches the python logic for determining if the environment is production
 */
export const isProduction = () => {
  return process.env.ENVIRONMENT !== 'development' && process.env.ENVIRONMENT !== 'test'
}
/**
 * The frontend URL
 */

export const frontendUrl = (process.env.FRONTEND_URL ?? 'http://localhost:3000').replace(/\/$/, '')
/**
 * The domain to use for the cookie
 */

export const cookieDomain = new URL(frontendUrl).hostname
/**
 * Cookie name
 */

export const cookieName = process.env.COOKIE_NAME ?? 'ev_s_tkn'
/**
 * The server URL
 */

export const serverUrl = (process.env.API_ENDPOINT ?? 'http://localhost:8000').replace(/\/$/, '')
/**
 * The chat backend URL
 */

export const chatUrl = (process.env.CHAT_ENDPOINT ?? 'http://localhost:8001').replace(/\/$/, '')
