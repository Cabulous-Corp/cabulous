import { PageLayout } from '@/components/layout/PageLayout'

export default async function HomeLayout({ children }: { children: React.ReactNode }) {
  // TODO: Personalizar o layout da home se necessário
  return (
    <PageLayout
      title="Bem-vindo"
      description="Gerencie suas campanhas e dashboard."
    >
      {children}
    </PageLayout>
  )
}
