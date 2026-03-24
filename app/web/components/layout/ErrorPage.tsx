'use client'

import { Button } from '@/components/ui/button'
import Link from 'next/link'

export function ErrorPage({ message, description }: { message: string; description?: string }) {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-6 text-center max-w-md px-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tighter">{message}</h1>
          {description && <p className="text-muted-foreground">{description}</p>}
        </div>
        <Button asChild variant="outline">
          <Link href="/">Voltar para o Início</Link>
        </Button>
      </div>
    </div>
  )
}
