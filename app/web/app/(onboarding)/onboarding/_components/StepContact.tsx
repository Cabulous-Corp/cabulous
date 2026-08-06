'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
  onBack: () => void
}

export function StepContact({ onNext, onBack }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

  const handleNext = async () => {
    const valid = await trigger(['email'])
    if (valid) onNext()
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">Como te encontram?</h2>
        <p className="text-sm text-muted-foreground mt-1">Seus contatos.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">E-mail *</label>
          <Input {...register('email')} placeholder="seu@email.com" className="mt-1" error={errors.email?.message} type="email" />
        </div>
        <div>
          <label className="text-sm font-medium">Discord</label>
          <Input {...register('discord_username')} placeholder="usuário#0000" className="mt-1" />
        </div>
        <div>
          <label className="text-sm font-medium">Telefone</label>
          <Input {...register('phone_number')} placeholder="(11) 99999-9999" className="mt-1" />
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={onBack} className="flex-1">Voltar</Button>
        <Button onClick={handleNext} className="flex-1">Continuar</Button>
      </div>
    </div>
  )
}
