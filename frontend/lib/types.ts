// Shapes returned by the CampusConnect FastAPI backend (see docs/API.md).

export type Role = "USER" | "ADMIN"
export type EventStatus = "pending" | "approved" | "rejected"

export interface CurrentUser {
  user_id: string
  email: string
  name: string
  year: number | null
  department: string | null
  profile_picture: string | null
  role: Role
  profile_completed: boolean
  created_at: string
}

export interface PublicUser {
  user_id: string
  name: string
  year: number | null
  department: string | null
  profile_picture: string | null
  followers_count: number
  following_count: number
}

export interface PersonSummary {
  user_id: string
  name: string
  year: number | null
  department: string | null
  profile_picture: string | null
  is_following?: boolean | null
  mutual_count?: number | null
}

export interface EventItem {
  event_id: string
  title: string
  description: string
  category: string
  host_id: string
  host_name: string | null
  date: string // YYYY-MM-DD
  start_time: string // HH:MM
  end_time: string
  venue: string
  registration_url: string | null
  poster_url: string | null
  tags: string[]
  status: EventStatus
  rejection_reason: string | null
  created_at: string
  like_count: number
  registration_count: number
  is_liked_by_me: boolean
  is_registered_by_me: boolean
}

export interface EventDetail extends EventItem {
  view_count: number
  share_count: number
}

export interface FeedUserAction {
  user_id: string
  name: string
  action: string
}

export interface FeedItem extends EventItem {
  social_context: { reason: string; users: FeedUserAction[] } | null
}

export interface CommentItem {
  comment_id: string
  event_id: string
  user_id: string
  user_name: string | null
  user_picture: string | null
  content: string
  created_at: string
}

export interface CommonInterest {
  event_id: string
  title: string
  category: string
  interaction_type: string
}

export interface EventAnalytics {
  total_events: number
  approved_events: number
  pending_events: number
  rejected_events: number
  by_category: Record<string, number>
  events_by_host: { host_id: string; host_name: string; total_submitted: number }[]
}

export interface NetworkAnalytics {
  total_users: number
  total_follows: number
  most_followed_users: { user_id: string; name: string; follower_count: number }[]
  most_interacted_events: { event_id: string; title: string; interaction_count: number }[]
}

export interface AuthTokenData {
  access_token: string
  token_type: string
  user_id: string
  role: Role
  profile_completed: boolean
}

export interface EventDraft {
  title: string
  description: string
  category: string
  date: string
  start_time: string
  end_time: string
  venue: string
  registration_url?: string | null
  poster_url?: string | null
  tags: string[]
}
