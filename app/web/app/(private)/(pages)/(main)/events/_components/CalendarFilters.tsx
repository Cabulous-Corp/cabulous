'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'
import { Search } from 'lucide-react'
import type { EventOptions } from '@/lib/api/events'

interface Props {
  options: EventOptions
}

export function CalendarFilters({ options }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    router.push(`/events?${params.toString()}`)
  }

  const debouncedSearch = useDebouncedCallback((value: string) => updateParam('search', value), 300)

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="relative flex-1 min-w-[200px] max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar eventos..."
          defaultValue={searchParams.get('search') ?? ''}
          onChange={(e) => debouncedSearch(e.target.value)}
          className="w-full h-10 pl-9 pr-3 rounded-md bg-background border text-sm"
        />
      </div>
      <select
        value={searchParams.get('type') ?? ''}
        onChange={(e) => updateParam('type', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todos os tipos</option>
        {options.types.map((t) => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>
      <select
        value={searchParams.get('status') ?? ''}
        onChange={(e) => updateParam('status', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todos os status</option>
        {options.statuses.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
      <select
        value={searchParams.get('audience') ?? ''}
        onChange={(e) => updateParam('audience', e.target.value)}
        className="h-10 px-3 rounded-md bg-background border text-sm"
      >
        <option value="">Todas as audiencias</option>
        {options.audiences.map((a) => (
          <option key={a.value} value={a.value}>{a.label}</option>
        ))}
      </select>
    </div>
  )
}
