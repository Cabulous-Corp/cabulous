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
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{currentStep} de {steps.length}</span>
      </div>
      <div className="flex gap-1">
        {steps.map((s) => (
          <div
            key={s.id}
            className={`h-1 flex-1 rounded-full transition-colors ${
              s.id <= currentStep ? 'bg-primary' : 'bg-muted'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
