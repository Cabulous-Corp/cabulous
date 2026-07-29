'use server'

import 'server-only'
import { api } from '@/lib/api'

type MediaPhoto = {
  id: string
  object_key: string
  content_type: string
}

export async function uploadMediaPhoto(formData: FormData): Promise<MediaPhoto> {
  return api.post('api/media/', { body: formData }).json<MediaPhoto>()
}
