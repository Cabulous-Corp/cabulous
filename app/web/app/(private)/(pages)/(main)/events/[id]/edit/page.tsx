import { getEvent, getEventOptions } from '@/lib/api/events'
import { EventEditForm } from './_components/EventEditForm'

interface Props {
  params: Promise<{ id: string }>
}

export default async function EditEventPage({ params }: Props) {
  const { id } = await params
  const [event, options] = await Promise.all([getEvent(id), getEventOptions()])
  return <EventEditForm event={event} options={options} />
}
