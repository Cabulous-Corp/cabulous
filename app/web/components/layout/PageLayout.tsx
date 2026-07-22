'use client'

import React, { ReactNode } from 'react'
import { motion } from 'framer-motion'

type PageLayoutProps = React.PropsWithChildren<{
  title: string
  description?: string
  actions?: ReactNode
  titleSlot?: ReactNode
  preTitle?: ReactNode
}>

export function PageLayout({ title, preTitle, description, actions, titleSlot, children }: PageLayoutProps) {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        delay: 0.2,
        staggerChildren: 0.1,
      },
    },
  }

  return (
    <motion.div className="space-y-6 pt-4 pb-10 md:pb-40 px-2" variants={container} initial="hidden" animate="show">
      <div className="flex items-center justify-between z-10 sticky top-0 bg-background py-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-primary tracking-tight">{title}</h1>
            {titleSlot}
          </div>
          {description && <p className="mt-1 text-base text-muted-foreground">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className="space-y-6">{children}</div>
    </motion.div>
  )
}
