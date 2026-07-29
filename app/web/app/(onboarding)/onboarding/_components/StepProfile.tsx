'use client'

import { useState, useCallback } from 'react'
import { useFormContext } from 'react-hook-form'
import { useDropzone } from 'react-dropzone'
import { ImagePlus, Loader2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { getSignedUploadUrl } from '@/actions/media'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
}

export function StepProfile({ onNext }: Props) {
  const { register, formState: { errors }, trigger, setValue, watch } = useFormContext<OnboardingFormValues>()
  const [uploading, setUploading] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)

  const firstName = watch('first_name') ?? ''
  const lastName = watch('last_name') ?? ''
  const initials = `${firstName[0] ?? ''}${lastName[0] ?? ''}`.toUpperCase() || '?'

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    const file = acceptedFiles[0]
    setUploading(true)
    try {
      const signed = await getSignedUploadUrl('avatar', file.name, file.type)
      const uploadFormData = new FormData()
      Object.entries(signed.fields).forEach(([key, value]) => {
        uploadFormData.append(key, value)
      })
      uploadFormData.append('file', file)
      const uploadRes = await fetch(signed.url, { method: 'POST', body: uploadFormData })
      if (!uploadRes.ok) throw new Error('Upload failed')
      setValue('avatar_key', signed.object_key)
      setAvatarPreview(URL.createObjectURL(file))
    } catch {
      // ponytail: add toast error
    } finally {
      setUploading(false)
    }
  }, [setValue])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: uploading,
  })

  const handleNext = async () => {
    const valid = await trigger(['first_name', 'last_name', 'username'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Quem e voce?</h2>
        <p className="text-sm text-muted-foreground mt-1">Conte um pouco sobre voce.</p>
      </div>

      <div className="space-y-4">
        <div className="flex justify-center">
          <div {...getRootProps()} className="cursor-pointer">
            <input {...getInputProps()} />
            <Avatar className="size-24 ring-2 ring-offset-2 ring-border hover:ring-primary transition-all">
              {avatarPreview ? (
                <img src={avatarPreview} alt="" className="size-full object-cover rounded-full" />
              ) : (
                <AvatarFallback className="text-2xl bg-muted">
                  {uploading ? <Loader2 className="size-6 animate-spin" /> : initials}
                </AvatarFallback>
              )}
            </Avatar>
            <p className="text-xs text-center text-muted-foreground mt-2">
              {uploading ? 'Enviando...' : 'Clique para adicionar foto'}
            </p>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">Nome completo *</label>
          <div className="flex gap-3 mt-1">
            <Input {...register('first_name')} placeholder="Nome" error={errors.first_name?.message} />
            <Input {...register('last_name')} placeholder="Sobrenome" error={errors.last_name?.message} />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">Username *</label>
          <Input
            {...register('username')}
            placeholder="@seunome"
            className="mt-1"
            error={errors.username?.message}
          />
        </div>
      </div>

      <Button onClick={handleNext} className="w-full">Continuar</Button>
    </div>
  )
}
