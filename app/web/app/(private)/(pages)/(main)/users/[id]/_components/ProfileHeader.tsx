'use client'

import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import type { UserProfile } from '@/lib/api/users'

interface Props {
  profile: UserProfile
}

function getMediaUrl(key: string | null): string | null {
  if (!key) return null
  return `${process.env.NEXT_PUBLIC_MEDIA_URL ?? ''}${key}`
}

export function ProfileHeader({ profile }: Props) {
  const bannerUrl = getMediaUrl(profile.banner)
  const avatarUrl = getMediaUrl(profile.avatar)
  const initials =
    `${profile.first_name?.[0] ?? ''}${profile.last_name?.[0] ?? ''}`.toUpperCase() || '?'

  return (
    <div>
      <div className="relative w-full aspect-[3/1] rounded-xl overflow-hidden bg-gradient-to-r from-primary/30 to-accent/30">
        {bannerUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={bannerUrl} alt="" className="w-full h-full object-cover" />
        ) : null}
      </div>

      <div className="flex items-end gap-4 -mt-12 px-4">
        <Avatar className="size-24 border-4 border-background rounded-full shrink-0">
          {avatarUrl ? <AvatarImage src={avatarUrl} alt={profile.full_name} /> : null}
          <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
        </Avatar>
        <div className="pb-2">
          <h1 className="text-2xl font-bold">{profile.full_name}</h1>
          <p className="text-muted-foreground">@{profile.username}</p>
        </div>
      </div>
    </div>
  )
}
