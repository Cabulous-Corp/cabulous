'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { User, Loader2, Pencil, Trash2, Upload } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

// TODO: Restore these imports when the profile actions are implemented
// import { 
//   createAvatarUploadTicket, 
//   confirmAvatarUpload, 
//   getUser, 
//   removeAvatar 
// } from '@/actions/profile'

interface AvatarUploadProps {
  initialAvatarUrl?: string | null
  userName?: string
}

export function AvatarUpload({ initialAvatarUrl, userName }: AvatarUploadProps) {
  const [avatarUrl, setAvatarUrl] = useState<string | null>(initialAvatarUrl || null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.size > 2 * 1024 * 1024) {
      toast.error('O arquivo deve ter no máximo 2MB')
      return
    }

    try {
      setIsUploading(true)
      // Mocking the upload process for now
      // const ticket = await createAvatarUploadTicket(file.name, file.type)
      // await confirmAvatarUpload(ticket.file_id)
      
      const objectUrl = URL.createObjectURL(file)
      setAvatarUrl(objectUrl)
      toast.success('Avatar atualizado com sucesso!')
    } catch (error) {
      toast.error('Erro ao fazer upload do avatar')
    } finally {
      setIsUploading(false)
    }
  }

  const handleRemove = async () => {
    try {
      setIsUploading(true)
      // await removeAvatar()
      setAvatarUrl(null)
      toast.success('Avatar removido com sucesso!')
    } catch (error) {
      toast.error('Erro ao remover o avatar')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="relative group">
      <Avatar className="h-24 w-24 border-2 border-border/50">
        <AvatarImage src={avatarUrl || undefined} alt={userName} />
        <AvatarFallback className="text-xl font-bold bg-primary/10">
          {userName?.[0]?.toUpperCase() || <User className="h-10 w-10 text-muted-foreground/50" />}
        </AvatarFallback>
      </Avatar>

      <div className="absolute -bottom-1 -right-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 rounded-full shadow-sm bg-background hover:bg-muted"
              disabled={isUploading}
            >
              {isUploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Pencil className="h-4 w-4" />
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => fileInputRef.current?.click()} className="gap-2 cursor-pointer">
              <Upload className="h-4 w-4" />
              <span>Fazer upload</span>
            </DropdownMenuItem>
            {avatarUrl && (
              <DropdownMenuItem onClick={handleRemove} className="gap-2 cursor-pointer text-destructive">
                <Trash2 className="h-4 w-4" />
                <span>Remover avatar</span>
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="hidden"
      />
    </div>
  )
}
