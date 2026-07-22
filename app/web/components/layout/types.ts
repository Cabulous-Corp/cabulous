// ponytail: using React.ComponentType to cover both lucide-react and react-icons icon families
import type { ComponentType } from 'react'

export type IconComponent = ComponentType<{ className?: string }>

export type SidebarLinkItem = {
  href: string
  target?: string
  icon?: IconComponent
  label: string
  end?: boolean
  active?: boolean
  matchQuery?: { param: string; value: string }
}

export type SidebarCollapsibleItem = {
  id: string
  icon: IconComponent
  label: string
  items: {
    href: string
    target?: string
    label: string
    end?: boolean
  }[]
}

export type SidebarItem = SidebarLinkItem | SidebarCollapsibleItem

export type SidebarSection = {
  title?: string
  items: SidebarItem[]
}
