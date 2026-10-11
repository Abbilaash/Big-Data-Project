"use client"

import { Suspense } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { CalendarCheck, ClipboardList, Plus } from "lucide-react"

import { api } from "@/lib/api"
import { useAsync } from "@/lib/use-async"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { EventCard } from "@/components/event-card"
import { PageHeader } from "@/components/page-header"
import { CardGridSkeleton, EmptyState, ErrorState, PageLoading } from "@/components/state-views"
import { LinkButton } from "@/components/link-button"

type Tab = "registered" | "hosted"

function MyEvents() {
  const router = useRouter()
  const search = useSearchParams()
  const tab: Tab = search.get("tab") === "hosted" ? "hosted" : "registered"

  const registered = useAsync(() => api.myRegistered(), [])
  const hosted = useAsync(() => api.myHosted(), [])
  const current = tab === "registered" ? registered : hosted

  const tabs: { id: Tab; label: string; count: number | null }[] = [
    { id: "registered", label: "Registered", count: registered.data?.length ?? null },
    { id: "hosted", label: "Submitted by me", count: hosted.data?.length ?? null },
  ]

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader title="My Events" description="Events you're attending and events you've submitted." />
        <LinkButton size="lg" className="h-10 px-4 text-sm" href="/events/new">
          <Plus className="h-4 w-4" aria-hidden /> Host an event
        </LinkButton>
      </div>

      <div role="tablist" aria-label="My events" className="mb-6 inline-flex rounded-lg bg-muted p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => router.replace(`/my-events?tab=${t.id}`)}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              tab === t.id ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
            {t.count !== null ? <span className="ml-1.5 text-muted-foreground">{t.count}</span> : null}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {current.loading ? (
          <CardGridSkeleton count={3} />
        ) : current.error ? (
          <ErrorState error={current.error} onRetry={current.reload} />
        ) : (current.data ?? []).length === 0 ? (
          tab === "registered" ? (
            <EmptyState
              icon={CalendarCheck}
              title="No registrations yet"
              description="Find something interesting and hit Register."
              action={
                <LinkButton href="/events">
                  Browse events
                </LinkButton>
              }
            />
          ) : (
            <EmptyState
              icon={ClipboardList}
              title="You haven't submitted any events"
              description="Host an event and it will show up here with its review status."
              action={
                <LinkButton href="/events/new">
                  Host an event
                </LinkButton>
              }
            />
          )
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(current.data ?? []).map((event) => (
              <EventCard key={event.event_id} event={event} showStatus={tab === "hosted"} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function MyEventsPage() {
  // useSearchParams requires a Suspense boundary for static prerendering.
  return (
    <Suspense fallback={<PageLoading />}>
      <MyEvents />
    </Suspense>
  )
}
