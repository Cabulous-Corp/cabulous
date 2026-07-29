'use client'

import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { z } from 'zod'
import { format } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Combobox } from '@/components/ui/combobox'
import { updateEvent } from '@/actions/events'
import type { EventRead, EventOptions } from '@/lib/api/events'
import { LocationPicker } from '../../../new/_components/LocationPicker'

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const _editSchema = z
  .object({
    title: z.string().max(255),
    description: z.string(),
    type: z.string(),
    audiences: z.array(z.string()),
    start_at: z.string(),
    end_at: z.string(),
    location_name: z.string(),
    location_address: z.string(),
    location_latitude: z.number().nullable(),
    location_longitude: z.number().nullable(),
  })
  .partial()
  .refine(
    (data) => {
      if (data.start_at && data.end_at && new Date(data.end_at) < new Date(data.start_at)) {
        return false
      }
      return true
    },
    { message: 'Fim deve ser posterior ao inicio.', path: ['end_at'] },
  )

type EditFormValues = z.infer<typeof _editSchema>

interface Props {
  event: EventRead
  options: EventOptions
}

export function EventEditForm({ event, options }: Props) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [audiences, setAudiences] = useState<string[]>(event.audiences ?? [])

  const form = useForm<EditFormValues>({
    defaultValues: {
      title: event.title,
      description: event.description ?? '',
      type: event.type,
      audiences: event.audiences,
      start_at: format(new Date(event.start_at), "yyyy-MM-dd'T'HH:mm"),
      end_at: format(new Date(event.end_at), "yyyy-MM-dd'T'HH:mm"),
      location_name: event.location?.name ?? '',
      location_address: event.location?.address ?? '',
      location_latitude: event.location?.latitude ?? null,
      location_longitude: event.location?.longitude ?? null,
    },
  })

  const handleSubmit = async (values: EditFormValues) => {
    setIsSubmitting(true)
    setSubmitError('')
    try {
      const payload: Record<string, unknown> = {}
      if (values.title && values.title !== event.title) payload.title = values.title
      if (values.description !== undefined && values.description !== (event.description ?? ''))
        payload.description = values.description
      if (values.type && values.type !== event.type) payload.type = values.type
      if (values.audiences && values.audiences.length > 0) payload.audiences = values.audiences
      if (values.start_at) payload.start_at = new Date(values.start_at).toISOString()
      if (values.end_at) payload.end_at = new Date(values.end_at).toISOString()

      const hasLocation = values.location_address || values.location_latitude || values.location_longitude
      if (hasLocation) {
        payload.location = {
          name: values.location_name || undefined,
          address: values.location_address ?? '',
          latitude: values.location_latitude ?? 0,
          longitude: values.location_longitude ?? 0,
        }
      }

      await updateEvent(event.id, payload)
      router.push(`/events/${event.id}`)
    } catch (e: unknown) {
      const err = e as { message?: string }
      setSubmitError(err.message ?? 'Erro ao atualizar evento.')
      setIsSubmitting(false)
    }
  }

  const toggleAudience = (audience: string) => {
    setAudiences((prev) => {
      const next = prev.includes(audience)
        ? prev.filter((a) => a !== audience)
        : [...prev, audience]
      form.setValue('audiences', next)
      return next
    })
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="size-4" /> Voltar
      </button>
      <h1 className="text-2xl font-bold mb-6">Editar Evento</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Titulo</FormLabel>
                <FormControl>
                  <Input {...field} value={field.value ?? ''} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Descricao</FormLabel>
                <FormControl>
                  <Textarea {...field} value={field.value ?? ''} rows={3} />
                </FormControl>
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tipo</FormLabel>
                <FormControl>
                  <Combobox
                    options={options.types.map((t) => ({ value: t.value, label: t.label }))}
                    value={field.value ?? ''}
                    onValueChange={(v) => field.onChange(String(v))}
                    placeholder="Selecione o tipo..."
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div>
            <label className="text-sm font-medium">Audiencias</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {options.audiences.map((a) => (
                <button
                  key={a.value}
                  type="button"
                  onClick={() => toggleAudience(a.value)}
                  className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                    audiences.includes(a.value)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-border hover:bg-accent'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="start_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Inicio</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" value={field.value ?? ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="end_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fim</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" value={field.value ?? ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Local (opcional)</h3>

            <FormField
              control={form.control}
              name="location_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome do local</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ''} />
                  </FormControl>
                </FormItem>
              )}
            />

            <LocationPicker
              onLocationSelect={(lat: number, lng: number, address: string) => {
                form.setValue('location_latitude', lat)
                form.setValue('location_longitude', lng)
                form.setValue('location_address', address)
              }}
            />
          </div>

          {submitError && <p className="text-sm text-destructive">{submitError}</p>}

          <div className="flex gap-3 justify-end pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando...' : 'Salvar Alteracoes'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}
