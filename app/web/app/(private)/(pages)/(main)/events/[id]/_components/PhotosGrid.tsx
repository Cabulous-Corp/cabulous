'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Star, X, Upload } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, EventPhotoRead } from '@/lib/api/events'
import { uploadAndLinkPhoto, unlinkPhoto, setThumbnail } from '@/actions/photos'

interface Props {
  eventId: string
  data: PaginatedResponse<EventPhotoRead> | null
  loading: boolean
  canManage: boolean
  onRefresh: () => void
}

export function PhotosGrid({ eventId, data, loading, canManage, onRefresh }: Props) {
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setUploading(true)
      for (const file of acceptedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        try {
          await uploadAndLinkPhoto(eventId, formData)
        } catch {
          // ponytail: add toast
        }
      }
      setUploading(false)
      onRefresh()
    },
    [eventId, onRefresh],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    disabled: uploading,
  })

  const photos = data?.results ?? []
  const mediaUrl = process.env.NEXT_PUBLIC_MEDIA_URL ?? ''

  return (
    <div>
      <div className="grid grid-cols-3 md:grid-cols-4 gap-3 mb-4">
        {/* Upload zone */}
        <div
          {...getRootProps()}
          className={`aspect-square rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50'
          } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="text-center text-muted-foreground">
            <Upload className="size-5 mx-auto mb-1" />
            <span className="text-[10px]">
              {uploading ? 'Enviando...' : 'Upload'}
            </span>
          </div>
        </div>

        {loading &&
          Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square rounded-lg" />
          ))}

        {photos.map((photo) => (
          <div
            key={photo.id}
            className="relative group aspect-square rounded-lg overflow-hidden"
          >
            <img
              src={`${mediaUrl}${photo.object_key}`}
              alt=""
              className="w-full h-full object-cover"
            />
            {/* Thumbnail badge */}
            {photo.is_thumbnail && (
              <div className="absolute top-2 left-2 bg-yellow-500 rounded-full p-0.5">
                <Star className="size-3 text-white fill-white" />
              </div>
            )}
            {/* Hover actions */}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
              {canManage && !photo.is_thumbnail && (
                <button
                  className="p-1.5 bg-white/90 rounded-full hover:bg-white"
                  onClick={async () => {
                    await setThumbnail(eventId, photo.id)
                    onRefresh()
                  }}
                  title="Definir como thumbnail"
                >
                  <Star className="size-3.5" />
                </button>
              )}
              {canManage && (
                <button
                  className="p-1.5 bg-white/90 rounded-full hover:bg-white text-destructive"
                  onClick={async () => {
                    await unlinkPhoto(eventId, photo.id)
                    onRefresh()
                  }}
                  title="Desvincular"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {!loading && photos.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Nenhuma foto ainda.
        </p>
      )}
    </div>
  )
}
