'use client'

import Link from 'next/link'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import type { PaginatedResponse, EventRead } from '@/lib/api/events'

interface Props {
  userId: string
  createdEvents: PaginatedResponse<EventRead> | null
  participatingEvents: PaginatedResponse<EventRead> | null
}

function EventMiniCard({ event }: { event: EventRead }) {
  return (
    <Link href={`/events/${event.id}`}>
      <Card className="p-3 hover:bg-muted/50 transition-colors cursor-pointer gap-2">
        <div className="flex items-center gap-2">
          <Badge style={{ backgroundColor: event.type_color, color: '#fff' }}>
            {event.type.replace(/_/g, ' ')}
          </Badge>
          <span className="text-sm font-medium truncate">{event.title}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          {format(new Date(event.start_at), "d 'de' MMMM 'de' yyyy", { locale: ptBR })}
        </p>
      </Card>
    </Link>
  )
}

export function ProfileTabs({ createdEvents, participatingEvents }: Props) {
  return (
    <Tabs defaultValue="created" className="px-4">
      <TabsList>
        <TabsTrigger value="created">Eventos</TabsTrigger>
        <TabsTrigger value="participating">Participando</TabsTrigger>
      </TabsList>

      <TabsContent value="created" className="space-y-2 mt-2">
        {createdEvents?.results.length ? (
          createdEvents.results.map((event) => (
            <EventMiniCard key={event.id} event={event} />
          ))
        ) : (
          <p className="text-sm text-muted-foreground py-4 text-center">
            Nenhum evento criado.
          </p>
        )}
      </TabsContent>

      <TabsContent value="participating" className="space-y-2 mt-2">
        {participatingEvents?.results.length ? (
          participatingEvents.results.map((event) => (
            <EventMiniCard key={event.id} event={event} />
          ))
        ) : (
          <p className="text-sm text-muted-foreground py-4 text-center">
            Nao participa de nenhum evento.
          </p>
        )}
      </TabsContent>
    </Tabs>
  )
}
