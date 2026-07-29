'use server'

import 'server-only'
import { api } from '@/lib/api'

export type EventType = 'UNIVERSITY_PARTY' | 'BIRTHDAY' | 'CLUB' | 'CASUAL_HANGOUT' | 'BARBECUE'
  | 'AFTER_PARTY' | 'GRADUATION' | 'SHOW' | 'FESTIVAL' | 'DINNER' | 'TRIP' | 'CABULOUS' | 'CINEMA'

export type EventStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

export type Audience = 'ILUMINADOS' | 'VOYEURS' | 'ELETRONICOS' | 'OTHERS'

export interface EventLocationRead {
  id: string
  name: string
  address: string
  latitude: number
  longitude: number
}

export interface EventRead {
  id: string
  title: string
  description: string
  start_at: string
  end_at: string
  type: EventType
  type_color: string
  status: EventStatus
  cancelled_at: string | null
  audiences: Audience[]
  participants_count: number
  location: EventLocationRead | null
  thumbnail_url: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface EventListParams {
  starts_from?: string
  starts_until?: string
  status?: EventStatus
  type?: EventType
  audience?: Audience
  participant?: string
  creator?: string
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface ParticipantRead {
  id: string
  user: string
  username: string
  created_at: string
}

export interface EventPhotoRead {
  id: string
  photo: string
  content_type: string
  object_key: string
  is_thumbnail: boolean
  created_at: string
}

export interface HighlightPhotoRead {
  id: string
  object_key: string
  content_type: string
}

export interface HighlightRead {
  id: string
  text: string
  author_id: string
  photos: HighlightPhotoRead[]
  created_at: string
  updated_at: string
}

export interface EventOptions {
  types: { value: EventType; label: string; color: string }[]
  audiences: { value: Audience; label: string }[]
  statuses: { value: EventStatus; label: string }[]
}

export async function getEvents(params: EventListParams = {}): Promise<PaginatedResponse<EventRead>> {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      searchParams.set(key, String(value))
    }
  })
  return api.get('api/events/', { searchParams }).json<PaginatedResponse<EventRead>>()
}

export async function getEvent(id: string): Promise<EventRead> {
  return api.get(`api/events/${id}/`).json<EventRead>()
}

export async function getEventParticipants(
  eventId: string,
  page?: number,
): Promise<PaginatedResponse<ParticipantRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/participants/`, { searchParams }).json<PaginatedResponse<ParticipantRead>>()
}

export async function getEventPhotos(eventId: string, page?: number): Promise<PaginatedResponse<EventPhotoRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/photos/`, { searchParams }).json<PaginatedResponse<EventPhotoRead>>()
}

export async function getEventHighlights(eventId: string, page?: number): Promise<PaginatedResponse<HighlightRead>> {
  const searchParams = page ? new URLSearchParams({ page: String(page) }) : undefined
  return api.get(`api/events/${eventId}/highlights/`, { searchParams }).json<PaginatedResponse<HighlightRead>>()
}

export async function getEventOptions(): Promise<EventOptions> {
  return api.get('api/events/options/').json<EventOptions>()
}
