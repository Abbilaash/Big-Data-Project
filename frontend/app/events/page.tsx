"use client"

import { useState } from "react"

import { events, categories } from "@/lib/data"
import { PageHeader } from "@/components/page-header"
import { SearchBar } from "@/components/search-bar"
import { EventCard } from "@/components/event-card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function EventsPage() {
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("All")

  const filtered = events.filter((event) => {
    const matchesQuery = event.name.toLowerCase().includes(query.toLowerCase())
    const matchesCategory = category === "All" || event.category === category
    return matchesQuery && matchesCategory
  })

  return (
    <div>
      <PageHeader
        title="Campus Events"
        description="Browse and register for upcoming events happening across campus."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <SearchBar
          value={query}
          onChange={setQuery}
          placeholder="Search events..."
        />
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-muted-foreground">
          No events found. Try a different search or category.
        </p>
      )}
    </div>
  )
}
