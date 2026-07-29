'use client'

import { useFormContext } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { OnboardingFormValues } from './OnboardingWizard'

interface Props {
  onNext: () => void
}

export function StepProfile({ onNext }: Props) {
  const { register, formState: { errors }, trigger } = useFormContext<OnboardingFormValues>()

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

        <div>
          <label className="text-sm font-medium">Foto de perfil</label>
          <p className="text-xs text-muted-foreground mt-1">ponytail: avatar upload via signed-url — skip for now, add later</p>
        </div>
      </div>

      <Button onClick={handleNext} className="w-full">Continuar</Button>
    </div>
  )
}
