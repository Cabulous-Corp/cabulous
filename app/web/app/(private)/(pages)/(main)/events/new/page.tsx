import { getEventOptions } from '@/lib/api/events'
import { EventForm } from './_components/EventForm'

interface Props {
  searchParams: Promise<{ date?: string }>
}

export default async function NewEventPage({ searchParams }: Props) {
  const params = await searchParams
  const options = await getEventOptions()
  return <EventForm options={options} prefilledDate={params.date ?? null} />
}
