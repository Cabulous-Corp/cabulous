'use client'

import { useState } from 'react'
import { EventRead } from '@/lib/api/events'
import { EventHeader } from './EventHeader'
import { EventTabs } from './EventTabs'

interface Props {
  event: EventRead
  isCreator: boolean
  isStaff: boolean
  userId: string | null
}

export function EventDetailClient({ event: initialEvent, isCreator, isStaff, userId }: Props) {
  const [event, setEvent] = useState(initialEvent)
  const canManage = isCreator || isStaff

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <EventHeader event={event} canManage={canManage} onEventUpdate={setEvent} />
      <div className="mt-6">
        <EventTabs event={event} canManage={canManage} userId={userId} />
      </div>
    </div>
  )
}
