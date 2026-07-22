import { ModeToggle } from '@/components/mode-toggle'

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  // TODO: Personalizar o layout público (termos, privacidade, etc)
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative">
      <div className="absolute top-4 right-4 z-30">
        <ModeToggle />
      </div>
      {children}
    </div>
  )
}
