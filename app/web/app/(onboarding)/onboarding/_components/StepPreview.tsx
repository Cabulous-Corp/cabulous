'use client'

import { useFormContext } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card } from '@/components/ui/card'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onBack: () => void
  onComplete: () => void
  submitting: boolean
  error: string
}

export function StepPreview({ onBack, onComplete, submitting, error }: Props) {
  const { getValues } = useFormContext<OnboardingFormValues>()
  const values = getValues()
  const initials = `${values.first_name?.[0] ?? ''}${values.last_name?.[0] ?? ''}`.toUpperCase()

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Seu perfil</h2>
        <p className="text-sm text-muted-foreground mt-1">É assim que você vai aparecer.</p>
      </div>

      <Card className="gap-0 overflow-hidden p-0">
        <div data-profile-preview-media className="relative">
          {values.banner_preview && (
            <div data-profile-preview-banner className="relative z-0 h-28 overflow-hidden bg-muted">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={values.banner_preview} alt="" className="size-full object-cover" />
            </div>
          )}
          <div
            data-profile-preview-avatar
            className={`relative z-10 px-6 ${values.banner_preview ? '-mt-10' : 'pt-6'}`}
          >
            <Avatar className="size-16 ring-4 ring-card">
              {values.avatar_preview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={values.avatar_preview} alt="" className="size-full object-cover rounded-full" />
              ) : values.avatar_key ? (
                <AvatarFallback className="text-lg bg-primary/10">
                  <span className="text-primary text-xs">OK</span>
                </AvatarFallback>
              ) : (
                <AvatarFallback className="text-lg">{initials || '?'}</AvatarFallback>
              )}
            </Avatar>
          </div>
          <div className="px-6 pt-3">
            <h3 className="font-semibold text-lg">{values.first_name} {values.last_name}</h3>
            <p className="text-sm text-muted-foreground">@{values.username}</p>
          </div>
        </div>
        <div className="space-y-4 px-6 pb-6 pt-4">
          {values.bio && <p className="text-sm">{values.bio}</p>}
          <div className="text-xs text-muted-foreground space-y-0.5">
            <p>{values.email}</p>
            {values.discord_username && <p>Discord: {values.discord_username}</p>}
            {values.phone_number && <p>Telefone: {values.phone_number}</p>}
          </div>
        </div>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={onComplete} disabled={submitting} className="flex-1">
          {submitting ? 'Salvando...' : 'Concluir!'}
        </Button>
      </div>
    </div>
  )
}
