"use client"

import { useState } from "react"
import Link from "next/link"
import { BarChart3, CalendarCheck, CalendarClock, CalendarX, Check, ShieldAlert, X } from "lucide-react"

import { api } from "@/lib/api"
import { useCurrentUser } from "@/lib/auth"
import { errorMessage, useAsync } from "@/lib/use-async"
import { formatDate, formatTimeRange } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { EventItem } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { PageHeader } from "@/components/page-header"
import { RankedBars } from "@/components/ranked-bars"
import { StatCard } from "@/components/stat-card"
import { StatusBadge } from "@/components/status-badge"
import { EmptyState, ErrorState, ListSkeleton, Spinner } from "@/components/state-views"
import { useToast } from "@/components/toast"
import { LinkButton } from "@/components/link-button"

type Tab = "queue" | "history" | "analytics"

function ReviewRow({
  event,
  onApprove,
  onReject,
  busy,
}: {
  event: EventItem
  onApprove: () => void
  onReject: () => void
  busy: boolean
}) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{event.category}</Badge>
            <span className="text-sm text-muted-foreground">
              by{" "}
              <Link href={`/people/${event.host_id}`} className="font-medium text-foreground hover:underline">
                {event.host_name ?? "Unknown host"}
              </Link>
            </span>
          </div>
          <h3 className="text-lg font-semibold leading-snug">
            <Link href={`/events/${event.event_id}`} className="hover:underline">
              {event.title}
            </Link>
          </h3>
          <p className="line-clamp-3 whitespace-pre-wrap text-sm text-muted-foreground">{event.description}</p>
          <p className="text-sm text-muted-foreground">
            {formatDate(event.date)} · {formatTimeRange(event.start_time, event.end_time)} · {event.venue}
          </p>
          {event.registration_url ? (
            <p className="truncate text-xs text-muted-foreground">
              Link:{" "}
              <a
                href={event.registration_url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline underline-offset-2"
              >
                {event.registration_url}
              </a>
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 gap-2">
          <Button variant="outline" size="lg" className="h-9" disabled={busy} onClick={onReject}>
            <X className="h-4 w-4" aria-hidden /> Reject
          </Button>
          <Button size="lg" className="h-9" disabled={busy} onClick={onApprove}>
            {busy ? <Spinner /> : <Check className="h-4 w-4" aria-hidden />} Approve
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Queue() {
  const toast = useToast()
  const pending = useAsync(() => api.adminEvents("pending"), [])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [rejecting, setRejecting] = useState<EventItem | null>(null)
  const [reason, setReason] = useState("")

  const removeFromQueue = (id: string) =>
    pending.setData((prev) => (prev ?? []).filter((e) => e.event_id !== id))

  const approve = async (event: EventItem) => {
    setBusyId(event.event_id)
    try {
      await api.approve(event.event_id)
      removeFromQueue(event.event_id)
      toast.success(`Approved “${event.title}”.`)
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't approve this event."))
      // A 409 means someone else already moderated it: refresh the queue.
      pending.reload()
    } finally {
      setBusyId(null)
    }
  }

  const confirmReject = async () => {
    if (!rejecting) return
    const event = rejecting
    setBusyId(event.event_id)
    try {
      await api.reject(event.event_id, reason)
      removeFromQueue(event.event_id)
      toast.success(`Rejected “${event.title}”.`)
      setRejecting(null)
      setReason("")
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't reject this event."))
      pending.reload()
    } finally {
      setBusyId(null)
    }
  }

  if (pending.loading) return <ListSkeleton rows={3} />
  if (pending.error) return <ErrorState error={pending.error} onRetry={pending.reload} />

  return (
    <>
      {(pending.data ?? []).length === 0 ? (
        <EmptyState
          icon={CalendarCheck}
          title="The queue is clear"
          description="New event submissions waiting for review will appear here."
        />
      ) : (
        <div className="space-y-4">
          {(pending.data ?? []).map((e) => (
            <ReviewRow
              key={e.event_id}
              event={e}
              busy={busyId === e.event_id}
              onApprove={() => void approve(e)}
              onReject={() => {
                setReason("")
                setRejecting(e)
              }}
            />
          ))}
        </div>
      )}

      <Dialog open={rejecting !== null} onOpenChange={(open) => !open && setRejecting(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject this event?</DialogTitle>
            <DialogDescription>
              “{rejecting?.title}” will not be published. The host will see your reason on their submission.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="reason">Reason (optional)</Label>
            <Textarea
              id="reason"
              rows={3}
              maxLength={500}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Duplicate of an existing event"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejecting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={busyId !== null}
              onClick={() => void confirmReject()}
            >
              {busyId ? <Spinner /> : null} Reject event
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function History() {
  const [filter, setFilter] = useState<"approved" | "rejected">("approved")
  const events = useAsync(() => api.adminEvents(filter), [filter])

  return (
    <div className="space-y-4">
      <div className="inline-flex rounded-lg bg-muted p-1" role="group" aria-label="Status filter">
        {(["approved", "rejected"] as const).map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={filter === s}
            onClick={() => setFilter(s)}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium capitalize transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              filter === s ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {events.loading ? (
        <ListSkeleton rows={3} />
      ) : events.error ? (
        <ErrorState error={events.error} onRetry={events.reload} />
      ) : (events.data ?? []).length === 0 ? (
        <EmptyState icon={CalendarX} title={`No ${filter} events`} />
      ) : (
        <ul className="space-y-3">
          {(events.data ?? []).map((e) => (
            <li key={e.event_id}>
              <Link
                href={`/events/${e.event_id}`}
                className="flex flex-col gap-2 rounded-xl border bg-card p-4 transition-colors hover:bg-accent/50 sm:flex-row sm:items-center sm:justify-between"
              >
                <span className="min-w-0">
                  <span className="block truncate font-medium">{e.title}</span>
                  <span className="block truncate text-sm text-muted-foreground">
                    {e.host_name ?? "Unknown host"} · {formatDate(e.date)}
                    {e.rejection_reason ? ` · “${e.rejection_reason}”` : ""}
                  </span>
                </span>
                <StatusBadge status={e.status} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Analytics() {
  const events = useAsync(() => api.eventAnalytics(), [])
  const network = useAsync(() => api.networkAnalytics(), [])

  return (
    <div className="space-y-8">
      <section aria-labelledby="ev-analytics">
        <h2 id="ev-analytics" className="mb-1 text-lg font-semibold">
          Events
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">Computed with MongoDB aggregation pipelines.</p>
        {events.loading ? (
          <ListSkeleton rows={2} />
        ) : events.error ? (
          <ErrorState error={events.error} onRetry={events.reload} />
        ) : events.data ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StatCard label="Total submitted" value={events.data.total_events} icon={BarChart3} />
              <StatCard label="Approved" value={events.data.approved_events} icon={CalendarCheck} />
              <StatCard label="Pending review" value={events.data.pending_events} icon={CalendarClock} />
              <StatCard label="Rejected" value={events.data.rejected_events} icon={CalendarX} />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Approved events by category</CardTitle>
                  <CardDescription>Number of public events per category.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RankedBars
                    unit="event"
                    emptyLabel="No approved events yet."
                    items={Object.entries(events.data.by_category).map(([label, value]) => ({
                      id: label,
                      label,
                      value,
                    }))}
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Most active hosts</CardTitle>
                  <CardDescription>Events submitted, all statuses.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RankedBars
                    unit="event"
                    emptyLabel="No submissions yet."
                    items={events.data.events_by_host.map((h) => ({
                      id: h.host_id,
                      label: h.host_name,
                      value: h.total_submitted,
                      href: `/people/${h.host_id}`,
                    }))}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="net-analytics">
        <h2 id="net-analytics" className="mb-1 text-lg font-semibold">
          Network
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">Computed from the Neo4j social graph.</p>
        {network.loading ? (
          <ListSkeleton rows={2} />
        ) : network.error ? (
          <ErrorState
            error={network.error}
            onRetry={network.reload}
            title="Network analytics unavailable"
          />
        ) : network.data ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="Users in graph" value={network.data.total_users} icon={BarChart3} />
              <StatCard label="Follow connections" value={network.data.total_follows} icon={BarChart3} />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Most followed students</CardTitle>
                  <CardDescription>Top 5 by follower count.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RankedBars
                    unit="follower"
                    emptyLabel="Nobody has been followed yet."
                    items={network.data.most_followed_users.map((u) => ({
                      id: u.user_id,
                      label: u.name,
                      value: u.follower_count,
                      href: `/people/${u.user_id}`,
                    }))}
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Most engaged events</CardTitle>
                  <CardDescription>Likes, registrations, shares and views combined.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RankedBars
                    unit="interaction"
                    emptyLabel="No interactions recorded yet."
                    items={network.data.most_interacted_events.map((e) => ({
                      id: e.event_id,
                      label: e.title,
                      value: e.interaction_count,
                      href: `/events/${e.event_id}`,
                    }))}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  )
}

export default function AdminPage() {
  const me = useCurrentUser()
  const [tab, setTab] = useState<Tab>("queue")

  if (me.role !== "ADMIN") {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="Administrators only"
        description="You don't have permission to view the admin console."
        action={
          <LinkButton href="/">
            Back home
          </LinkButton>
        }
      />
    )
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "queue", label: "Review queue" },
    { id: "history", label: "History" },
    { id: "analytics", label: "Analytics" },
  ]

  return (
    <div>
      <PageHeader title="Admin console" description="Moderate event submissions and monitor activity." />

      <div role="tablist" aria-label="Admin sections" className="mb-6 inline-flex rounded-lg bg-muted p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              tab === t.id ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "queue" ? <Queue /> : tab === "history" ? <History /> : <Analytics />}
      </div>
    </div>
  )
}
