"use client"

import { useEffect, useState } from "react"

import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { errorMessage } from "@/lib/use-async"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LinkButton } from "@/components/link-button"
import { Spinner } from "@/components/state-views"

function GoogleMark() {
  return (
    <svg viewBox="0 0 48 48" className="h-4 w-4" aria-hidden>
      <path
        fill="#EA4335"
        d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.5 17.7 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 7.1-10.1 7.1-17.5z"
      />
      <path
        fill="#FBBC05"
        d="M10.5 28.7a14.5 14.5 0 0 1 0-9.4l-7.9-6.1a24 24 0 0 0 0 21.6l7.9-6.1z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.5-5.8c-2.1 1.4-4.9 2.3-8.4 2.3-6.3 0-11.6-4-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z"
      />
    </svg>
  )
}

export function SignInCard() {
  const { signIn } = useAuth()
  const [notice, setNotice] = useState<string | null>(null)
  const [devEnabled, setDevEnabled] = useState(false)
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  // The backend reports OAuth failures in the URL fragment.
  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""))
    const err = params.get("error")
    if (err) {
      setNotice(err)
      window.history.replaceState(null, "", window.location.pathname)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .authConfig()
      .then((cfg) => !cancelled && setDevEnabled(cfg.dev_login_enabled))
      .catch(() => {
        /* backend unreachable: the Google link is still shown */
      })
    return () => {
      cancelled = true
    }
  }, [])

  const onDevLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setBusy(true)
    try {
      const result = await api.devLogin(email.trim(), name.trim())
      await signIn(result.access_token)
    } catch (err) {
      setFormError(
        err instanceof ApiError && err.status === 404
          ? "Developer sign-in is not enabled on the server."
          : errorMessage(err),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <section id="signin" className="rounded-lg border bg-card p-6 sm:p-8">
      <h2 className="text-xl font-semibold">Sign in</h2>
      <p className="mt-1 text-sm text-muted-foreground">Use your Google account to continue.</p>

      {notice ? (
        <p role="alert" className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
          {notice}
        </p>
      ) : null}

      <LinkButton
        size="lg"
        variant="outline"
        className="mt-6 h-10 w-full text-sm"
        href={api.googleLoginUrl()}
        external
      >
        <GoogleMark /> Continue with Google
      </LinkButton>

      {devEnabled ? (
        <form onSubmit={onDevLogin} className="mt-8 space-y-4 border-t pt-6">
          <div>
            <h3 className="text-sm font-semibold">Developer sign-in</h3>
            <p className="text-xs text-muted-foreground">
              Enabled by <code className="font-mono">ENABLE_DEV_LOGIN</code> on this server. Never available in
              production. Use the configured <code className="font-mono">ADMIN_EMAIL</code> to get admin access.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dev-email">Email</Label>
            <Input
              id="dev-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dev-name">Name</Label>
            <Input
              id="dev-name"
              required
              maxLength={100}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
            />
          </div>
          {formError ? (
            <p role="alert" className="text-sm text-destructive">
              {formError}
            </p>
          ) : null}
          <Button type="submit" size="lg" className="h-10 w-full text-sm" disabled={busy}>
            {busy ? <Spinner /> : null} Sign in (development)
          </Button>
        </form>
      ) : null}
    </section>
  )
}
