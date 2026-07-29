'use client'

import { useState, useEffect } from 'react'
import { EventRead } from '@/lib/api/events'
import { getEventParticipants, getEventPhotos, getEventHighlights } from '@/lib/api/events'
import { ParticipantsList } from './ParticipantsList'
import { PhotosGrid } from './PhotosGrid'
import { HighlightsList } from './HighlightsList'

interface Props {
  event: EventRead
  canManage: boolean
  userId: string | null
}

type Tab = 'participants' | 'photos' | 'highlights'

export function EventTabs({ event, canManage, userId }: Props) {
  const [tab, setTab] = useState<Tab>('participants')
  const tabs: { key: Tab; label: string }[] = [
    { key: 'participants', label: 'Participantes' },
    { key: 'photos', label: 'Fotos' },
    { key: 'highlights', label: 'Highlights' },
  ]

  return (
    <div>
      <div className="flex border-b">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="pt-4">
        {tab === 'participants' && (
          <ParticipantsSection eventId={event.id} canManage={canManage} userId={userId} />
        )}
        {tab === 'photos' && (
          <PhotosSection eventId={event.id} canManage={canManage} />
        )}
        {tab === 'highlights' && (
          <HighlightsSection eventId={event.id} canManage={canManage} userId={userId} />
        )}
      </div>
    </div>
  )
}

function ParticipantsSection({
  eventId,
  canManage,
  userId,
}: {
  eventId: string
  canManage: boolean
  userId: string | null
}) {
  const [data, setData] = useState<
    Awaited<ReturnType<typeof getEventParticipants>> | null
  >(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventParticipants(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  return (
    <ParticipantsList
      eventId={eventId}
      data={data}
      loading={loading}
      canManage={canManage}
      userId={userId}
      onRefresh={load}
    />
  )
}

function PhotosSection({
  eventId,
  canManage,
}: {
  eventId: string
  canManage: boolean
}) {
  const [data, setData] = useState<
    Awaited<ReturnType<typeof getEventPhotos>> | null
  >(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventPhotos(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  return (
    <PhotosGrid
      eventId={eventId}
      data={data}
      loading={loading}
      canManage={canManage}
      onRefresh={load}
    />
  )
}

function HighlightsSection({
  eventId,
  canManage,
  userId,
}: {
  eventId: string
  canManage: boolean
  userId: string | null
}) {
  const [data, setData] = useState<
    Awaited<ReturnType<typeof getEventHighlights>> | null
  >(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const result = await getEventHighlights(eventId)
    setData(result)
    setLoading(false)
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  return (
    <HighlightsList
      eventId={eventId}
      data={data}
      loading={loading}
      canManage={canManage}
      userId={userId}
      onRefresh={load}
    />
  )
}
