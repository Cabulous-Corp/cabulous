import * as React from 'react'
import { AlertCircle } from 'lucide-react'

import { cn } from '@/utils/utils'

interface TextareaProps extends React.ComponentProps<'textarea'> {
  error?: string
}

function Textarea({ className, error, ...props }: TextareaProps) {
  const isInvalid = error || props['aria-invalid'] === true || props['aria-invalid'] === 'true'

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="relative w-full">
        <textarea
          data-slot="textarea"
          aria-invalid={isInvalid ? true : undefined}
          className={cn(
            // Base styles
            'flex w-full min-h-24 px-4 py-3 rounded-lg bg-input dark:bg-input/30',
            'text-base transition-all outline-none border border-input hover:border-border/80',
            // Typography & Selection
            'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
            // Interaction states
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none',
            // Validation states
            'aria-invalid:border-destructive aria-invalid:ring-destructive',
            isInvalid && 'pr-12',
            className,
          )}
          {...props}
        />
        {isInvalid && (
          <AlertCircle
            className="absolute top-4 right-5 w-5 h-5 text-destructive pointer-events-none"
            aria-hidden="true"
          />
        )}
      </div>
      {error && <p className="text-xs text-destructive font-medium pl-4">{error}</p>}
    </div>
  )
}

export { Textarea }
