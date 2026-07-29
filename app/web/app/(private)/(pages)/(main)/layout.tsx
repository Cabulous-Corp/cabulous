import { verifySessionWithoutRedirect } from '@/actions/session'
import { MainLayoutClient } from './main-layout-client'

export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const user = await verifySessionWithoutRedirect()
  return <MainLayoutClient user={user}>{children}</MainLayoutClient>
}
