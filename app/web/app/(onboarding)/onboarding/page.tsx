import { verifySessionWithoutRedirect } from '@/actions/session'
import { redirect } from 'next/navigation'
import { OnboardingWizard } from './_components/OnboardingWizard'

export default async function OnboardingPage() {
  const user = await verifySessionWithoutRedirect()
  if (user?.onboarding_completed_at) {
    redirect('/')
  }
  return <OnboardingWizard />
}
