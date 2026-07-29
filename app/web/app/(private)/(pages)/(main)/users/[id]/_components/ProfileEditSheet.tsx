'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { updateUserProfile } from '@/actions/users'
import type { UserProfile } from '@/lib/api/users'

const editProfileSchema = z.object({
  first_name: z.string().min(1, 'Nome e obrigatorio.'),
  last_name: z.string().min(1, 'Sobrenome e obrigatorio.'),
  bio: z.string().optional(),
  discord_username: z.string().optional(),
  phone_number: z.string().optional(),
})

type EditProfileValues = z.infer<typeof editProfileSchema>

interface Props {
  profile: UserProfile
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ProfileEditSheet({ profile, open, onOpenChange }: Props) {
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EditProfileValues>({
    resolver: zodResolver(editProfileSchema),
    defaultValues: {
      first_name: profile.first_name,
      last_name: profile.last_name,
      bio: profile.bio || '',
      discord_username: profile.discord_username || '',
      phone_number: profile.phone_number || '',
    },
  })

  const onSubmit = async (data: EditProfileValues) => {
    setSubmitting(true)
    setError('')
    try {
      await updateUserProfile(profile.id, data)
      onOpenChange(false)
      router.refresh()
    } catch (e: unknown) {
      const err = e as { message?: string }
      setError(err.message ?? 'Erro ao salvar perfil.')
      setSubmitting(false)
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Editar perfil</SheetTitle>
          <SheetDescription>Atualize suas informacoes.</SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 mt-4">
          <div className="flex gap-3">
            <Input
              {...register('first_name')}
              placeholder="Nome"
              error={errors.first_name?.message}
            />
            <Input
              {...register('last_name')}
              placeholder="Sobrenome"
              error={errors.last_name?.message}
            />
          </div>

          <Textarea
            {...register('bio')}
            placeholder="Bio"
            rows={4}
            maxLength={500}
            error={errors.bio?.message}
          />

          <Input
            {...register('discord_username')}
            placeholder="Discord (usuario#0000)"
            error={errors.discord_username?.message}
          />

          <Input
            {...register('phone_number')}
            placeholder="Telefone"
            error={errors.phone_number?.message}
          />

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" disabled={submitting} className="w-full">
            {submitting ? 'Salvando...' : 'Salvar'}
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  )
}
