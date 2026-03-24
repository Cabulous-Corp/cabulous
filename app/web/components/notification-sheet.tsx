import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Bell } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Notification {
  id: string
  title: string
  description: string
  time: string
  isRead: boolean
}

const mockNotifications: Notification[] = [
  {
    id: '1',
    title: 'Campanha Aprovada',
    description: "Sua campanha 'Verão 2024' foi aprovada e já está ativa.",
    time: 'Há 2 horas',
    isRead: false,
  },
  {
    id: '2',
    title: 'Novo Participante',
    description: "João Silva acabou de se cadastrar na campanha 'Volta às Aulas'.",
    time: 'Há 5 horas',
    isRead: true,
  },
  {
    id: '3',
    title: 'Alerta de Sistema',
    description: 'Manutenção programada para o próximo domingo às 02:00.',
    time: 'Há 1 dia',
    isRead: true,
  },
]

export function NotificationSheet({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader className="mb-4">
          <SheetTitle>Notificações</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-100px)] pr-4">
          <div className="space-y-4">
            {mockNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 rounded-lg border ${
                  notification.isRead ? 'bg-background' : 'bg-muted/30'
                } transition-colors hover:bg-muted/50`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`mt-1 h-2 w-2 rounded-full ${notification.isRead ? 'bg-muted-foreground' : 'bg-primary'}`}
                  />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">{notification.title}</p>
                    <p className="text-sm text-muted-foreground">{notification.description}</p>
                    <p className="text-xs text-muted-foreground pt-1">{notification.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
