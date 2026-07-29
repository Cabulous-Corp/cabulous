'use client'

import { useMemo } from 'react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { CalendarDays, Clock } from 'lucide-react'
import type { EventRead } from '@/lib/api/events'

interface Props {
  events: EventRead[]
  onEventClick: (eventId: string) => void
}

export function AgendaView({ events, onEventClick }: Props) {
  const groupedByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    events.forEach((event) => {
      const dayKey = format(new Date(event.start_at), 'yyyy-MM-dd')
      if (!map.has(dayKey)) map.set(dayKey, [])
      map.get(dayKey)!.push(event)
    })
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [events])

  if (groupedByDay.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <CalendarDays className="size-12 mb-3 opacity-30" />
        <p className="text-sm">Nenhum evento neste periodo.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 overflow-auto border rounded-lg">
      {groupedByDay.map(([dayKey, dayEvents]) => {
        const date = new Date(dayKey + 'T00:00:00')
        return (
          <div key={dayKey} className="border-b last:border-b-0">
            <div className="sticky top-0 bg-background z-10 py-3 px-4 border-b">
              <h3 className="text-sm font-semibold capitalize">
                {format(date, "EEEE, d 'de' MMMM", { locale: ptBR })}
              </h3>
            </div>
            <div className="divide-y">
              {dayEvents.map((event) => (
                <div
                  key={event.id}
                  className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-accent/50 transition-colors"
                  onClick={() => onEventClick(event.id)}
                >
                  <div className="w-2 h-10 rounded-full shrink-0" style={{ backgroundColor: event.type_color }} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{event.title}</div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="size-3" />
                        {format(new Date(event.start_at), 'HH:mm')} - {format(new Date(event.end_at), 'HH:mm')}
                      </span>
                      {event.location && <span>{event.location.name || event.location.address}</span>}
                    </div>
                  </div>
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full text-white shrink-0"
                    style={{ backgroundColor: event.type_color }}
                  >
                    {event.type.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
