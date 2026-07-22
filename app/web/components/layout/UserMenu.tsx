'use client'

import * as React from 'react'
import {
  Moon,
  Sun,
  Laptop,
  User,
  LogOut,
  Settings2,
  ChevronDown,
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { useRouter } from 'next/navigation'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { logoutAction } from '@/actions/session'
import { useUser } from '@/hooks/use-user'
import { Kbd } from '@/components/ui/kbd'

export function UserMenu() {
  const { user } = useUser()
  const { setTheme, theme } = useTheme()
  const router = useRouter()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className="p-3">
          <button className="flex h-12 w-full items-center justify-between rounded-lg border border-border/50 px-3 hover:bg-primary/20 transition-colors outline-none group">
            <div className="flex items-center gap-3">
              <Avatar className="flex items-center justify-center h-6 w-6 rounded-md border border-border/50 bg-primary/20 p-0.5 shrink-0">
                <AvatarFallback className="rounded-md text-[10px] pb-[1px] font-bold font-mono">
                  {user?.name?.[0]?.toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col items-start text-left">
                <span className="text-xs font-bold tracking-tight text-sidebar-foreground group-hover:text-primary transition-colors">
                  {user?.name || 'Minha Conta'}
                </span>
              </div>
            </div>
            <ChevronDown className="h-3 w-3 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors" />
          </button>
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-(--radix-dropdown-menu-trigger-width) min-w-56" align="start" sideOffset={4}>
        
        {/* System Section */}
        <DropdownMenuLabel className="text-xs text-muted-foreground">Conta</DropdownMenuLabel>
        <DropdownMenuItem className="gap-2 p-2 cursor-pointer" onClick={() => router.push('/settings/account')}>
          <div className="flex size-6 items-center justify-center rounded-md border bg-background">
            <User className="size-4" />
          </div>
          <div className="font-medium text-muted-foreground">Meu Perfil</div>
        </DropdownMenuItem>

        <DropdownMenuItem className="gap-2 p-2 cursor-pointer" onClick={() => router.push('/settings/admin')}>
          <div className="flex size-6 items-center justify-center rounded-md border bg-background">
            <Settings2 className="size-4" />
          </div>
          <div className="font-medium text-muted-foreground">Configurações</div>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Preferences Section */}
        <DropdownMenuLabel className="text-xs text-muted-foreground">Preferências</DropdownMenuLabel>

        <DropdownMenuSub>
          <DropdownMenuSubTrigger className="gap-2 p-2 cursor-pointer">
            <div className="h-4 w-4 flex items-center justify-center">
              {theme === 'light' ? (
                <Sun className="h-4 w-4" />
              ) : theme === 'dark' ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Laptop className="h-4 w-4" />
              )}
            </div>
            <span>Tema</span>
            <Kbd>T</Kbd>
          </DropdownMenuSubTrigger>
          <DropdownMenuPortal>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => setTheme('light')} className="gap-2 cursor-pointer">
                <Sun className="h-4 w-4" />
                <span>Claro</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme('dark')} className="gap-2 cursor-pointer">
                <Moon className="h-4 w-4" />
                <span>Escuro</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme('system')} className="gap-2 cursor-pointer">
                <Laptop className="h-4 w-4" />
                <span>Sistema</span>
              </DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuPortal>
        </DropdownMenuSub>

        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <form
            action={logoutAction}
            className="gap-2 p-2 cursor-pointer text-destructive hover:text-destructive/80 hover:bg-destructive/10"
          >
            <button type="submit" className="w-full flex items-center gap-2 cursor-pointer">
              <div className="flex size-6 items-center justify-center rounded-md border border-destructive/40 bg-background">
                <LogOut className="size-4" />
              </div>
              <div className="font-medium">Sair</div>
            </button>
          </form>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
