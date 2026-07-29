'use client'

import { useMemo } from 'react'
import { startOfWeek, addDays, format, isSameDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import type { EventRead } from '@/lib/api/events'

interface Props {
  currentDate: Date
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)

export function WeekView({ currentDate, events, onDayClick, onEventClick }: Props) {
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 0 })
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  const eventsByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    days.forEach((day) => {
      map.set(day.toISOString(), events.filter((e) => isSameDay(new Date(e.start_at), day)))
    })
    return map
  }, [events, days])

  return (
    <div className="flex flex-col flex-1 overflow-auto border rounded-lg">
      <div className="grid grid-cols-[60px_repeat(7,1fr)] sticky top-0 bg-background z-10 border-b">
        <div className="py-2" />
        {days.map((day) => (
          <div key={day.toISOString()} className="py-2 text-center text-xs font-semibold">
            <div className="text-muted-foreground">{format(day, 'EEE', { locale: ptBR })}</div>
            <div className="text-lg">{format(day, 'd')}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-[60px_repeat(7,1fr)]">
        {HOURS.map((hour) => (
          <div key={`h-${hour}`} className="contents">
            <div className="h-12 border-r border-b pr-2 pt-0 text-right text-[10px] text-muted-foreground">
              {String(hour).padStart(2, '0')}:00
            </div>
            {days.map((day) => {
              const dayEvents = (eventsByDay.get(day.toISOString()) ?? []).filter((e) => {
                return new Date(e.start_at).getHours() === hour
              })
              return (
                <div
                  key={`${day.toISOString()}-${hour}`}
                  className="h-12 border-r border-b cursor-pointer hover:bg-accent/30"
                  onClick={() => {
                    const d = new Date(day)
                    d.setHours(hour, 0, 0, 0)
                    onDayClick(d)
                  }}
                >
                  {dayEvents.map((event) => (
                    <div
                      key={event.id}
                      className="text-[10px] px-1 py-0.5 rounded-sm text-white mx-0.5 cursor-pointer hover:opacity-80 truncate"
                      style={{ backgroundColor: event.type_color }}
                      onClick={(e) => { e.stopPropagation(); onEventClick(event.id) }}
                      title={event.title}
                    >
                      {event.title}
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
