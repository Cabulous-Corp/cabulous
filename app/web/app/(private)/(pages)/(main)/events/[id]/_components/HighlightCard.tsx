'use client'

import { HighlightRead } from '@/lib/api/events'

interface Props {
  highlight: HighlightRead
  canManage: boolean
  userId: string | null
}

export function HighlightCard({ highlight, canManage, userId }: Props) {
  const isAuthor = userId === highlight.author_id
  const mediaUrl = process.env.NEXT_PUBLIC_MEDIA_URL ?? ''

  return (
    <div className="border rounded-lg p-4">
      <p className="text-sm">{highlight.text}</p>
      {highlight.photos.length > 0 && (
        <div className="flex gap-2 mt-3">
          {highlight.photos.map((photo) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={photo.id}
              src={`${mediaUrl}${photo.object_key}`}
              alt=""
              className="w-16 h-16 object-cover rounded-md"
            />
          ))}
        </div>
      )}
      <div className="mt-2 text-[10px] text-muted-foreground">
        {new Date(highlight.created_at).toLocaleDateString('pt-BR')}
        {(canManage || isAuthor) && (
          <span className="ml-2 text-primary cursor-pointer hover:underline">
            Editar
          </span>
        )}
      </div>
    </div>
  )
}
