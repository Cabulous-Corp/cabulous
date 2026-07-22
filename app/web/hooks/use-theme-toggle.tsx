'use client'

import { useEffect } from 'react'
import { useTheme } from 'next-themes'
import { toast } from 'sonner'
import { MdDarkMode, MdLightMode } from 'react-icons/md'

const INPUTABLE_TAGS = ['INPUT', 'TEXTAREA', 'SELECT']

export function useThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement

      // Ignore if typing in an inputable element
      if (
        INPUTABLE_TAGS.includes(target.tagName) ||
        target.isContentEditable ||
        target.closest('[contenteditable="true"]')
      ) {
        return
      }

      if (e.key === 't' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const current = resolvedTheme ?? 'light'
        const next = current === 'dark' ? 'light' : 'dark'
        setTheme(next)

        toast(`Tema alterado para ${next === 'dark' ? 'escuro' : 'claro'}`, {
          duration: 2000,
          icon: next === 'dark' ? <MdDarkMode /> : <MdLightMode />,
        })
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [resolvedTheme, setTheme])
}
