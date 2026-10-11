"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

import { useAuth } from "@/lib/auth"
import { ErrorState, PageLoading } from "@/components/state-views"
import { ApiError } from "@/lib/api"

/** Routes reachable without a session. */
const PUBLIC_PATHS = ["/login", "/auth/callback"]
const isPublic = (path: string) => PUBLIC_PATHS.some((p) => path === p || path.startsWith(p + "/"))

/**
 * Central session routing:
 *   anonymous      -> /login (except public pages)
 *   needs-profile  -> /complete-profile (from every page, public ones included)
 *   ready          -> kept off /login and /complete-profile
 * Children render only once the session state allows the current page.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { status, signOut, refresh } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  const publicPage = isPublic(pathname)
  const onboarding = pathname === "/complete-profile"

  useEffect(() => {
    if (status === "anonymous" && !publicPage) router.replace("/login")
    else if (status === "needs-profile" && !onboarding) router.replace("/complete-profile")
    else if (status === "ready" && (pathname === "/login" || onboarding)) router.replace("/")
  }, [status, publicPage, onboarding, pathname, router])

  if (status === "loading") return <PageLoading label="Loading your session…" />

  if (status === "unavailable") {
    return (
      <div className="mx-auto max-w-lg py-16">
        <ErrorState
          title="Can't reach CampusConnect"
          error={new ApiError(0, "The server isn't responding. Check that the backend is running, then try again.")}
          onRetry={() => void refresh()}
        />
        <p className="mt-4 text-center text-sm">
          <button type="button" onClick={signOut} className="text-muted-foreground underline underline-offset-4">
            Sign out
          </button>
        </p>
      </div>
    )
  }

  // Avoid flashing protected content while a redirect is in flight.
  if (status === "anonymous" && !publicPage) return <PageLoading label="Redirecting to sign in…" />
  if (status === "needs-profile" && !onboarding) return <PageLoading />
  if (status === "ready" && (pathname === "/login" || onboarding)) return <PageLoading />

  return <>{children}</>
}
