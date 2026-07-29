'use client'

import { useState } from 'react'
import { Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ProfileEditSheet } from './ProfileEditSheet'
import type { UserProfile } from '@/lib/api/users'

interface Props {
  profile: UserProfile
  isOwn: boolean
}

export function ProfileInfo({ profile, isOwn }: Props) {
  const [editOpen, setEditOpen] = useState(false)

  return (
    <div className="px-4 space-y-4">
      {profile.bio && (
        <p className="text-muted-foreground leading-relaxed">{profile.bio}</p>
      )}

      <div className="flex flex-wrap gap-4 text-sm">
        {profile.discord_username && (
          <span className="text-muted-foreground">
            Discord: {profile.discord_username}
          </span>
        )}
        {profile.phone_number && (
          <span className="text-muted-foreground">
            Tel: {profile.phone_number}
          </span>
        )}
      </div>

      {isOwn && (
        <>
          <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
            <Pencil className="size-3 mr-1" /> Editar perfil
          </Button>
          <ProfileEditSheet
            profile={profile}
            open={editOpen}
            onOpenChange={setEditOpen}
          />
        </>
      )}
    </div>
  )
}
