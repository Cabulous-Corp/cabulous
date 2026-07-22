'use client'

import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { SidebarSection } from './types'
import { cn } from '@/utils/utils'

interface LayoutProps {
  children: ReactNode
  showBackButton?: boolean
  backPath?: string
  sidebarSections?: SidebarSection[]
}

export function Layout({ children, showBackButton, backPath, sidebarSections }: LayoutProps) {
  return (
    <div className={cn('min-h-dvh bg-background')}>
      <Sidebar sections={sidebarSections} showBackButton={showBackButton ?? false} backPath={backPath} />

      <main className="flex-1 md:pl-72 md:pr-4 px-1 pb-8 pt-4 relative z-10">{children}</main>
    </div>
  )
}
