"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "./api"
import { errorMessage } from "./use-async"
import type { EventItem } from "./types"
import { useToast } from "@/components/toast"

interface State {
  liked: boolean
  likeCount: number
  registered: boolean
  registrationCount: number
}

function fromEvent(e: Pick<EventItem, "is_liked_by_me" | "like_count" | "is_registered_by_me" | "registration_count">): State {
  return {
    liked: e.is_liked_by_me,
    likeCount: e.like_count,
    registered: e.is_registered_by_me,
    registrationCount: e.registration_count,
  }
}

/**
 * Optimistic like / register toggles. The UI updates immediately and rolls
 * back (with a toast) if the server rejects or is unreachable, so the visible
 * state never claims something the backend didn't record.
 */
export function useEventInteractions(
  event: Pick<
    EventItem,
    "event_id" | "is_liked_by_me" | "like_count" | "is_registered_by_me" | "registration_count"
  >,
) {
  const toast = useToast()
  const [state, setState] = useState<State>(() => fromEvent(event))
  const [busy, setBusy] = useState<"like" | "register" | null>(null)

  // Re-sync when the parent reloads fresh data for this event.
  useEffect(() => {
    setState(fromEvent(event))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event.event_id, event.is_liked_by_me, event.like_count, event.is_registered_by_me, event.registration_count])

  const toggleLike = useCallback(async () => {
    if (busy) return
    const previous = state
    const next = !previous.liked
    setState({ ...previous, liked: next, likeCount: Math.max(0, previous.likeCount + (next ? 1 : -1)) })
    setBusy("like")
    try {
      if (next) await api.like(event.event_id)
      else await api.unlike(event.event_id)
    } catch (err) {
      setState(previous)
      toast.error(errorMessage(err, "Couldn't update your like."))
    } finally {
      setBusy(null)
    }
  }, [busy, state, event.event_id, toast])

  const toggleRegister = useCallback(async () => {
    if (busy) return
    const previous = state
    const next = !previous.registered
    setState({
      ...previous,
      registered: next,
      registrationCount: Math.max(0, previous.registrationCount + (next ? 1 : -1)),
    })
    setBusy("register")
    try {
      if (next) {
        await api.register(event.event_id)
        toast.success("You're registered. See it under My Events.")
      } else {
        await api.unregister(event.event_id)
        toast.success("Registration cancelled.")
      }
    } catch (err) {
      setState(previous)
      toast.error(errorMessage(err, "Couldn't update your registration."))
    } finally {
      setBusy(null)
    }
  }, [busy, state, event.event_id, toast])

  return { ...state, busy, toggleLike, toggleRegister }
}
