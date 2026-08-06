import { describe, expect, it } from 'vitest'
import { formatApiError } from '@/lib/api/errors'

describe('formatApiError', () => {
  it('formats a field validation error with a friendly field label', () => {
    expect(
      formatApiError({ new_password: ['A senha é muito parecida com Nome de usuário'] }),
    ).toBe('Senha: A senha é muito parecida com Nome de usuário')
  })

  it('formats multiple field errors without exposing JSON', () => {
    expect(
      formatApiError({
        avatar_key: ['O avatar não foi encontrado.'],
        phone_number: ['Informe um telefone válido.'],
      }),
    ).toBe('Avatar: O avatar não foi encontrado. Telefone: Informe um telefone válido.')
  })

  it('prefers the backend detail message', () => {
    expect(formatApiError({ detail: 'Onboarding has already been completed.' })).toBe(
      'Onboarding has already been completed.',
    )
  })

  it('keeps a plain response body readable', () => {
    expect(formatApiError('Service unavailable')).toBe('Service unavailable')
  })

  it('returns a safe fallback for unknown payloads', () => {
    expect(formatApiError({ unexpected: { nested: true } })).toBe('Erro de validação. Tente novamente.')
  })
})
