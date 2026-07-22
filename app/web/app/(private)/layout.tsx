import { verifySession } from '@/actions/session'
import { redirect } from 'next/navigation'
import { UserProvider } from '@/hooks/use-user'

export default async function PrivateLayout({ children }: { children: React.ReactNode }) {
  // TODO: Re-implementar a verificação de sessão e redirecionamento no futuro
  /*
  const user = await verifySession()

  if (!user) {
    redirect('/login')
  }

  */

  return <UserProvider>{children}</UserProvider>
}
