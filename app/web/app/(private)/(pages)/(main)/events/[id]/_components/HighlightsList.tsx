'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { PaginatedResponse, HighlightRead } from '@/lib/api/events'
import { createHighlight } from '@/actions/highlights'
import { HighlightCard } from './HighlightCard'

interface Props {
  eventId: string
  data: PaginatedResponse<HighlightRead> | null
  loading: boolean
  canManage: boolean
  userId: string | null
  onRefresh: () => void
}

export function HighlightsList({
  eventId,
  data,
  loading,
  canManage,
  userId,
  onRefresh,
}: Props) {
  const [showForm, setShowForm] = useState(false)
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const highlights = data?.results ?? []

  const handleCreate = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    await createHighlight(eventId, { text: text.trim(), photo_ids: [] })
    setText('')
    setShowForm(false)
    setSubmitting(false)
    onRefresh()
  }

  return (
    <div>
      {(userId || canManage) && (
        <div className="mb-4">
          {!showForm ? (
            <Button variant="outline" size="sm" onClick={() => setShowForm(true)}>
              <Plus className="size-3 mr-1" /> Adicionar highlight
            </Button>
          ) : (
            <div className="space-y-3 p-4 border rounded-lg">
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Escreva um destaque..."
                rows={3}
                maxLength={500}
              />
              <div className="flex gap-2 justify-end">
                <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleCreate}
                  disabled={submitting || !text.trim()}
                >
                  {submitting ? 'Salvando...' : 'Salvar'}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      )}

      <div className="space-y-4">
        {highlights.map((h) => (
          <HighlightCard
            key={h.id}
            highlight={h}
            canManage={canManage}
            userId={userId}
          />
        ))}
      </div>

      {!loading && highlights.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Nenhum highlight ainda.
        </p>
      )}
    </div>
  )
}
