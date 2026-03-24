'use server'

import 'server-only'

import { context, propagation } from '@opentelemetry/api'
import { yellow } from 'colorette'
import ky, { AfterResponseHook, BeforeRequestHook, BeforeErrorHook } from 'ky'
import { cookies, headers } from 'next/headers'
import { chatUrl, cookieName, serverUrl } from '@/lib/config'
import { safeJsonParse } from '@/lib/json'
import { logger } from '@/lib/logger'

const _beforeRequestHooks: BeforeRequestHook[] = [
  async (request: Request) => {
    // Set a traceId for the request
    const traceId = crypto.randomUUID()
    request.headers.set('X-Trace-Id', traceId)
    request.headers.set('X-Timestamp', Date.now().toString())

    logger.info(`[RQT] tid=${traceId} [${request.method}] ${request.url}`)

    const cookieStore = await cookies()
    const sessionToken = cookieStore.get(cookieName)

    if (sessionToken?.value) {
      request.headers.set('Cookie', `${cookieName}=${sessionToken.value}`)
    }

    // Forward User-Agent and IP to the backend
    const reqHeaders = await headers()
    const userAgent = reqHeaders.get('user-agent')
    const forwardedFor = reqHeaders.get('x-forwarded-for')
    const realIp = reqHeaders.get('x-real-ip')

    if (userAgent) {
      request.headers.set('User-Agent', userAgent)
    }

    if (forwardedFor) {
      request.headers.set('X-Forwarded-For', forwardedFor)
    } else if (realIp) {
      request.headers.set('X-Forwarded-For', realIp)
    }

    propagation.inject(context.active(), request.headers, {
      set: (carrier, key, value) => {
        if (carrier instanceof Headers) {
          carrier.set(key, value)
        }
      },
    })
  },
]

const _afterResponseHooks: AfterResponseHook[] = [
  async (_request, _options, response) => {
    logger.info(
      `\t[RSP] tid=${_request.headers.get('X-Trace-Id')} [${_request.method}] [${response.status}] ${_request.url} (${Date.now() - Number(_request.headers.get('X-Timestamp'))}ms)`,
    )
  },
]

const _beforeErrorHooks: BeforeErrorHook[] = [
  async (error) => {
    const responseText = await error.response.text()

    const { parsed, success } = safeJsonParse<{
      detail?: string
      message?: string
    }>(responseText)

    const msg = success ? (parsed?.detail ?? parsed?.message ?? responseText) : responseText

    logger.error(
      `\ttid=${error.request.headers.get('X-Trace-Id')} [${error.request.method}] [${error.response?.status}] failed because server answered with: ${yellow(JSON.stringify(msg))}`,
    )

    return error
  },
]

export const api = ky.create({
  prefixUrl: serverUrl,
  timeout: 60000,
  throwHttpErrors: true, // Don't change this, we handle errors in the actions directly
  hooks: {
    beforeRequest: _beforeRequestHooks,
    afterResponse: _afterResponseHooks,
    beforeError: _beforeErrorHooks,
  },
})

export const chat = ky.create({
  prefixUrl: chatUrl,
  timeout: 60000,
  throwHttpErrors: true, // Don't change this, we handle errors in the actions directly
  hooks: {
    beforeRequest: _beforeRequestHooks,
    afterResponse: _afterResponseHooks,
    beforeError: _beforeErrorHooks,
  },
})
