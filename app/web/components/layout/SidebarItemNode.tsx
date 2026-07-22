'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { NavLink } from '@/components/nav-link'
import { cn } from '@/utils/utils'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { usePathname, useSearchParams } from 'next/navigation'
import { SidebarItem } from './types'

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export function SidebarItemNode({ item }: { item: SidebarItem }) {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const isChildActive =
    'items' in item ? item.items.some((sub) => pathname === sub.href || pathname.startsWith(sub.href + '/')) : false
  const [isOpen, setIsOpen] = useState(isChildActive)

  if ('items' in item) {
    const Icon = item.icon

    return (
      <motion.div variants={itemVariants}>
        <Collapsible open={isOpen} onOpenChange={setIsOpen} className="space-y-1">
          <CollapsibleTrigger
            className={cn(
              // Layout & Alignment
              'flex w-full items-center justify-between px-3 py-2 rounded-md',
              // Typography & Interaction
              'text-sm font-medium text-sidebar-foreground transition-all duration-200',
              // Hover States
              'hover:bg-sidebar-accent/10 hover:text-sidebar-accent-foreground cursor-pointer',
              'group',
            )}
          >
            <div className="flex items-center gap-3">
              {Icon && <Icon className="h-5 w-5 shrink-0" />}
              <span>{item.label}</span>
            </div>
            <ChevronDown className={cn('h-4 w-4 transition-transform duration-200', isOpen ? 'rotate-180' : '')} />
          </CollapsibleTrigger>
          <CollapsibleContent className="overflow-hidden space-y-1 px-2 data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
            {item.items.map((sub, i) => (
              <NavLink
                key={i}
                href={sub.href}
                target={sub.target}
                end={sub.end}
                className={cn(
                  // Layout & Alignment
                  'flex items-center gap-3 px-3 pl-9 py-2 rounded-md',
                  // Typography & Interaction
                  'text-sm font-medium text-sidebar-foreground/80 transition-all duration-200',
                  // Hover States
                  'hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/10',
                )}
                activeClassName="text-sidebar-primary-foreground font-medium bg-sidebar-primary/20"
              >
                <span>{sub.label}</span>
              </NavLink>
            ))}
          </CollapsibleContent>
        </Collapsible>
      </motion.div>
    )
  }

  const Icon = item.icon
  const isActiveQueryMatch = item.matchQuery && searchParams.get(item.matchQuery.param) === item.matchQuery.value

  return (
    <motion.div variants={itemVariants}>
      <NavLink
        href={item.href}
        target={item.target}
        end={item.end}
        className={cn(
          // Layout & Alignment
          'flex items-center gap-3 px-3 py-2 rounded-md',
          // Typography & Interaction
          'text-sm font-medium text-sidebar-foreground transition-all duration-200',
          // Active & Hover Logic
          isActiveQueryMatch
            ? 'bg-sidebar-primary/30 text-sidebar-primary-foreground font-semibold'
            : 'text-sidebar-accent-foreground hover:bg-sidebar-accent/10 hover:text-sidebar-accent-foreground',
        )}
        activeClassName={!item.matchQuery ? 'bg-sidebar-primary/20 text-sidebar-primary-foreground font-semibold' : ''}
      >
        {Icon && <Icon className="h-5 w-5 shrink-0" />}
        <span>{item.label}</span>
      </NavLink>
    </motion.div>
  )
}
