export function capitalize(s: string) {
  if (!s) return ''

  return s.charAt(0).toLocaleUpperCase() + s.slice(1)
}

export function getFirstNameSafely(s?: string | null) {
  if (!s) return ''

  return capitalize(s.split(' ')[0])
}
