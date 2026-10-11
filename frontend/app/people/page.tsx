"use client"

import { useEffect, useState } from "react"
import { Sparkles, Users } from "lucide-react"

import { api, type ApiError } from "@/lib/api"
import { YEARS } from "@/lib/constants"
import { errorMessage, useAsync } from "@/lib/use-async"
import { yearLabel } from "@/lib/format"
import type { PersonSummary } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/page-header"
import { PersonCard } from "@/components/person-card"
import { SearchBar } from "@/components/search-bar"
import { SelectField } from "@/components/select-field"
import { EmptyState, ErrorState, ListSkeleton, Spinner } from "@/components/state-views"
import { useToast } from "@/components/toast"

const PAGE_SIZE = 24

export default function PeoplePage() {
  const toast = useToast()
  const [query, setQuery] = useState("")
  const [debounced, setDebounced] = useState("")
  const [department, setDepartment] = useState("all")
  const [year, setYear] = useState("all")

  const [people, setPeople] = useState<PersonSummary[]>([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [retry, setRetry] = useState(0)

  const departments = useAsync(() => api.departments(), [])
  const suggestions = useAsync(() => api.suggestions(6), [])

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(query.trim()), 300)
    return () => window.clearTimeout(t)
  }, [query])

  const filters = () => ({
    q: debounced || undefined,
    department: department === "all" ? undefined : department,
    year: year === "all" ? undefined : Number(year),
  })

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .people({ ...filters(), page: 1, limit: PAGE_SIZE })
      .then((rows) => {
        if (cancelled) return
        setPeople(rows)
        setPage(1)
        setHasMore(rows.length === PAGE_SIZE)
      })
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced, department, year, retry])

  const loadMore = async () => {
    setLoadingMore(true)
    try {
      const next = page + 1
      const rows = await api.people({ ...filters(), page: next, limit: PAGE_SIZE })
      setPeople((prev) => {
        const seen = new Set(prev.map((p) => p.user_id))
        return [...prev, ...rows.filter((p) => !seen.has(p.user_id))]
      })
      setPage(next)
      setHasMore(rows.length === PAGE_SIZE)
    } catch (e) {
      toast.error(errorMessage(e, "Couldn't load more people."))
    } finally {
      setLoadingMore(false)
    }
  }

  const filtering = Boolean(debounced) || department !== "all" || year !== "all"
  const suggested = (suggestions.data ?? []).filter((s) => s.mutual_count && s.mutual_count > 0)

  return (
    <div className="space-y-8">
      <PageHeader
        title="People"
        description="Find classmates, follow them, and see the events they care about."
      />

      {!filtering && suggested.length > 0 ? (
        <section aria-labelledby="suggested-heading">
          <h2 id="suggested-heading" className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden /> Friends of friends
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {suggested.map((p) => (
              <PersonCard key={p.user_id} person={p} />
            ))}
          </div>
        </section>
      ) : null}

      <section aria-labelledby="directory-heading">
        <h2 id="directory-heading" className="sr-only">
          Directory
        </h2>
        <div className="mb-5 flex flex-col gap-3 sm:flex-row">
          <SearchBar value={query} onChange={setQuery} placeholder="Search by name or department…" />
          <SelectField
            aria-label="Department"
            value={department}
            onChange={setDepartment}
            className="w-full sm:w-44"
            options={[
              { value: "all", label: "All departments" },
              ...(departments.data ?? []).map((d) => ({ value: d, label: d })),
            ]}
          />
          <SelectField
            aria-label="Year"
            value={year}
            onChange={setYear}
            className="w-full sm:w-40"
            options={[
              { value: "all", label: "All years" },
              ...YEARS.map((y) => ({ value: String(y), label: yearLabel(y) })),
            ]}
          />
        </div>

        {loading ? (
          <ListSkeleton rows={6} />
        ) : error ? (
          <ErrorState error={error} onRetry={() => setRetry((n) => n + 1)} title="Couldn't load people" />
        ) : people.length === 0 ? (
          <EmptyState
            icon={Users}
            title={filtering ? "No one matches those filters" : "No one else has joined yet"}
            description={
              filtering
                ? "Try a different name or clear the filters."
                : "Invite classmates — they'll show up here once they finish setting up."
            }
            action={
              filtering ? (
                <Button
                  variant="outline"
                  onClick={() => {
                    setQuery("")
                    setDepartment("all")
                    setYear("all")
                  }}
                >
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {people.map((p) => (
                <PersonCard key={p.user_id} person={p} />
              ))}
            </div>
            {hasMore ? (
              <div className="mt-8 flex justify-center">
                <Button
                  variant="outline"
                  size="lg"
                  className="h-10 px-5 text-sm"
                  disabled={loadingMore}
                  onClick={() => void loadMore()}
                >
                  {loadingMore ? <Spinner /> : null} Load more
                </Button>
              </div>
            ) : null}
          </>
        )}
      </section>
    </div>
  )
}
