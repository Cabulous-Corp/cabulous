import { parseISO, format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

export function formatDateWithoutTime(d: string | undefined | null = '', formatStr: string = 'dd/MM/yyyy') {
  if (!d) return ''
  if (d === '') return ''

  // This ensures we create a iso date at the user timezone
  const date = parseISO(d)

  return format(date, formatStr, { locale: ptBR })
}

export function formatDateWithTime(d: string | undefined | null = '', formatStr: string = 'dd/MM/yyyy') {
  if (!d) return ''
  if (d === '') return ''

  // This ensures we create a iso date at the user timezone
  const date = parseISO(d)

  return format(date, formatStr, { locale: ptBR })
}

export function formatPeriod(startDate?: string | Date | null, endDate?: string | Date | null) {
  if (!startDate || !endDate) return '—'

  const start = format(new Date(startDate), 'd MMM', { locale: ptBR })
  const end = format(new Date(endDate), 'd MMM yyyy', { locale: ptBR })

  return `${start} – ${end}`
}
