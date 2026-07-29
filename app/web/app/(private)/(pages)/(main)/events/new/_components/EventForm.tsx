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
import { createEvent } from '@/actions/events'
import type { EventOptions } from '@/lib/api/events'
import { LocationPicker } from './LocationPicker'

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const eventSchema = z.object({
  title: z.string().min(1, 'Titulo e obrigatorio.').max(255),
  description: z.string(),
  type: z.string().min(1, 'Tipo e obrigatorio.'),
  audiences: z.array(z.string()).min(1, 'Selecione ao menos uma audiencia.'),
  start_at: z.string().min(1, 'Data de inicio e obrigatoria.'),
  end_at: z.string().min(1, 'Data de fim e obrigatoria.'),
  location_name: z.string(),
  location_address: z.string(),
  location_latitude: z.number().nullable(),
  location_longitude: z.number().nullable(),
}).refine((data) => new Date(data.end_at) >= new Date(data.start_at), {
  message: 'Fim deve ser posterior ao inicio.',
  path: ['end_at'],
})

type EventFormValues = z.infer<typeof eventSchema>

interface Props {
  options: EventOptions
  prefilledDate: string | null
}

export function EventForm({ options, prefilledDate }: Props) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [audiences, setAudiences] = useState<string[]>([])

  const today = format(new Date(), "yyyy-MM-dd'T'HH:mm")
  const prefilled = prefilledDate ? `${prefilledDate}T20:00` : undefined

  const form = useForm<EventFormValues>({
    defaultValues: {
      title: '',
      description: '',
      type: '',
      audiences: [],
      start_at: prefilled ?? today,
      end_at: prefilled ?? today,
      location_name: '',
      location_address: '',
      location_latitude: null,
      location_longitude: null,
    },
  })

  const handleSubmit = async (values: EventFormValues) => {
    setIsSubmitting(true)
    setSubmitError('')
    try {
      const hasLocation = values.location_address && values.location_latitude && values.location_longitude
      await createEvent({
        title: values.title,
        description: values.description || undefined,
        start_at: new Date(values.start_at).toISOString(),
        end_at: new Date(values.end_at).toISOString(),
        type: values.type,
        audiences: values.audiences,
        location: hasLocation
          ? {
              name: values.location_name || undefined,
              address: values.location_address,
              latitude: values.location_latitude!,
              longitude: values.location_longitude!,
            }
          : null,
      })
    } catch (e: unknown) {
      const err = e as { message?: string }
      setSubmitError(err.message ?? 'Erro ao criar evento.')
      setIsSubmitting(false)
    }
  }

  const toggleAudience = (audience: string) => {
    setAudiences((prev) => {
      const next = prev.includes(audience) ? prev.filter((a) => a !== audience) : [...prev, audience]
      form.setValue('audiences', next)
      return next
    })
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="size-4" /> Voltar
      </button>
      <h1 className="text-2xl font-bold mb-6">Novo Evento</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="title"
            rules={{ required: 'Titulo e obrigatorio.' }}
            render={({ field, fieldState }) => (
              <FormItem>
                <FormLabel>Titulo *</FormLabel>
                <FormControl>
                  <Input {...field} placeholder="Nome do evento" error={fieldState.error?.message} />
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
                  <Textarea {...field} placeholder="Descreva o evento..." rows={3} />
                </FormControl>
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="type"
            rules={{ required: 'Tipo e obrigatorio.' }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tipo *</FormLabel>
                <FormControl>
                  <Combobox
                    options={options.types.map((t) => ({ value: t.value, label: t.label }))}
                    value={field.value}
                    onValueChange={(v) => field.onChange(String(v))}
                    placeholder="Selecione o tipo..."
                    searchPlaceholder="Buscar tipo..."
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div>
            <label className="text-sm font-medium">Audiencias *</label>
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
            {form.formState.errors.audiences && (
              <p className="text-destructive text-sm mt-1">{form.formState.errors.audiences.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="start_at"
              rules={{ required: 'Data de inicio e obrigatoria.' }}
              render={({ field, fieldState }) => (
                <FormItem>
                  <FormLabel>Inicio *</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" error={fieldState.error?.message} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="end_at"
              rules={{ required: 'Data de fim e obrigatoria.' }}
              render={({ field, fieldState }) => (
                <FormItem>
                  <FormLabel>Fim *</FormLabel>
                  <FormControl>
                    <Input {...field} type="datetime-local" error={fieldState.error?.message} />
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
                    <Input {...field} placeholder="Ex: Bar do Ze" />
                  </FormControl>
                </FormItem>
              )}
            />

            <LocationPicker
              onLocationSelect={(lat, lng, address) => {
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
              {isSubmitting ? 'Criando...' : 'Criar Evento'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}
