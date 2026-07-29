'use client'

import { ProfileHeader } from './ProfileHeader'
import { ProfileInfo } from './ProfileInfo'
import { ProfileTabs } from './ProfileTabs'
import type { UserProfile } from '@/lib/api/users'
import type { PaginatedResponse, EventRead } from '@/lib/api/events'

interface Props {
  profile: UserProfile
  isOwn: boolean
  createdEvents: PaginatedResponse<EventRead> | null
  participatingEvents: PaginatedResponse<EventRead> | null
}

export function ProfileClient({ profile, isOwn, createdEvents, participatingEvents }: Props) {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <ProfileHeader profile={profile} />
      <ProfileInfo profile={profile} isOwn={isOwn} />
      <ProfileTabs
        userId={profile.id}
        createdEvents={createdEvents}
        participatingEvents={participatingEvents}
      />
    </div>
  )
}
