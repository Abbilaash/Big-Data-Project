"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { CalendarSearch, Plus } from "lucide-react"

import { api, type ApiError } from "@/lib/api"
import { errorMessage } from "@/lib/use-async"
import { useToast } from "@/components/toast"
import type { EventItem } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { EventCard } from "@/components/event-card"
import { PageHeader } from "@/components/page-header"
import { SearchBar } from "@/components/search-bar"
import { SelectField } from "@/components/select-field"
import { CardGridSkeleton, EmptyState, ErrorState, Spinner } from "@/components/state-views"
import { LinkButton } from "@/components/link-button"

const PAGE_SIZE = 12

export default function EventsPage() {
  const toast = useToast()
  const [query, setQuery] = useState("")
  const [debounced, setDebounced] = useState("")
  const [category, setCategory] = useState("all")
  const [upcomingOnly, setUpcomingOnly] = useState(true)
  const [categories, setCategories] = useState<string[]>([])

  const [events, setEvents] = useState<EventItem[]>([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    api.categories().then((r) => setCategories(r.categories)).catch(() => undefined)
  }, [])

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(query.trim()), 300)
    return () => window.clearTimeout(t)
  }, [query])

  // Reset to page 1 whenever a filter changes.
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .events({
        search: debounced || undefined,
        category: category === "all" ? undefined : category,
        upcoming_only: upcomingOnly,
        page: 1,
        limit: PAGE_SIZE,
      })
      .then((rows) => {
        if (cancelled) return
        setEvents(rows)
        setPage(1)
        setHasMore(rows.length === PAGE_SIZE)
      })
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [debounced, category, upcomingOnly, retry])

  const loadMore = async () => {
    setLoadingMore(true)
    try {
      const next = page + 1
      const rows = await api.events({
        search: debounced || undefined,
        category: category === "all" ? undefined : category,
        upcoming_only: upcomingOnly,
        page: next,
        limit: PAGE_SIZE,
      })
      setEvents((prev) => {
        const seen = new Set(prev.map((e) => e.event_id))
        return [...prev, ...rows.filter((e) => !seen.has(e.event_id))]
      })
      setPage(next)
      setHasMore(rows.length === PAGE_SIZE)
    } catch (e) {
      toast.error(errorMessage(e, "Couldn't load more events."))
    } finally {
      setLoadingMore(false)
    }
  }

  const filtered = Boolean(debounced) || category !== "all"

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader title="Campus Events" description="Browse and register for events happening across campus." />
        <LinkButton size="lg" className="h-10 px-4 text-sm" href="/events/new">
          <Plus className="h-4 w-4" aria-hidden /> Host an event
        </LinkButton>
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <SearchBar value={query} onChange={setQuery} placeholder="Search by title, description or tag…" />
        <SelectField
          aria-label="Category"
          value={category}
          onChange={setCategory}
          className="w-full sm:w-48"
          options={[{ value: "all", label: "All categories" }, ...categories.map((c) => ({ value: c, label: c }))]}
        />
        <label className="flex shrink-0 cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={upcomingOnly}
            onChange={(e) => setUpcomingOnly(e.target.checked)}
            className="h-4 w-4 rounded border-input accent-[var(--primary)]"
          />
          Upcoming only
        </label>
      </div>

      {loading ? (
        <CardGridSkeleton />
      ) : error && events.length === 0 ? (
        <ErrorState error={error} onRetry={() => setRetry((n) => n + 1)} title="Couldn't load events" />
      ) : events.length === 0 ? (
        <EmptyState
          icon={CalendarSearch}
          title={filtered ? "No events match your filters" : "No events yet"}
          description={
            filtered
              ? "Try a different search term or category."
              : "Approved events will appear here. Be the first to host one."
          }
          action={
            filtered ? (
              <Button
                variant="outline"
                onClick={() => {
                  setQuery("")
                  setCategory("all")
                }}
              >
                Clear filters
              </Button>
            ) : (
              <LinkButton href="/events/new">
                Host an event
              </LinkButton>
            )
          }
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {events.map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
          {hasMore ? (
            <div className="mt-8 flex justify-center">
              <Button variant="outline" size="lg" className="h-10 px-5 text-sm" disabled={loadingMore} onClick={() => void loadMore()}>
                {loadingMore ? <Spinner /> : null} Load more
              </Button>
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}
