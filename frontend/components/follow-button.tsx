"use client"

import { useEffect, useState } from "react"
import { UserCheck, UserPlus } from "lucide-react"

import { api } from "@/lib/api"
import { errorMessage } from "@/lib/use-async"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/toast"

/** Follow / unfollow with optimistic update and rollback. */
export function FollowButton({
  userId,
  name,
  initialFollowing,
  onChange,
  size = "default",
}: {
  userId: string
  /** Person's name, so the accessible name is e.g. "Follow Asha Raman". */
  name?: string
  initialFollowing: boolean
  onChange?: (following: boolean) => void
  size?: "default" | "sm" | "lg"
}) {
  const toast = useToast()
  const [following, setFollowing] = useState(initialFollowing)
  const [busy, setBusy] = useState(false)

  useEffect(() => setFollowing(initialFollowing), [initialFollowing, userId])

  const toggle = async () => {
    if (busy) return
    const next = !following
    setFollowing(next)
    setBusy(true)
    try {
      if (next) await api.follow(userId)
      else await api.unfollow(userId)
      onChange?.(next)
    } catch (err) {
      setFollowing(!next)
      toast.error(errorMessage(err, "Couldn't update follow status."))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Button
      size={size}
      variant={following ? "outline" : "default"}
      aria-label={name ? `${following ? "Following" : "Follow"} ${name}` : undefined}
      disabled={busy}
      onClick={() => void toggle()}
    >
      {following ? <UserCheck className="h-4 w-4" aria-hidden /> : <UserPlus className="h-4 w-4" aria-hidden />}
      {following ? "Following" : "Follow"}
    </Button>
  )
}
