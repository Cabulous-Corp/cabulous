'use client'

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

type CalendarViewType = 'month' | 'week' | 'agenda'

interface Props {
  title: string
  viewType: CalendarViewType
  onViewChange: (type: CalendarViewType) => void
  onPrev: () => void
  onNext: () => void
  onToday: () => void
}

export function CalendarNavigation({ title, viewType, onViewChange, onPrev, onNext, onToday }: Props) {
  const views: { label: string; value: CalendarViewType }[] = [
    { label: 'Mes', value: 'month' },
    { label: 'Semana', value: 'week' },
    { label: 'Agenda', value: 'agenda' },
  ]

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" onClick={onPrev}>
          <ChevronLeft className="size-4" />
        </Button>
        <h2 className="text-lg font-semibold min-w-[180px] text-center capitalize">{title}</h2>
        <Button variant="outline" size="icon" onClick={onNext}>
          <ChevronRight className="size-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onToday}>
          Hoje
        </Button>
      </div>
      <div className="flex rounded-lg bg-muted p-1">
        {views.map((v) => (
          <button
            key={v.value}
            onClick={() => onViewChange(v.value)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              viewType === v.value ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
    </div>
  )
}
