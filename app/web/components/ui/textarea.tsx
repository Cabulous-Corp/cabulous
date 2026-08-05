import * as React from 'react'
import { AlertCircle } from 'lucide-react'

import { cn } from '@/utils/utils'

interface TextareaProps extends React.ComponentProps<'textarea'> {
  error?: string
}

function Textarea({ className, error, ...props }: TextareaProps) {
  const isInvalid = error || props['aria-invalid'] === true || props['aria-invalid'] === 'true'

  return (
    <div className="flex w-full flex-col gap-1.5">
      <div className="relative w-full">
        <textarea
          data-slot="textarea"
          aria-invalid={isInvalid ? true : undefined}
          className={cn(
            'flex min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-base shadow-xs transition-colors outline-none md:text-sm',
            'placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground',
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50',
            'aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
            isInvalid && 'pr-10',
            className,
          )}
          {...props}
        />
        {isInvalid && (
          <AlertCircle
            className="pointer-events-none absolute top-3 right-3 size-4 text-destructive"
            aria-hidden="true"
          />
        )}
      </div>
      {error && <p className="pl-1 text-xs font-medium text-destructive">{error}</p>}
    </div>
  )
}

export { Textarea }
