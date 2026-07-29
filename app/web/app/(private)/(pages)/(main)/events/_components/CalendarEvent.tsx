'use client'

import type { EventRead } from '@/lib/api/events'

interface Props {
  event: EventRead
  onClick: () => void
}

export function CalendarEvent({ event, onClick }: Props) {
  return (
    <div
      className="text-[10px] leading-tight px-1 py-0.5 rounded-sm truncate text-white cursor-pointer hover:opacity-80 font-medium"
      style={{ backgroundColor: event.type_color }}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      title={event.title}
    >
      {event.title}
    </div>
  )
}
