'use client'

import { useState, useCallback, useEffect, type Dispatch, type SetStateAction } from 'react'
import { useFormContext } from 'react-hook-form'
import { useDropzone } from 'react-dropzone'
import { Camera, Loader2, ImageUp } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { getSignedUploadUrl } from '@/actions/media'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
}

export function StepProfile({ onNext }: Props) {
  const {
    register,
    formState: { errors },
    trigger,
    setValue,
    watch,
    clearErrors,
    setError,
  } = useFormContext<OnboardingFormValues>()
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [bannerUploading, setBannerUploading] = useState(false)
  const [avatarSrc, setAvatarSrc] = useState<string | null>(null)
  const [bannerSrc, setBannerSrc] = useState<string | null>(null)

  const firstName = watch('first_name') ?? ''
  const lastName = watch('last_name') ?? ''
  const initials = `${firstName[0] ?? ''}${lastName[0] ?? ''}`.toUpperCase() || '?'

  useEffect(() => {
    return () => {
      if (avatarSrc) URL.revokeObjectURL(avatarSrc)
    }
  }, [avatarSrc])

  useEffect(() => {
    return () => {
      if (bannerSrc) URL.revokeObjectURL(bannerSrc)
    }
  }, [bannerSrc])

  const uploadFile = useCallback(
    async (
      file: File,
      type: 'avatar' | 'banner',
      setPreview: Dispatch<SetStateAction<string | null>>,
      setLoading: (loading: boolean) => void,
    ) => {
      const blobUrl = URL.createObjectURL(file)
      const previewField = type === 'avatar' ? 'avatar_preview' : 'banner_preview'
      const keyField = type === 'avatar' ? 'avatar_key' : 'banner_key'
      setPreview((previous) => {
        if (previous) URL.revokeObjectURL(previous)
        return blobUrl
      })
      clearErrors(previewField)
      setValue(previewField, blobUrl)
      setLoading(true)
      try {
        const signed = await getSignedUploadUrl(type, file.name, file.type)
        const fd = new FormData()
        Object.entries(signed.fields).forEach(([k, v]) => fd.append(k, v))
        fd.append('file', file)
        const res = await fetch(signed.url, { method: 'POST', body: fd })
        if (!res.ok) throw new Error('Upload failed')
        setValue(keyField, signed.object_key)
      } catch {
        setValue(keyField, undefined)
        setError(previewField, {
          type: 'upload',
          message: 'Nao foi possivel enviar a imagem. Tente novamente.',
        })
      } finally {
        setLoading(false)
      }
    },
    [clearErrors, setError, setValue],
  )

  const avatarDrop = useDropzone({
    onDrop: (files) => { if (files[0]) uploadFile(files[0], 'avatar', setAvatarSrc, setAvatarUploading) },
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: avatarUploading,
  })

  const bannerDrop = useDropzone({
    onDrop: (files) => { if (files[0]) uploadFile(files[0], 'banner', setBannerSrc, setBannerUploading) },
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: bannerUploading,
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
        {/* Banner */}
        <div {...bannerDrop.getRootProps()} className="relative cursor-pointer group">
          <input {...bannerDrop.getInputProps()} />
          <div className="h-28 rounded-lg bg-muted/50 border border-dashed border-border flex items-center justify-center overflow-hidden">
            {bannerSrc ? (
              <img src={bannerSrc} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="flex flex-col items-center gap-1 text-muted-foreground">
                {bannerUploading ? (
                  <Loader2 className="size-5 animate-spin" />
                ) : (
                  <>
                    <ImageUp className="size-5" />
                    <span className="text-xs">Adicionar banner</span>
                  </>
                )}
              </div>
            )}
          </div>
          {errors.banner_preview?.message && (
            <p className="mt-2 text-xs font-medium text-destructive">{errors.banner_preview.message}</p>
          )}
        </div>

        {/* Avatar */}
        <div className="flex justify-center -mt-10 relative z-10">
          <div {...avatarDrop.getRootProps()} className="cursor-pointer group relative">
            <input {...avatarDrop.getInputProps()} />
            <Avatar className="size-24 ring-4 ring-background">
              {avatarSrc ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={avatarSrc} alt="" className="size-full object-cover rounded-full" />
              ) : (
                <AvatarFallback className="text-2xl bg-muted">
                  {avatarUploading ? <Loader2 className="size-6 animate-spin" /> : initials}
                </AvatarFallback>
              )}
            </Avatar>
            {!avatarUploading && (
              <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera className="size-5 text-white" />
              </div>
            )}
          </div>
          {errors.avatar_preview?.message && (
            <p className="mt-2 text-center text-xs font-medium text-destructive">{errors.avatar_preview.message}</p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium">Nome completo *</label>
          <div className="mt-1 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
            <Input {...register('first_name')} placeholder="Nome" error={errors.first_name?.message} />
            <Input {...register('last_name')} placeholder="Sobrenome" error={errors.last_name?.message} />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">Username *</label>
          <Input {...register('username')} placeholder="@seunome" className="mt-1" error={errors.username?.message} />
        </div>
      </div>

      <Button onClick={handleNext} className="w-full">Continuar</Button>
    </div>
  )
}
