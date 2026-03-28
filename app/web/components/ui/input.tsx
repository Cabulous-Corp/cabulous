import * as React from 'react'
import { AlertCircle } from 'lucide-react'

import { cn } from '@/utils/utils'

interface InputProps extends React.ComponentProps<'input'> {
  error?: string
  startAdornment?: React.ReactNode
  requirement?: string
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
          minLength={type === 'password' ? 8 : undefined}
          required={(type === 'password' || type === 'email' ? true : false)}
          className={cn(
            // Base styles
            "h-16 w-100 min-w-0 px-4 rounded-md bg-input",
            'text-base transition-all outline-none border border-input hover:border-purple-500',
            // Typography & Selection
            'file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
            // File input specific
            'file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium',
            // Interaction states
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'focus-within:ring-2 focus-within:ring-accent  focus-within:border-accent',
            'hover:ring-2 hover:ring-accent user-invalid:ring-2 user-invalid:ring-red-500',
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
