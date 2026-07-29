'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { UserMenu } from './UserMenu'
import Logo from '@/components/logo'
import { SidebarSection } from './types'
import { SidebarItemNode } from './SidebarItemNode'

import React, { Suspense } from 'react'

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
  exit: { opacity: 0 },
}

export function Sidebar({ sections }: { sections?: SidebarSection[] }) {
  return (
    <div
      className={
        'fixed left-0 bottom-0 top-0 z-50 w-66 h-full rounded-tr-xl rounded-br-xl duration-300 ease-in-out overflow-hidden delay-0 hidden md:flex bg-sidebar border-r border-white/5 px-1 pt-4 pb-2'
      }
    >
      <aside className={'flex flex-col h-full relative z-20 w-full'}>
        <Logo className="p-2 h-9 mb-4" href="/" />
        <UserMenu />

        <AnimatePresence mode="wait">
          <motion.div
            key="main-nav"
            className="flex flex-col flex-1 overflow-hidden"
            variants={containerVariants}
            initial="hidden"
            animate="show"
            exit="exit"
          >
            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
              <Suspense fallback={<div className="h-20 animate-pulse bg-sidebar-accent/5 rounded-md" />}>
                {sections?.map((section, idx) => (
                  <div key={idx} className="mb-4 space-y-1 flex-col">
                    {section.title && (
                      <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                        {section.title}
                      </h3>
                    )}
                    {section.items.map((item, itemIdx) => (
                      <SidebarItemNode key={itemIdx} item={item} />
                    ))}
                  </div>
                ))}
              </Suspense>
            </div>
          </motion.div>
        </AnimatePresence>
      </aside>
    </div>
  )
}