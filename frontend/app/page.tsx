"use client"

import Link from "next/link"
import { CalendarCheck, ClipboardList, Plus, UserPlus, Users } from "lucide-react"

import { api } from "@/lib/api"
import { useCurrentUser } from "@/lib/auth"
import { useAsync } from "@/lib/use-async"
import { formatDate } from "@/lib/format"
import { Button } from "@/components/ui/button"
import { EventCard } from "@/components/event-card"
import { PersonCard } from "@/components/person-card"
import { StatCard } from "@/components/stat-card"
import { CardGridSkeleton, EmptyState, ErrorState, ListSkeleton } from "@/components/state-views"
import { LinkButton } from "@/components/link-button"

function SectionHeading({ title, href, hrefLabel }: { title: string; href?: string; hrefLabel?: string }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      {href ? (
        <Link href={href} className="text-sm font-medium text-primary hover:underline">
          {hrefLabel ?? "View all"}
        </Link>
      ) : null}
    </div>
  )
}

export default function DashboardPage() {
  const me = useCurrentUser()
  const recommended = useAsync(() => api.feed({ limit: 6, fallback: false }), [])
  const generalEvents = useAsync(() => api.upcoming(6), [])
  const registered = useAsync(() => api.myRegistered(), [])
  const hosted = useAsync(() => api.myHosted(), [])
  const profile = useAsync(() => api.user(me.user_id), [me.user_id])
  const suggestions = useAsync(() => api.suggestions(4), [])

  const upcomingRegistered = (registered.data ?? []).slice(0, 3)
  const firstName = me.name.split(" ")[0]

  return (
    <div className="space-y-10">
      <section className="flex flex-col gap-4 rounded-2xl border bg-gradient-to-br from-primary/10 via-card to-card p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Welcome back, {firstName}</h1>
          <p className="mt-1 text-muted-foreground">
            Here&apos;s what&apos;s happening on campus and what your connections are up to.
          </p>
        </div>
        <LinkButton size="lg" className="h-10 w-fit px-4 text-sm" href="/events/new">
          <Plus className="h-4 w-4" aria-hidden /> Host an event
        </LinkButton>
      </section>

      <section aria-label="Your activity" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Events registered" value={registered.data?.length ?? "–"} icon={CalendarCheck} />
        <StatCard label="Events submitted" value={hosted.data?.length ?? "–"} icon={ClipboardList} />
        <StatCard label="Following" value={profile.data?.following_count ?? "–"} icon={UserPlus} />
        <StatCard label="Followers" value={profile.data?.followers_count ?? "–"} icon={Users} />
      </section>

      {/* 1. SEPARATE SECTION: Recommended Events based on connections */}
      <section id="recommended-events" className="rounded-2xl border bg-card/60 p-6 shadow-sm">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold tracking-tight text-foreground">
              Recommended Events for You
            </h2>
            <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              Personalized via Network Graph
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Events liked, registered for, or shared by the students you follow or who follow you.
          </p>
        </div>

        {recommended.loading ? (
          <CardGridSkeleton count={3} />
        ) : recommended.error ? (
          <ErrorState error={recommended.error} onRetry={recommended.reload} title="Couldn't load recommendations" />
        ) : (recommended.data ?? []).length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <p className="font-medium text-muted-foreground">No personalized recommendations yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              When classmates you follow or who follow you like or register for events, they will appear here.
            </p>
            <LinkButton href="/people" variant="outline" size="sm" className="mt-4">
              Find and follow students
            </LinkButton>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(recommended.data ?? []).map((event) => (
              <EventCard key={event.event_id} event={event} reason={event.social_context?.reason} />
            ))}
          </div>
        )}
      </section>

      {/* 2. SEPARATE SECTION: General Campus Events */}
      <section id="general-events">
        <SectionHeading title="General Campus Events" href="/events" hrefLabel="View all events" />
        <p className="mb-4 text-sm text-muted-foreground">
          All approved upcoming workshops, hackathons, and gatherings across PSG Tech.
        </p>
        {generalEvents.loading ? (
          <CardGridSkeleton count={3} />
        ) : generalEvents.error ? (
          <ErrorState error={generalEvents.error} onRetry={generalEvents.reload} title="Couldn't load campus events" />
        ) : (generalEvents.data ?? []).length === 0 ? (
          <EmptyState
            title="No upcoming events yet"
            description="When events are approved they'll show up here. Be the first to host one."
            action={
              <LinkButton href="/events/new">
                Host an event
              </LinkButton>
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(generalEvents.data ?? []).map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
        )}
      </section>

      <div className="grid gap-10 lg:grid-cols-2">
        <section>
          <SectionHeading title="Your registrations" href="/my-events" />
          {registered.loading ? (
            <ListSkeleton rows={2} />
          ) : registered.error ? (
            <ErrorState error={registered.error} onRetry={registered.reload} />
          ) : upcomingRegistered.length === 0 ? (
            <EmptyState
              icon={CalendarCheck}
              title="You haven't registered for anything"
              description="Register for an event and it will appear here."
            />
          ) : (
            <ul className="space-y-3">
              {upcomingRegistered.map((e) => (
                <li key={e.event_id}>
                  <Link
                    href={`/events/${e.event_id}`}
                    className="flex items-center justify-between gap-3 rounded-xl border bg-card p-4 transition-colors hover:bg-accent/50"
                  >
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{e.title}</span>
                      <span className="block truncate text-sm text-muted-foreground">
                        {formatDate(e.date)} · {e.venue}
                      </span>
                    </span>
                    <span className="text-xs text-primary">View</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <SectionHeading title="People you may know" href="/people" />
          {suggestions.loading ? (
            <ListSkeleton rows={3} />
          ) : suggestions.error ? (
            <ErrorState error={suggestions.error} onRetry={suggestions.reload} />
          ) : (suggestions.data ?? []).length === 0 ? (
            <EmptyState
              icon={Users}
              title="No suggestions yet"
              description="As more students join and follow each other, suggestions will appear."
            />
          ) : (
            <div className="space-y-3">
              {(suggestions.data ?? []).map((p) => (
                <PersonCard key={p.user_id} person={p} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
