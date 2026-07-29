'use client'

import { useMemo } from 'react'
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth } from 'date-fns'
import type { EventRead } from '@/lib/api/events'
import { CalendarDay } from './CalendarDay'

interface Props {
  currentDate: Date
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']

export function MonthView({ currentDate, events, onDayClick, onEventClick }: Props) {
  const days = useMemo(() => {
    const monthStart = startOfMonth(currentDate)
    const monthEnd = endOfMonth(currentDate)
    const calStart = startOfWeek(monthStart, { weekStartsOn: 0 })
    const calEnd = endOfWeek(monthEnd, { weekStartsOn: 0 })
    return eachDayOfInterval({ start: calStart, end: calEnd })
  }, [currentDate])

  const eventsByDay = useMemo(() => {
    const map = new Map<string, EventRead[]>()
    days.forEach((day) => {
      const key = day.toISOString()
      const dayEvents = events.filter((event) => {
        const start = new Date(event.start_at)
        const end = new Date(event.end_at)
        const dayStart = new Date(day.getFullYear(), day.getMonth(), day.getDate())
        const dayEnd = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59)
        return start <= dayEnd && end >= dayStart
      })
      if (dayEvents.length > 0) map.set(key, dayEvents)
    })
    return map
  }, [events, days])

  return (
    <div className="flex flex-col flex-1 border rounded-lg overflow-hidden">
      <div className="grid grid-cols-7 border-b bg-muted/50">
        {WEEKDAYS.map((d) => (
          <div key={d} className="py-2 text-center text-xs font-semibold text-muted-foreground">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 flex-1 auto-rows-fr">
        {days.map((day) => (
          <CalendarDay
            key={day.toISOString()}
            date={day}
            isCurrentMonth={isSameMonth(day, currentDate)}
            events={eventsByDay.get(day.toISOString()) ?? []}
            onDayClick={onDayClick}
            onEventClick={onEventClick}
          />
        ))}
      </div>
    </div>
  )
}
