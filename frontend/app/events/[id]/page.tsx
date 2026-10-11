"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import {
  ArrowLeft,
  CalendarDays,
  Clock,
  ExternalLink,
  Eye,
  Heart,
  MapPin,
  Share2,
  Trash2,
  Users,
} from "lucide-react"

import { api } from "@/lib/api"
import { useCurrentUser } from "@/lib/auth"
import { errorMessage, useAsync } from "@/lib/use-async"
import { formatDate, formatRelative, formatTimeRange, isPast, pluralize } from "@/lib/format"
import { useEventInteractions } from "@/lib/use-event-interactions"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { EventPoster } from "@/components/event-card"
import { StatusBadge } from "@/components/status-badge"
import { UserAvatar } from "@/components/user-avatar"
import { useToast } from "@/components/toast"
import { EmptyState, ErrorState, ListSkeleton, PageLoading, Spinner } from "@/components/state-views"
import type { EventDetail } from "@/lib/types"
import { LinkButton } from "@/components/link-button"

function Comments({ eventId, canComment }: { eventId: string; canComment: boolean }) {
  const me = useCurrentUser()
  const toast = useToast()
  const comments = useAsync(() => api.comments(eventId), [eventId])
  const [text, setText] = useState("")
  const [posting, setPosting] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const content = text.trim()
    if (!content) return
    setPosting(true)
    try {
      const created = await api.addComment(eventId, content)
      comments.setData((prev) => [...(prev ?? []), created])
      setText("")
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't post your comment."))
    } finally {
      setPosting(false)
    }
  }

  const remove = async (commentId: string) => {
    try {
      await api.deleteComment(eventId, commentId)
      comments.setData((prev) => (prev ?? []).filter((c) => c.comment_id !== commentId))
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't delete the comment."))
    }
  }

  return (
    <section aria-labelledby="comments-heading">
      <h2 id="comments-heading" className="mb-4 text-xl font-semibold tracking-tight">
        Discussion {comments.data ? <span className="text-muted-foreground">({comments.data.length})</span> : null}
      </h2>

      {canComment ? (
        <form onSubmit={submit} className="mb-6 space-y-2">
          <Label htmlFor="comment" className="sr-only">
            Add a comment
          </Label>
          <Textarea
            id="comment"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={1000}
            rows={3}
            placeholder="Ask a question or share your thoughts…"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">{text.length}/1000</span>
            <Button type="submit" size="lg" disabled={posting || !text.trim()}>
              {posting ? <Spinner /> : null} Post comment
            </Button>
          </div>
        </form>
      ) : null}

      {comments.loading ? (
        <ListSkeleton rows={2} />
      ) : comments.error ? (
        <ErrorState error={comments.error} onRetry={comments.reload} title="Couldn't load comments" />
      ) : (comments.data ?? []).length === 0 ? (
        <EmptyState title="No comments yet" description="Start the conversation." />
      ) : (
        <ul className="space-y-4">
          {(comments.data ?? []).map((c) => (
            <li key={c.comment_id} className="flex gap-3">
              <Link href={c.user_id === me.user_id ? "/profile" : `/people/${c.user_id}`}>
                <UserAvatar name={c.user_name ?? "?"} src={c.user_picture} />
              </Link>
              <div className="min-w-0 flex-1 rounded-xl bg-muted/50 px-4 py-3">
                <div className="flex flex-wrap items-center gap-x-2">
                  <span className="text-sm font-medium">{c.user_name ?? "Unknown user"}</span>
                  <span className="text-xs text-muted-foreground">{formatRelative(c.created_at)}</span>
                  {c.user_id === me.user_id || me.role === "ADMIN" ? (
                    <button
                      type="button"
                      onClick={() => void remove(c.comment_id)}
                      className="ml-auto rounded p-1 text-muted-foreground hover:text-destructive focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label="Delete comment"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  ) : null}
                </div>
                <p className="mt-1 whitespace-pre-wrap break-words text-sm">{c.content}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function EventBody({ event }: { event: EventDetail }) {
  const me = useCurrentUser()
  const toast = useToast()
  const ix = useEventInteractions(event)
  const [shares, setShares] = useState(event.share_count)
  const approved = event.status === "approved"
  const past = isPast(event.date)
  const isHost = event.host_id === me.user_id

  const share = async () => {
    const url = window.location.href
    try {
      if (navigator.share) {
        await navigator.share({ title: event.title, url })
      } else {
        await navigator.clipboard.writeText(url)
        toast.success("Link copied to clipboard.")
      }
    } catch (err) {
      if ((err as Error)?.name === "AbortError") return // user closed the share sheet
      toast.error("Couldn't copy the link. You can copy it from the address bar.")
      return
    }
    try {
      await api.share(event.event_id)
      setShares((n) => n + 1)
    } catch {
      /* the share itself worked; recording it is best-effort */
    }
  }

  return (
    <article className="space-y-8">
      <div className="overflow-hidden rounded-2xl border bg-card">
        <EventPoster event={event} className="aspect-[16/5]" />
        <div className="space-y-4 p-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{event.category}</Badge>
            {past ? <Badge variant="outline">Past event</Badge> : null}
            {!approved ? <StatusBadge status={event.status} /> : null}
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{event.title}</h1>
          <p className="text-sm text-muted-foreground">
            Hosted by{" "}
            {isHost ? (
              <Link href="/profile" className="font-medium text-foreground hover:underline">
                you
              </Link>
            ) : (
              <Link href={`/people/${event.host_id}`} className="font-medium text-foreground hover:underline">
                {event.host_name ?? "Unknown host"}
              </Link>
            )}
          </p>

          {!approved ? (
            <p
              role="status"
              className={cn(
                "rounded-lg border px-4 py-3 text-sm",
                event.status === "rejected"
                  ? "border-red-200 bg-red-50 text-red-900 dark:border-red-400/30 dark:bg-red-400/10 dark:text-red-200"
                  : "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200",
              )}
            >
              {event.status === "pending"
                ? "This event is waiting for an administrator's review. Only you and admins can see it."
                : `This event was not approved.${event.rejection_reason ? ` Reason: ${event.rejection_reason}` : ""}`}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-2 pt-2">
            <Button
              size="lg"
              className="h-10 px-5 text-sm"
              variant={ix.registered ? "secondary" : "default"}
              disabled={!approved || past || ix.busy === "register"}
              aria-pressed={ix.registered}
              onClick={() => void ix.toggleRegister()}
            >
              {ix.registered ? "Registered ✓ (click to cancel)" : past ? "Event ended" : "Register"}
            </Button>
            <Button
              size="lg"
              variant="outline"
              className={cn("h-10 gap-1.5 px-4 text-sm", ix.liked && "border-rose-200 bg-rose-50 text-rose-600 dark:border-rose-400/30 dark:bg-rose-400/10 dark:text-rose-300")}
              disabled={!approved || ix.busy === "like"}
              aria-pressed={ix.liked}
              onClick={() => void ix.toggleLike()}
            >
              <Heart className={cn("h-4 w-4", ix.liked && "fill-current")} aria-hidden />
              {ix.liked ? "Liked" : "Like"} · {ix.likeCount}
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="h-10 gap-1.5 px-4 text-sm"
              disabled={!approved}
              onClick={() => void share()}
            >
              <Share2 className="h-4 w-4" aria-hidden /> Share
            </Button>
            {event.registration_url ? (
              <LinkButton
                size="lg"
                variant="ghost"
                className="h-10 gap-1.5 px-4 text-sm"
                href={event.registration_url}
                external
                newTab
              >
                Official page <ExternalLink className="h-4 w-4" aria-hidden />
              </LinkButton>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>About this event</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{event.description}</p>
            {event.tags.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {event.tags.map((t) => (
                  <Badge key={t} variant="outline">
                    #{t}
                  </Badge>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Details</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4 text-sm">
              <div className="flex gap-3">
                <CalendarDays className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                <div>
                  <dt className="sr-only">Date</dt>
                  <dd>{formatDate(event.date)}</dd>
                </div>
              </div>
              <div className="flex gap-3">
                <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                <div>
                  <dt className="sr-only">Time</dt>
                  <dd>{formatTimeRange(event.start_time, event.end_time)}</dd>
                </div>
              </div>
              <div className="flex gap-3">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                <div>
                  <dt className="sr-only">Venue</dt>
                  <dd>{event.venue}</dd>
                </div>
              </div>
              <div className="flex gap-3">
                <Users className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                <div>
                  <dt className="sr-only">Registrations</dt>
                  <dd>{pluralize(ix.registrationCount, "registration")}</dd>
                </div>
              </div>
              <div className="flex gap-3">
                <Eye className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                <div>
                  <dt className="sr-only">Reach</dt>
                  <dd>
                    {pluralize(event.view_count, "viewer")} · {pluralize(shares, "share")}
                  </dd>
                </div>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {approved ? <Comments eventId={event.event_id} canComment /> : null}
    </article>
  )
}

export default function EventDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params.id
  const event = useAsync(() => api.event(id), [id])
  const viewed = useRef<string | null>(null)

  // Record one view per visit once we know the event is public.
  useEffect(() => {
    if (event.data?.status === "approved" && viewed.current !== event.data.event_id) {
      viewed.current = event.data.event_id
      api.view(event.data.event_id).catch(() => undefined)
    }
  }, [event.data])

  return (
    <div>
      <Link
        href="/events"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> All events
      </Link>

      {event.loading ? (
        <PageLoading label="Loading event…" />
      ) : event.error ? (
        event.error.status === 404 ? (
          <EmptyState
            title="Event not found"
            description="It may have been removed, or it isn't public yet."
            action={
              <LinkButton href="/events">
                Browse events
              </LinkButton>
            }
          />
        ) : (
          <ErrorState error={event.error} onRetry={event.reload} title="Couldn't load this event" />
        )
      ) : event.data ? (
        <EventBody event={event.data} />
      ) : null}
    </div>
  )
}
