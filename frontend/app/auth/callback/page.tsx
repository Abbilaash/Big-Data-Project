"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/lib/auth"
import { PageLoading } from "@/components/state-views"
import { Button } from "@/components/ui/button"
import { LinkButton } from "@/components/link-button"

/**
 * Landing page for the Google OAuth redirect. The backend places the session
 * token in the URL *fragment* (never sent to servers or logged). We read it
 * once, remove it from the address bar, then hand it to the auth context.
 */
export default function AuthCallbackPage() {
  const router = useRouter()
  const { signIn } = useAuth()
  const started = useRef(false)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (started.current) return // React strict mode double-invokes effects
    started.current = true

    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""))
    const token = params.get("token")
    window.history.replaceState(null, "", window.location.pathname)

    if (!token) {
      setFailed(true)
      return
    }
    void signIn(token).then((status) => {
      if (status === "ready") router.replace("/")
      else if (status === "needs-profile") router.replace("/complete-profile")
      else setFailed(true)
    })
  }, [router, signIn])

  if (failed) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <h1 className="text-xl font-semibold">Sign-in didn&apos;t complete</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          We couldn&apos;t finish signing you in. Please try again.
        </p>
        <LinkButton className="mt-6" size="lg" href="/login">
          Back to sign in
        </LinkButton>
      </div>
    )
  }
  return <PageLoading label="Signing you in…" />
}
