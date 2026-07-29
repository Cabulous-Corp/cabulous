'use server'

import 'server-only'
import { api } from '@/lib/api'

interface SignedUrlResponse {
  url: string
  fields: Record<string, string>
  object_key: string
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

export async function uploadToSignedUrl(
  signedUrl: string,
  fields: Record<string, string>,
  file: File,
): Promise<string> {
  const formData = new FormData()
  Object.entries(fields).forEach(([key, value]) => {
    formData.append(key, value)
  })
  formData.append('file', file)

  const response = await fetch(signedUrl, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('Upload failed')
  }

  return fields.key
}
