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
        <p className="text-sm text-muted-foreground mt-1">Assim que voce vai aparecer.</p>
      </div>

      <Card className="p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Avatar className="size-16">
            <AvatarFallback className="text-lg">{initials || '?'}</AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold text-lg">{values.first_name} {values.last_name}</h3>
            <p className="text-sm text-muted-foreground">@{values.username}</p>
          </div>
        </div>
        {values.bio && <p className="text-sm">{values.bio}</p>}
        <div className="text-xs text-muted-foreground space-y-0.5">
          <p>{values.email}</p>
          {values.discord_username && <p>Discord: {values.discord_username}</p>}
          {values.phone_number && <p>Tel: {values.phone_number}</p>}
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
