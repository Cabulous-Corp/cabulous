import { getSession } from '@/actions/session'
import { redirect } from 'next/navigation'
import { OnboardingWizard } from './_components/OnboardingWizard'

export default async function OnboardingPage() {
  const user = await getSession()
  if (!user) {
    redirect('/login')
  }
  if (user.onboarding_completed_at) {
    redirect('/')
  }
  return <OnboardingWizard />
}
