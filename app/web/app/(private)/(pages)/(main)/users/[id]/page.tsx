import { getUser, getUserEvents } from '@/lib/api/users'
import { verifySessionWithoutRedirect } from '@/actions/session'
import { ProfileClient } from './_components/ProfileClient'
import { notFound } from 'next/navigation'

interface Props {
  params: Promise<{ id: string }>
}

export default async function UserProfilePage({ params }: Props) {
  const { id } = await params
  const [profile, sessionUser, createdEvents, participatingEvents] = await Promise.all([
    getUser(id).catch(() => null),
    verifySessionWithoutRedirect(),
    getUserEvents(id, 'created').catch(() => null),
    getUserEvents(id, 'participating').catch(() => null),
  ])
  if (!profile) notFound()
  const isOwn = sessionUser?.id === profile.id
  return (
    <ProfileClient
      profile={profile}
      isOwn={isOwn}
      createdEvents={createdEvents}
      participatingEvents={participatingEvents}
    />
  )
}
