'use client'

interface Step {
  id: number
  label: string
}

interface Props {
  steps: Step[]
  currentStep: number
}

export function OnboardingProgress({ steps, currentStep }: Props) {
  return (
    <div
      className="space-y-2"
      role="progressbar"
      aria-label={`Progresso do onboarding: etapa ${currentStep} de ${steps.length}`}
      aria-valuemin={1}
      aria-valuemax={steps.length}
      aria-valuenow={currentStep}
    >
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Etapa {currentStep} de {steps.length}</span>
        <span>{steps[currentStep - 1]?.label}</span>
      </div>
      <div className="flex gap-1.5">
        {steps.map((s) => (
          <div
            key={s.id}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              s.id <= currentStep ? 'bg-primary' : 'bg-muted'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
