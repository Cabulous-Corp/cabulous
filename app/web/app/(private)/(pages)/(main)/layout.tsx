import { verifySessionWithoutRedirect } from '@/actions/session'
import { MainLayoutClient } from './main-layout-client'

type SessionUser = { id: string; email: string; username: string }

export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const user = await verifySessionWithoutRedirect()
  return <MainLayoutClient user={user}>{children}</MainLayoutClient>
}
