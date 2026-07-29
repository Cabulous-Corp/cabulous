'use server'

import 'server-only'
import { revalidatePath } from 'next/cache'
import { api } from '@/lib/api'
import { uploadMediaPhoto } from '@/lib/api/media'
import { verifySession } from '@/actions/session'

export async function uploadAndLinkPhoto(eventId: string, formData: FormData) {
  await verifySession()
  const photo = await uploadMediaPhoto(formData)
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photo.id } })
  revalidatePath(`/events/${eventId}`)
  return photo
}

export async function linkPhoto(eventId: string, photoId: string) {
  await verifySession()
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photoId } })
  revalidatePath(`/events/${eventId}`)
}

export async function unlinkPhoto(eventId: string, photoPk: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/photos/${photoPk}/`)
  revalidatePath(`/events/${eventId}`)
}

export async function setThumbnail(eventId: string, photoId: string) {
  await verifySession()
  await api.put(`api/events/${eventId}/thumbnail/`, { json: { photo_id: photoId } })
  revalidatePath(`/events/${eventId}`)
}

export async function uploadAndSetThumbnail(eventId: string, formData: FormData) {
  await verifySession()
  const photo = await uploadMediaPhoto(formData)
  await api.post(`api/events/${eventId}/photos/`, { json: { photo_id: photo.id } })
  await api.put(`api/events/${eventId}/thumbnail/`, { json: { photo_id: photo.id } })
  revalidatePath(`/events/${eventId}`)
  return photo
}

export async function clearThumbnail(eventId: string) {
  await verifySession()
  await api.delete(`api/events/${eventId}/thumbnail/`)
  revalidatePath(`/events/${eventId}`)
}
