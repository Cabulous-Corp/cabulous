'use client'

import { usePathname } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'
import { SidebarSection } from '@/components/layout/types'
import { Home } from 'lucide-react'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  // TODO: Implementar links dinâmicos e sessões da sidebar conforme necessário
  const sidebarSections: SidebarSection[] = [
    {
      items: [
        {
          label: 'Home',
          href: '/',
          icon: Home,
          end: true,
          active: pathname === '/',
        },
      ],
    },
  ]

  return (
    <Layout sidebarSections={sidebarSections}>
      {children}
    </Layout>
  )
}