import { getEvents, getEventOptions } from '@/lib/api/events'
import { CalendarView } from './_components/CalendarView'
import type { EventStatus, EventType, Audience } from '@/lib/api/events'

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}

export default async function EventsPage({ searchParams }: Props) {
  const params = await searchParams
  const options = await getEventOptions()

  const startsFrom = typeof params.starts_from === 'string' ? params.starts_from : undefined
  const startsUntil = typeof params.starts_until === 'string' ? params.starts_until : undefined
  const status = typeof params.status === 'string' ? params.status as EventStatus : undefined
  const type = typeof params.type === 'string' ? params.type as EventType : undefined
  const audience = typeof params.audience === 'string' ? params.audience as Audience : undefined
  const search = typeof params.search === 'string' ? params.search : undefined

  const initialEvents = await getEvents({
    starts_from: startsFrom,
    starts_until: startsUntil,
    status,
    type,
    audience,
    search,
    page_size: 200,
  })

  return <CalendarView initialEvents={initialEvents.results} options={options} />
}
