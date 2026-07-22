export type SidebarLinkItem = {
  href: string
  target?: string
  icon?: any
  label: string
  end?: boolean
  active?: boolean
  matchQuery?: { param: string; value: string }
}

export type SidebarCollapsibleItem = {
  id: string
  icon: any
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
