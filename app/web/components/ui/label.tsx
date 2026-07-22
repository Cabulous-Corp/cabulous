'use client'

import * as React from 'react'
import * as LabelPrimitive from '@radix-ui/react-label'
import { HelpCircle } from 'lucide-react'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'

import { cn } from '@/utils/utils'

export interface LabelProps extends React.ComponentProps<typeof LabelPrimitive.Root> {
  helperText?: string
  required?: boolean
}

function Label({ className, children, helperText, required, ...props }: LabelProps) {
  return (
    <LabelPrimitive.Root
      data-slot="label"
      className={cn(
        // Layout & Alignment
        'inline-flex items-center gap-2 leading-none cursor-pointer',
        // Typography & Interaction
        'text-sm font-medium text-heading',
        // Disabled States
        'group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50',
        'peer-disabled:cursor-not-allowed peer-disabled:opacity-50',
        className,
      )}
      {...props}
    >
      {children}
      {required && <span className="text-destructive">*</span>}
      {helperText && (
        <HoverCard openDelay={200}>
          <HoverCardTrigger asChild>
            <HelpCircle className="w-4 h-4 text-muted-foreground cursor-help" />
          </HoverCardTrigger>
          <HoverCardContent
            side="top"
            align="start"
            className="w-auto max-w-[280px] px-3 py-2 rounded-lg text-sm text-muted-foreground"
          >
            {helperText}
          </HoverCardContent>
        </HoverCard>
      )}
    </LabelPrimitive.Root>
  )
}

export { Label }
