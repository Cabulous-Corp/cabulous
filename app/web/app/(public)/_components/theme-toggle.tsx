'use client'

import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { setTheme } = useTheme()

  return (
    <div className="flex items-center gap-1">
      <Button variant="ghost" size="sm" onClick={() => setTheme('light')}>
        Claro
      </Button>
      <Button variant="ghost" size="sm" onClick={() => setTheme('dark')}>
        Escuro
      </Button>
      <Button variant="ghost" size="sm" onClick={() => setTheme('system')}>
        Sistema
      </Button>
    </div>
  )
}