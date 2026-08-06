const FIELD_LABELS: Record<string, string> = {
  avatar_key: 'Avatar',
  banner_key: 'Banner',
  discord_username: 'Discord',
  email: 'E-mail',
  first_name: 'Nome',
  last_name: 'Sobrenome',
  new_password: 'Senha',
  phone_number: 'Telefone',
  username: 'Nome de usuário',
}

const FALLBACK_MESSAGE = 'Erro de validação. Tente novamente.'

function getMessages(value: unknown): string[] {
  if (typeof value === 'string') {
    return value ? [value] : []
  }

  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === 'string' && item.length > 0)
  }

  return []
}

export function formatApiError(payload: unknown): string {
  const directMessages = getMessages(payload)
  if (directMessages.length > 0) {
    return directMessages.join(' ')
  }

  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return FALLBACK_MESSAGE
  }

  const record = payload as Record<string, unknown>
  const directMessage = getMessages(record.detail).concat(getMessages(record.message))
  if (directMessage.length > 0) {
    return directMessage[0]
  }

  const fieldMessages = Object.entries(record).flatMap(([field, value]) => {
    const messages = getMessages(value)
    if (messages.length === 0) {
      return []
    }

    if (field === 'non_field_errors') {
      return [messages.join(' ')]
    }

    return [`${FIELD_LABELS[field] ?? field}: ${messages.join(' ')}`]
  })

  return fieldMessages.length > 0 ? fieldMessages.join(' ') : FALLBACK_MESSAGE
}
