'use client'

import { useState } from 'react'
import { UserPlus, UserX } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Combobox } from '@/components/ui/combobox'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, ParticipantRead } from '@/lib/api/events'
import { addParticipants, removeParticipant } from '@/actions/participants'

interface Props {
  eventId: string
  data: PaginatedResponse<ParticipantRead> | null
  loading: boolean
  canManage: boolean
  userId: string | null
  onRefresh: () => void
}

export function ParticipantsList({ eventId, data, loading, canManage, userId, onRefresh }: Props) {
  const [selectedUserId, setSelectedUserId] = useState<string>('')

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
        ))}
      </div>
    )
  }

  const participants = data?.results ?? []

  return (
    <div>
      {canManage && (
        <div className="flex gap-3 mb-4">
          <Combobox
            options={[]}
            value={selectedUserId}
            onValueChange={(v) => setSelectedUserId(String(v))}
            placeholder="Buscar usuario..."
            // ponytail: backend needs user search endpoint; combobox disabled for now
          />
          <Button
            size="sm"
            onClick={async () => {
              if (!selectedUserId) return
              await addParticipants(eventId, [selectedUserId])
              setSelectedUserId('')
              onRefresh()
            }}
            disabled
          >
            <UserPlus className="size-3 mr-1" /> Adicionar
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {participants.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-3 py-2 border-b last:border-b-0"
          >
            <Avatar className="size-8">
              <AvatarFallback>
                {(p.username ?? '?')[0].toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <a href={`/users/${p.user}`} className="flex-1 text-sm hover:underline">
              {p.username ?? 'Usuario'}
            </a>
            {canManage && p.user !== userId && (
              <Button
                variant="ghost"
                size="icon"
                onClick={async () => {
                  await removeParticipant(eventId, p.user)
                  onRefresh()
                }}
              >
                <UserX className="size-4 text-muted-foreground" />
              </Button>
            )}
          </div>
        ))}
      </div>

      {participants.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Nenhum participante ainda.
        </p>
      )}
    </div>
  )
}
