'use server'

import 'server-only'
import { api } from '@/lib/api'

interface SignedUrlResponse {
  upload_url: string
  method: 'PUT'
  headers: Record<string, string>
  object_key: string
  expires_in: number
}

export async function getSignedUploadUrl(
  fileType: 'avatar' | 'banner',
  filename: string,
  contentType: string,
): Promise<SignedUrlResponse> {
  return api
    .post('api/users/uploads/signed-url/', {
      json: { file_type: fileType, filename, content_type: contentType },
    })
    .json<SignedUrlResponse>()
}
