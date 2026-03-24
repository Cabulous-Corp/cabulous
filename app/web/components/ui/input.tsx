import * as React from 'react'
import { AlertCircle } from 'lucide-react'

import { cn } from '@/utils/utils'

interface InputProps extends React.ComponentProps<'input'> {
  error?: string
  startAdornment?: React.ReactNode
}

function Input({ className, type, error, startAdornment, ...props }: InputProps) {
  const isInvalid = error || props['aria-invalid'] === true || props['aria-invalid'] === 'true'

  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="relative w-full">
        {startAdornment && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
            {startAdornment}
          </div>
        )}
        <input
          type={type}
          data-slot="input"
          aria-invalid={isInvalid ? true : undefined}
          className={cn(
            // Base styles
            'h-12 w-full min-w-0 px-4 rounded-lg bg-input dark:bg-input/30',
            'text-base transition-all outline-none border border-input hover:border-border/80',
            // Typography & Selection
            'file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
            // File input specific
            'file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium',
            // Interaction states
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none',
            // Validation states
            'aria-invalid:border-destructive aria-invalid:ring-destructive dark:aria-invalid:ring-destructive',
            startAdornment && 'pl-10',
            isInvalid && 'pr-12',
            className,
          )}
          {...props}
        />
        {isInvalid && (
          <AlertCircle
            className="absolute top-1/2 -translate-y-1/2 right-5 w-5 h-5 text-destructive pointer-events-none"
            aria-hidden="true"
          />
        )}
      </div>
      {error && <p className="text-xs text-destructive font-medium pl-4">{error}</p>}
    </div>
  )
}

export { Input }
