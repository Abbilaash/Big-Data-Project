"use client"

import Link from "next/link"
import { CalendarDays, Heart, MapPin, Users, UserRoundCheck } from "lucide-react"

import type { EventItem } from "@/lib/types"
import { formatShortDate, formatTimeRange, isPast, pluralize } from "@/lib/format"
import { useEventInteractions } from "@/lib/use-event-interactions"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { StatusBadge } from "@/components/status-badge"
import { LinkButton } from "@/components/link-button"

export function EventPoster({ event, className }: { event: EventItem; className?: string }) {
  const { day, month } = formatShortDate(event.date)
  return (
    <div
      className={cn(
        "poster-grid relative overflow-hidden bg-muted",
        // Without a poster, a slim banner (date chip only) avoids a large empty block.
        event.poster_url ? (className ?? "aspect-[16/7]") : "h-16",
      )}
    >
      {event.poster_url ? (
        // External, user-supplied URL: plain <img> with no referrer; hidden if it fails to load.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={event.poster_url}
          alt=""
          referrerPolicy="no-referrer"
          loading="lazy"
          className="h-full w-full object-cover"
          onError={(e) => {
            e.currentTarget.style.display = "none"
          }}
        />
      ) : null}
      <div className="absolute left-3 top-3 flex flex-col items-center rounded-lg bg-background/95 px-2.5 py-1 text-center shadow-sm ring-1 ring-border">
        <span className="text-[10px] font-semibold leading-tight tracking-wide text-primary">{month}</span>
        <span className="text-lg font-bold leading-tight">{day}</span>
      </div>
    </div>
  )
}

export function EventCard({
  event,
  reason,
  showStatus = false,
}: {
  event: EventItem
  /** Social explanation from the feed, e.g. "Priya registered for this event". */
  reason?: string | null
  showStatus?: boolean
}) {
  const ix = useEventInteractions(event)
  const approved = event.status === "approved"
  const past = isPast(event.date)

  return (
    <Card className="flex h-full flex-col overflow-hidden pt-0">
      <EventPoster event={event} />

      <CardContent className="flex flex-1 flex-col gap-3 pt-4">
        {reason ? (
          <p className="flex items-start gap-1.5 rounded-md bg-primary/5 px-2.5 py-1.5 text-xs font-medium leading-snug text-primary">
            <UserRoundCheck className="mt-px h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="min-w-0">{reason}</span>
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="secondary">{event.category}</Badge>
          {past ? <Badge variant="outline">Past event</Badge> : null}
          {showStatus ? <StatusBadge status={event.status} /> : null}
        </div>

        <h3 className="text-lg font-semibold leading-snug">
          <Link
            href={`/events/${event.event_id}`}
            className="rounded-sm hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {event.title}
          </Link>
        </h3>
        <p className="line-clamp-2 text-sm text-muted-foreground">{event.description}</p>

        <ul className="mt-auto space-y-1.5 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 shrink-0" aria-hidden />
            {formatTimeRange(event.start_time, event.end_time)}
          </li>
          <li className="flex items-center gap-2">
            <MapPin className="h-4 w-4 shrink-0" aria-hidden />
            <span className="truncate">{event.venue}</span>
          </li>
          <li className="flex items-center gap-2">
            <Users className="h-4 w-4 shrink-0" aria-hidden />
            {pluralize(ix.registrationCount, "registration")}
            {event.host_name ? <span className="truncate">· by {event.host_name}</span> : null}
          </li>
        </ul>

        {event.status === "rejected" && event.rejection_reason ? (
          <p className="rounded-md bg-red-50 px-2.5 py-1.5 text-xs text-red-800 dark:bg-red-400/10 dark:text-red-300">
            Reason: {event.rejection_reason}
          </p>
        ) : null}
      </CardContent>

      <CardFooter className="gap-2">
        <Button
          variant="outline"
          size="icon-lg"
          aria-pressed={ix.liked}
          aria-label={ix.liked ? `Unlike (${ix.likeCount} likes)` : `Like (${ix.likeCount} likes)`}
          disabled={!approved || ix.busy === "like"}
          onClick={() => void ix.toggleLike()}
          className={cn("w-auto gap-1 px-2.5", ix.liked && "border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100 dark:border-rose-400/30 dark:bg-rose-400/10 dark:text-rose-300 dark:hover:bg-rose-400/20")}
        >
          <Heart className={cn("h-4 w-4", ix.liked && "fill-current")} aria-hidden />
          <span className="text-sm tabular-nums">{ix.likeCount}</span>
        </Button>
        <Button
          size="lg"
          className="flex-1"
          variant={ix.registered ? "secondary" : "default"}
          disabled={!approved || past || ix.busy === "register"}
          aria-pressed={ix.registered}
          onClick={() => void ix.toggleRegister()}
        >
          {ix.registered ? "Registered ✓" : past ? "Event ended" : "Register"}
        </Button>
        <LinkButton variant="outline" size="lg" href={`/events/${event.event_id}`}>
          Details
        </LinkButton>
      </CardFooter>
    </Card>
  )
}
