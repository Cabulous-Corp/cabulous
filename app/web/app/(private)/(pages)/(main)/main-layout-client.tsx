'use client'

import { usePathname } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'
import { SidebarSection } from '@/components/layout/types'
import { MdHome, MdEvent } from 'react-icons/md'

type SessionUser = { id: string; email: string; username: string } | null

export function MainLayoutClient({ children }: { children: React.ReactNode; user: SessionUser }) {
  const pathname = usePathname()

  const sidebarSections: SidebarSection[] = [
    {
      items: [{ label: 'Home', href: '/', icon: MdHome, end: true, active: pathname === '/' }],
    },
    {
      title: 'Eventos',
      items: [{ label: 'Calendario', href: '/events', icon: MdEvent, active: pathname.startsWith('/events') }],
    },
  ]

  return (
    <Layout sidebarSections={sidebarSections} showBackButton={false}>
      {children}
    </Layout>
  )
}
