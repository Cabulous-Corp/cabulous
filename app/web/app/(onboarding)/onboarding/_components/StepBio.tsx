'use client'

import { useFormContext } from 'react-hook-form'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepBio({ onNext, onBack }: Props) {
  const { register } = useFormContext<OnboardingFormValues>()

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Conte sobre voce</h2>
        <p className="text-sm text-muted-foreground mt-1">Uma breve descricao para seu perfil.</p>
      </div>

      <Textarea
        {...register('bio')}
        placeholder="Escreva algo sobre voce..."
        rows={4}
        maxLength={500}
      />

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={onNext} className="flex-1">Continuar</Button>
      </div>
    </div>
  )
}
