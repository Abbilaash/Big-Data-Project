import Link from "next/link"
import { CalendarCheck, CheckCircle2, Lightbulb, Users } from "lucide-react"

import {
  currentUser,
  events,
  stats,
  students,
} from "@/lib/data"
import { StatCard } from "@/components/stat-card"
import { EventCard } from "@/components/event-card"
import { StudentCard } from "@/components/student-card"
import { Button } from "@/components/ui/button"

const statIcons = [CalendarCheck, CheckCircle2, Lightbulb, Users]

function SectionHeader({
  title,
  href,
}: {
  title: string
  href?: string
}) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <h2 className="text-xl font-semibold">{title}</h2>
      {href ? (
        <Button
          variant="ghost"
          size="sm"
          nativeButton={false}
          render={<Link href={href} />}
        >
          View all
        </Button>
      ) : null}
    </div>
  )
}

export default function DashboardPage() {
  const upcomingEvents = events.slice(0, 3)
  const recommendedEvents = events.slice(3, 6)
  const recommendedTeammates = students.slice(0, 3)

  return (
    <div className="space-y-10">
      {/* Welcome */}
      <section className="rounded-xl border bg-card p-6">
        <h1 className="text-2xl font-bold sm:text-3xl">
          Welcome back, {currentUser.name.split(" ")[0]}!
        </h1>
        <p className="mt-1 max-w-2xl text-muted-foreground">
          Here&apos;s what&apos;s happening around campus. Explore upcoming events,
          discover new opportunities, and connect with fellow students.
        </p>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={stat.value}
            icon={statIcons[i]}
          />
        ))}
      </section>

      {/* Upcoming events */}
      <section>
        <SectionHeader title="Upcoming Events" href="/events" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {upcomingEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </section>

      {/* Recommended events */}
      <section>
        <SectionHeader title="Recommended Events" href="/events" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recommendedEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </section>

      {/* Recommended teammates */}
      <section>
        <SectionHeader title="Recommended Teammates" href="/teammates" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recommendedTeammates.map((student) => (
            <StudentCard key={student.id} student={student} showConnect />
          ))}
        </div>
      </section>
    </div>
  )
}
