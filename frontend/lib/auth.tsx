"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

import { api, ApiError, getToken, onUnauthorized, setToken } from "./api"
import type { CurrentUser } from "./types"

type Status = "loading" | "anonymous" | "needs-profile" | "ready" | "unavailable"

interface AuthContextValue {
  status: Status
  user: CurrentUser | null
  /** Store a freshly issued token and (re)load the session. */
  signIn: (token: string) => Promise<Status>
  signOut: () => void
  /** Re-read the profile, e.g. after the user edits it. */
  refresh: () => Promise<void>
  setUser: (user: CurrentUser) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading")
  const [user, setUser] = useState<CurrentUser | null>(null)

  const load = useCallback(async (): Promise<Status> => {
    const token = getToken()
    if (!token) {
      setUser(null)
      setStatus("anonymous")
      return "anonymous"
    }
    try {
      const me = await api.me(token)
      setUser(me)
      setStatus("ready")
      return "ready"
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 403) {
          // Signed in but onboarding is unfinished.
          setUser(null)
          setStatus("needs-profile")
          return "needs-profile"
        }
        if (err.status === 401 || err.status === 404) {
          setToken(null)
          setUser(null)
          setStatus("anonymous")
          return "anonymous"
        }
      }
      setStatus("unavailable")
      return "unavailable"
    }
  }, [])

  const signOut = useCallback(() => {
    setToken(null)
    setUser(null)
    setStatus("anonymous")
  }, [])

  const signIn = useCallback(
    async (token: string) => {
      setToken(token)
      setStatus("loading")
      return load()
    },
    [load],
  )

  useEffect(() => {
    void load()
  }, [load])

  // Any 401 from the API (expired/revoked token) ends the session everywhere.
  useEffect(() => {
    onUnauthorized(signOut)
    return () => onUnauthorized(null)
  }, [signOut])

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      signIn,
      signOut,
      refresh: async () => {
        await load()
      },
      setUser,
    }),
    [status, user, signIn, signOut, load],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>")
  return ctx
}

/** For pages rendered only when signed in (guaranteed by <AuthGate>). */
export function useCurrentUser(): CurrentUser {
  const { user } = useAuth()
  if (!user) throw new Error("useCurrentUser used without an authenticated user")
  return user
}
