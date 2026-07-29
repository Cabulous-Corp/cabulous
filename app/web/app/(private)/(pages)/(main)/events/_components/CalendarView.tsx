'use client'

import { useState, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { addMonths, subMonths, addWeeks, subWeeks, startOfWeek, format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import type { EventRead, EventOptions } from '@/lib/api/events'
import { CalendarNavigation } from './CalendarNavigation'
import { CalendarFilters } from './CalendarFilters'
import { MonthView } from './MonthView'
import { WeekView } from './WeekView'
import { AgendaView } from './AgendaView'

type CalendarViewType = 'month' | 'week' | 'agenda'

interface Props {
  initialEvents: EventRead[]
  options: EventOptions
}

export function CalendarView({ initialEvents, options }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [events] = useState(initialEvents)
  const [viewType, setViewType] = useState<CalendarViewType>('month')
  const [currentDate, setCurrentDate] = useState(new Date())

  const navigate = {
    prev: () => setCurrentDate((d) => (viewType === 'week' ? subWeeks(d, 1) : subMonths(d, 1))),
    next: () => setCurrentDate((d) => (viewType === 'week' ? addWeeks(d, 1) : addMonths(d, 1))),
    today: () => setCurrentDate(new Date()),
  }

  const title = useMemo(() => {
    if (viewType === 'month') return format(currentDate, "MMMM 'de' yyyy", { locale: ptBR })
    if (viewType === 'week') {
      const start = startOfWeek(currentDate, { weekStartsOn: 0 })
      return `Semana de ${format(start, "d 'de' MMM", { locale: ptBR })}`
    }
    return format(currentDate, "MMMM yyyy", { locale: ptBR })
  }, [viewType, currentDate])

  return (
    <div className="flex flex-col h-full gap-4 p-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Eventos</h1>
        <a
          href="/events/new"
          className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground h-10 px-4 text-sm font-medium"
        >
          Novo Evento
        </a>
      </div>

      <CalendarFilters options={options} />

      <CalendarNavigation
        title={title}
        viewType={viewType}
        onViewChange={setViewType}
        onPrev={navigate.prev}
        onNext={navigate.next}
        onToday={navigate.today}
      />

      {viewType === 'month' && (
        <MonthView
          currentDate={currentDate}
          events={events}
          onDayClick={(date) => router.push(`/events/new?date=${format(date, 'yyyy-MM-dd')}`)}
          onEventClick={(id) => router.push(`/events/${id}`)}
        />
      )}
      {viewType === 'week' && (
        <WeekView
          currentDate={currentDate}
          events={events}
          onDayClick={(date) => router.push(`/events/new?date=${format(date, 'yyyy-MM-dd')}`)}
          onEventClick={(id) => router.push(`/events/${id}`)}
        />
      )}
      {viewType === 'agenda' && (
        <AgendaView events={events} onEventClick={(id) => router.push(`/events/${id}`)} />
      )}
    </div>
  )
}
