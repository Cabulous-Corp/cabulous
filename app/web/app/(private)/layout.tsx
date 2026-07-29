import { verifySessionWithoutRedirect } from '@/actions/session'
import { UserProvider } from '@/hooks/use-user'

export default async function PrivateLayout({ children }: { children: React.ReactNode }) {
  const user = await verifySessionWithoutRedirect()
  return <UserProvider user={user}>{children}</UserProvider>
}
