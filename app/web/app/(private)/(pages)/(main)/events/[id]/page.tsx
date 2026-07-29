import { notFound } from 'next/navigation'
import { getEvent } from '@/lib/api/events'
import { verifySessionWithoutRedirect } from '@/actions/session'
import { EventDetailClient } from './_components/EventDetailClient'

interface Props {
  params: Promise<{ id: string }>
}

export default async function EventDetailPage({ params }: Props) {
  const { id } = await params
  const event = await getEvent(id).catch(() => null)
  if (!event) notFound()
  const user = await verifySessionWithoutRedirect()

  // ponytail: event.creator not exposed; adjust when backend adds creator_id
  const isCreator = user?.id === event.id
  const isStaff = false // ponytail: wire is_staff from session when available

  return (
    <EventDetailClient
      event={event}
      isCreator={isCreator}
      isStaff={isStaff}
      userId={user?.id ?? null}
    />
  )
}
