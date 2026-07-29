'use client'

import { useState } from 'react'
import { useForm, FormProvider } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { OnboardingProgress } from './OnboardingProgress'
import { StepProfile } from './StepProfile'
import { StepBio } from './StepBio'
import { StepContact } from './StepContact'
import { StepPassword } from './StepPassword'
import { StepPreview } from './StepPreview'
import { completeOnboarding } from '@/actions/onboarding'

const onboardingSchema = z.object({
  first_name: z.string().min(1, 'Nome e obrigatorio.'),
  last_name: z.string().min(1, 'Sobrenome e obrigatorio.'),
  username: z.string().min(3, 'Username deve ter pelo menos 3 caracteres.'),
  avatar_key: z.string().optional(),
  banner_key: z.string().optional(),
  bio: z.string().optional(),
  email: z.string().email('Email invalido.').min(1, 'Email e obrigatorio.'),
  discord_username: z.string().optional(),
  phone_number: z.string().optional(),
  new_password: z.string().min(8, 'Senha deve ter pelo menos 8 caracteres.'),
})

export type OnboardingFormValues = z.infer<typeof onboardingSchema>

const STEPS = [
  { id: 1, label: 'Perfil' },
  { id: 2, label: 'Bio' },
  { id: 3, label: 'Contato' },
  { id: 4, label: 'Senha' },
  { id: 5, label: 'Confirmar' },
]

export function OnboardingWizard() {
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      username: '',
      bio: '',
      email: '',
      discord_username: '',
      phone_number: '',
      new_password: '',
    },
    mode: 'onChange',
  })

  const handleComplete = async () => {
    setSubmitting(true)
    setError('')
    try {
      const values = form.getValues()
      await completeOnboarding({
        first_name: values.first_name,
        last_name: values.last_name,
        username: values.username,
        bio: values.bio || undefined,
        email: values.email,
        discord_username: values.discord_username || undefined,
        phone_number: values.phone_number || undefined,
        new_password: values.new_password,
        avatar_key: values.avatar_key || undefined,
        banner_key: values.banner_key || undefined,
      })
      router.push('/')
    } catch (e: unknown) {
      const err = e as { message?: string }
      setError(err.message ?? 'Erro ao completar onboarding.')
      setSubmitting(false)
    }
  }

  return (
    <FormProvider {...form}>
      <div className="w-full max-w-md mx-auto space-y-6">
        <OnboardingProgress steps={STEPS} currentStep={step} />

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {step === 1 && <StepProfile onNext={() => setStep(2)} />}
            {step === 2 && <StepBio onNext={() => setStep(3)} onBack={() => setStep(1)} />}
            {step === 3 && <StepContact onNext={() => setStep(4)} onBack={() => setStep(2)} />}
            {step === 4 && <StepPassword onNext={() => setStep(5)} onBack={() => setStep(3)} />}
            {step === 5 && (
              <StepPreview
                onBack={() => setStep(4)}
                onComplete={handleComplete}
                submitting={submitting}
                error={error}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </FormProvider>
  )
}
