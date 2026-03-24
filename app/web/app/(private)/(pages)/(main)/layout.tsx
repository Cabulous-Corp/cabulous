'use client'

import { useRouter, usePathname } from 'next/navigation'
import { Layout } from '@/components/layout/Layout'
import { SidebarSection } from '@/components/layout/types'
import { MdHome } from 'react-icons/md'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  // TODO: Implementar links dinâmicos e sessões da sidebar conforme necessário
  const sidebarSections: SidebarSection[] = [
    {
      items: [
        {
          label: 'Home',
          href: '/',
          icon: MdHome,
          end: true,
          active: pathname === '/',
        },
      ],
    },
  ]

  return (
    <Layout sidebarSections={sidebarSections} showBackButton={false}>
      {children}
    </Layout>
  )
}
