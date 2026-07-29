'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepPassword({ onNext, onBack }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

  const handleNext = async () => {
    const valid = await trigger(['new_password'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Sua senha</h2>
        <p className="text-sm text-muted-foreground mt-1">Crie uma senha segura para sua conta.</p>
      </div>

      <Input
        {...register('new_password')}
        type="password"
        placeholder="Minimo 8 caracteres"
        error={errors.new_password?.message}
      />

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={handleNext} className="flex-1">Continuar</Button>
      </div>
    </div>
  )
}
