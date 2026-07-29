'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { ArrowLeft, ImagePlus, Pencil, XCircle, RotateCcw } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EventRead } from '@/lib/api/events'
import { cancelEvent, reactivateEvent } from '@/actions/events'
import { uploadAndSetThumbnail } from '@/actions/photos'

interface Props {
  event: EventRead
  canManage: boolean
  onEventUpdate: (event: EventRead) => void
}

export function EventHeader({ event, canManage, onEventUpdate }: Props) {
  const router = useRouter()
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      setUploading(true)
      const formData = new FormData()
      formData.append('file', acceptedFiles[0])
      try {
        await uploadAndSetThumbnail(event.id, formData)
        router.refresh() // ponytail: simple refresh; add react-query revalidation later
      } catch {
        // ponytail: error toast via sonner when added
      } finally {
        setUploading(false)
      }
    },
    [event.id, router],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: !canManage || uploading,
  })

  const statusLabel = {
    SCHEDULED: 'Agendado',
    IN_PROGRESS: 'Em andamento',
    COMPLETED: 'Concluido',
    CANCELLED: 'Cancelado',
  }[event.status]

  const statusVariant =
    event.status === 'CANCELLED'
      ? 'destructive'
      : event.status === 'IN_PROGRESS'
        ? 'default'
        : 'secondary'

  return (
    <div className="flex gap-6">
      {/* Thumbnail */}
      <div className="w-48 shrink-0">
        {event.thumbnail_url ? (
          <div className="relative group rounded-lg overflow-hidden aspect-video">
            <img
              src={`${process.env.NEXT_PUBLIC_MEDIA_URL ?? ''}${event.thumbnail_url}`}
              alt={event.title}
              className="w-full h-full object-cover"
            />
            {canManage && (
              <div
                {...getRootProps()}
                className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer"
              >
                <input {...getInputProps()} />
                <span className="text-white text-xs text-center px-2">
                  Alterar thumbnail
                </span>
              </div>
            )}
          </div>
        ) : canManage ? (
          <div
            {...getRootProps()}
            className={`aspect-video rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="text-center text-muted-foreground">
              <ImagePlus className="size-6 mx-auto mb-1" />
              <span className="text-[10px]">
                {uploading ? 'Enviando...' : 'Adicionar thumbnail'}
              </span>
            </div>
          </div>
        ) : (
          <div className="aspect-video rounded-lg bg-muted flex items-center justify-center">
            <ImagePlus className="size-6 text-muted-foreground/30" />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <button
          onClick={() => router.push('/events')}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="size-4" /> Voltar
        </button>

        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold">{event.title}</h1>
          <Badge style={{ backgroundColor: event.type_color, color: '#fff' }}>
            {event.type.replace(/_/g, ' ')}
          </Badge>
          <Badge variant={statusVariant as 'default' | 'secondary' | 'destructive'}>
            {statusLabel}
          </Badge>
        </div>

        <div className="mt-3 space-y-1 text-sm text-muted-foreground">
          <p>
            {format(new Date(event.start_at), "d 'de' MMMM 'de' yyyy 'as' HH:mm", {
              locale: ptBR,
            })}
            {' ate '}
            {format(new Date(event.end_at), "d 'de' MMMM 'de' yyyy 'as' HH:mm", {
              locale: ptBR,
            })}
          </p>
          {event.participants_count > 0 && (
            <p>
              {event.participants_count} participante
              {event.participants_count > 1 ? 's' : ''}
            </p>
          )}
          {event.location && (
            <p>
              {event.location.name ? `${event.location.name} — ` : ''}
              {event.location.address}
            </p>
          )}
        </div>

        {event.description && (
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            {event.description}
          </p>
        )}

        {canManage && (
          <div className="flex gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push(`/events/${event.id}/edit`)}
            >
              <Pencil className="size-3 mr-1" /> Editar
            </Button>
            {event.status !== 'CANCELLED' ? (
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  if (confirm('Cancelar este evento?')) {
                    await cancelEvent(event.id)
                    router.refresh()
                  }
                }}
              >
                <XCircle className="size-3 mr-1" /> Cancelar
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await reactivateEvent(event.id)
                  router.refresh()
                }}
              >
                <RotateCcw className="size-3 mr-1" /> Reativar
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
