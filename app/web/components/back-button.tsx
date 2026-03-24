'use client'

import { Button } from './ui/button'
import { useRouter } from 'next/navigation'
import { cn } from '@/utils/utils'
import { ArrowLeft } from 'lucide-react'

export default function BackButton({ className, path }: { className?: string; path?: string }) {
  const router = useRouter()

  const handleBack = () => {
    if (path) {
      router.push(path)
    } else {
      router.back()
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn('gap-2 px-3 h-9 text-sidebar-foreground/60 hover:text-sidebar-foreground', className)}
      onClick={handleBack}
    >
      <ArrowLeft className="h-4 w-4" />
      <span className="text-xs font-medium">Voltar</span>
    </Button>
  )
}
