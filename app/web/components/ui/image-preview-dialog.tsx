'use client'

import Image from 'next/image'
import { Eye } from 'lucide-react'

import { cn } from '@/utils/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useState } from 'react'

interface ImagePreviewDialogProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  triggerClassName?: string
  dialogContentClassName?: string
}

export function ImagePreviewDialog({
  src,
  alt,
  width = 80,
  height = 80,
  className,
  triggerClassName,
  dialogContentClassName,
}: ImagePreviewDialogProps) {
  const [open, setOpen] = useState(false)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen(true)
        }}
        className={cn(
          'group relative rounded-md overflow-hidden border border-border/60 hover:border-primary/50 transition-colors cursor-pointer',
          triggerClassName,
        )}
        aria-label="Abrir preview da imagem"
      >
        <Image src={src} alt={alt} width={width} height={height} unoptimized className={cn('object-cover', className)} />
        <div className="absolute inset-0 bg-black/45 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <Eye className="w-5 h-5 text-white" />
        </div>
      </button>

      <DialogContent className={cn('sm:max-w-4xl p-3', dialogContentClassName)}>
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || 'Preview da imagem'}</DialogTitle>
        </DialogHeader>
        <div className="w-full flex items-center justify-center rounded-md overflow-hidden bg-muted/30">
          <Image
            src={src}
            alt={alt || 'Preview da imagem'}
            width={1400}
            height={1000}
            unoptimized
            className="max-h-[80vh] w-auto h-auto object-contain"
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
