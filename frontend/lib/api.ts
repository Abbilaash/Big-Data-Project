// Thin, typed client for the CampusConnect backend.
//
// - Reads the API origin from NEXT_PUBLIC_API_URL (default http://localhost:8000).
// - Attaches the bearer token kept in localStorage.
// - Normalises every failure into ApiError with a user-presentable message.

import type {
  AuthTokenData,
  CommentItem,
  CommonInterest,
  CurrentUser,
  EventAnalytics,
  EventDetail,
  EventDraft,
  EventItem,
  FeedItem,
  NetworkAnalytics,
  PersonSummary,
  PublicUser,
  Role,
} from "./types"

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

const TOKEN_KEY = "cc_token"

export class ApiError extends Error {
  status: number
  /** Field-level problems keyed by field name, for 422 responses. */
  fields: Record<string, string>

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.fields = fields
  }

  get isNetwork() {
    return this.status === 0
  }
}

// ---- token storage (every access guarded: storage can be blocked) ----------
export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token)
    else window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage unavailable: session lasts for this tab only */
  }
}

let unauthorizedHandler: (() => void) | null = null
export function onUnauthorized(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

// ---- core request ----------------------------------------------------------
type Method = "GET" | "POST" | "PATCH" | "DELETE"

interface Options {
  method?: Method
  body?: unknown
  query?: Record<string, string | number | boolean | null | undefined>
  /** Use an explicit token instead of the stored one (right after login). */
  token?: string | null
  signal?: AbortSignal
}

function describeValidation(detail: unknown): { message: string; fields: Record<string, string> } {
  const fields: Record<string, string> = {}
  if (Array.isArray(detail)) {
    for (const item of detail) {
      const loc: unknown[] = Array.isArray(item?.loc) ? item.loc : []
      const field = String(loc[loc.length - 1] ?? "")
      const msg = String(item?.msg ?? "Invalid value").replace(/^Value error, /, "")
      if (field && !fields[field]) fields[field] = msg
    }
  }
  const first = Object.entries(fields)[0]
  return {
    message: first ? `${first[0].replace(/_/g, " ")}: ${first[1]}` : "Please check the form and try again.",
    fields,
  }
}

export async function request<T>(path: string, opts: Options = {}): Promise<T> {
  const { method = "GET", body, query, signal } = opts
  const token = opts.token !== undefined ? opts.token : getToken()

  const url = new URL(API_URL + path)
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v))
    }
  }

  const headers: Record<string, string> = { Accept: "application/json" }
  if (body !== undefined) headers["Content-Type"] = "application/json"
  if (token) headers.Authorization = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (err) {
    if ((err as Error)?.name === "AbortError") throw err
    throw new ApiError(0, "Can't reach the CampusConnect server. Check your connection and try again.")
  }

  let payload: unknown = null
  try {
    payload = await res.json()
  } catch {
    /* empty or non-JSON body */
  }

  if (!res.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail
    if (res.status === 401) {
      if (token) unauthorizedHandler?.()
      throw new ApiError(401, "Your session has expired. Please sign in again.")
    }
    if (res.status === 422) {
      const { message, fields } = describeValidation(detail)
      throw new ApiError(422, message, fields)
    }
    if (res.status === 503) {
      throw new ApiError(503, "This feature is temporarily unavailable. Please try again shortly.")
    }
    if (res.status >= 500) {
      throw new ApiError(res.status, "Something went wrong on our side. Please try again.")
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : "The request could not be completed.")
  }

  return ((payload as { data?: T } | null)?.data ?? (payload as T)) as T
}

// ---- endpoints -------------------------------------------------------------
export const api = {
  // auth
  authConfig: () => request<{ dev_login_enabled: boolean }>("/api/auth/config", { token: null }),
  devLogin: (email: string, name: string) =>
    request<AuthTokenData>("/api/auth/dev-login", { method: "POST", body: { email, name }, token: null }),
  completeProfile: (
    body: { name: string; year: number; department: string; profile_picture?: string | null },
    token?: string | null,
  ) => request<AuthTokenData>("/api/auth/complete-profile", { method: "POST", body, token }),
  session: (token?: string | null) =>
    request<{
      user_id: string
      email: string
      name: string
      profile_picture: string | null
      role: Role
      profile_completed: boolean
    }>("/api/auth/session", { token }),
  googleLoginUrl: () => `${API_URL}/api/auth/google/login`,

  // current user
  me: (token?: string | null) => request<CurrentUser>("/api/users/me", { token }),
  updateMe: (body: Partial<{ name: string; year: number; department: string; profile_picture: string }>) =>
    request<CurrentUser>("/api/users/me", { method: "PATCH", body }),

  // people
  people: (q: { q?: string; department?: string; year?: number; page?: number; limit?: number }) =>
    request<PersonSummary[]>("/api/users", { query: q }),
  suggestions: (limit = 12) => request<PersonSummary[]>("/api/users/suggestions", { query: { limit } }),
  departments: () => request<string[]>("/api/users/departments"),
  user: (id: string) => request<PublicUser>(`/api/users/${id}`),
  followers: (id: string) => request<PersonSummary[]>(`/api/users/${id}/followers`),
  following: (id: string) => request<PersonSummary[]>(`/api/users/${id}/following`),

  // social
  follow: (id: string) => request(`/api/social/follow/${id}`, { method: "POST" }),
  unfollow: (id: string) => request(`/api/social/follow/${id}`, { method: "DELETE" }),
  followStatus: (id: string) =>
    request<{ target_user_id: string; is_following: boolean }>(`/api/social/status/${id}`),
  mutuals: (id: string) => request<PersonSummary[]>(`/api/social/mutuals/${id}`),
  commonInterests: (id: string) => request<CommonInterest[]>(`/api/social/common-interests/${id}`),

  // events
  categories: () => request<{ categories: string[] }>("/api/events/categories", { token: null }),
  events: (q: { search?: string; category?: string; upcoming_only?: boolean; page?: number; limit?: number }) =>
    request<EventItem[]>("/api/events", { query: q }),
  upcoming: (limit = 6) => request<EventItem[]>("/api/events/upcoming", { query: { limit } }),
  event: (id: string) => request<EventDetail>(`/api/events/${id}`),
  createEvent: (body: EventDraft) => request<EventItem>("/api/events", { method: "POST", body }),
  myHosted: () => request<EventItem[]>("/api/events/my-hosted"),
  myRegistered: () => request<EventItem[]>("/api/events/registered"),
  like: (id: string) => request(`/api/events/${id}/like`, { method: "POST" }),
  unlike: (id: string) => request(`/api/events/${id}/like`, { method: "DELETE" }),
  register: (id: string) => request(`/api/events/${id}/register`, { method: "POST" }),
  unregister: (id: string) => request(`/api/events/${id}/register`, { method: "DELETE" }),
  view: (id: string) => request(`/api/events/${id}/view`, { method: "POST" }),
  share: (id: string) => request(`/api/events/${id}/share`, { method: "POST" }),

  // comments
  comments: (id: string) => request<CommentItem[]>(`/api/events/${id}/comments`),
  addComment: (id: string, content: string) =>
    request<CommentItem>(`/api/events/${id}/comments`, { method: "POST", body: { content } }),
  deleteComment: (eventId: string, commentId: string) =>
    request(`/api/events/${eventId}/comments/${commentId}`, { method: "DELETE" }),

  // feed
  feed: (limit = 12) => request<FeedItem[]>("/api/feed", { query: { limit } }),

  // admin
  adminEvents: (status: "pending" | "approved" | "rejected") =>
    request<EventItem[]>("/api/admin/events", { query: { status } }),
  approve: (id: string) => request<EventItem>(`/api/admin/events/${id}/approve`, { method: "POST" }),
  reject: (id: string, reason?: string) =>
    request<EventItem>(`/api/admin/events/${id}/reject`, {
      method: "POST",
      body: { rejection_reason: reason?.trim() || null },
    }),
  eventAnalytics: () => request<EventAnalytics>("/api/admin/analytics/events"),
  networkAnalytics: () => request<NetworkAnalytics>("/api/admin/analytics/network"),
}
