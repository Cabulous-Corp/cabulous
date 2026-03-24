'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { forwardRef } from 'react'
import { cn } from '@/utils/utils'

interface NavLinkProps {
  href: string
  target?: string
  className?: string
  activeClassName?: string
  pendingClassName?: string
  end?: boolean
  children: React.ReactNode
}

const NavLink = forwardRef<HTMLAnchorElement, NavLinkProps>(
  ({ className, activeClassName, pendingClassName, href, target, end, children, ...props }, ref) => {
    const pathname = usePathname()
    const isActive = end ? pathname === href : pathname === href || pathname.startsWith(href + '/')

    return (
      <Link ref={ref} href={href} target={target} className={cn(className, isActive && activeClassName)} {...props}>
        {children}
      </Link>
    )
  },
)

NavLink.displayName = 'NavLink'

export { NavLink }
