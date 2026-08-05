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
    <div className="flex w-full flex-col gap-1.5">
      <div className="relative w-full">
        {startAdornment && (
          <div className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground">
            {startAdornment}
          </div>
        )}
        <input
          type={type}
          data-slot="input"
          aria-invalid={isInvalid ? true : undefined}
          minLength={type === 'password' ? 8 : undefined}
          required={type === 'password' || type === 'email' ? true : undefined}
          className={cn(
            'flex h-9 w-full min-w-0 rounded-md border border-input bg-background px-3 py-1 text-base shadow-xs transition-colors outline-none md:text-sm',
            'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground',
            'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
            'aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
            startAdornment && 'pl-10',
            isInvalid && 'pr-10',
            className,
          )}
          {...props}
        />
        {isInvalid && (
          <AlertCircle
            className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-destructive"
            aria-hidden="true"
          />
        )}
      </div>
      {error && <p className="pl-1 text-xs font-medium text-destructive">{error}</p>}
    </div>
  )
}

export { Input }
