'use client'

import { isToday } from 'date-fns'
import type { EventRead } from '@/lib/api/events'
import { CalendarEvent } from './CalendarEvent'

interface Props {
  date: Date
  isCurrentMonth: boolean
  events: EventRead[]
  onDayClick: (date: Date) => void
  onEventClick: (eventId: string) => void
}

export function CalendarDay({ date, isCurrentMonth, events, onDayClick, onEventClick }: Props) {
  return (
    <div
      className={`border-b border-r p-1 min-h-[80px] cursor-pointer hover:bg-accent/50 transition-colors ${
        !isCurrentMonth ? 'opacity-40' : ''
      }`}
      onClick={() => onDayClick(date)}
    >
      <div
        className={`text-xs mb-1 w-6 h-6 flex items-center justify-center rounded-full ${
          isToday(date) ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
        }`}
      >
        {date.getDate()}
      </div>
      <div className="space-y-0.5">
        {events.slice(0, 3).map((event) => (
          <CalendarEvent key={event.id} event={event} onClick={() => onEventClick(event.id)} />
        ))}
        {events.length > 3 && (
          <div className="text-[10px] text-muted-foreground px-1">+{events.length - 3} mais</div>
        )}
      </div>
    </div>
  )
}
