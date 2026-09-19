import Link from "next/link"
import { notFound } from "next/navigation"
import {
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  Building2,
  Users,
} from "lucide-react"

import { events } from "@/lib/data"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default async function EventDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const event = events.find((e) => e.id === id)

  if (!event) {
    notFound()
  }

  const details = [
    { icon: Calendar, label: "Date", value: event.date },
    { icon: Clock, label: "Time", value: event.time },
    { icon: MapPin, label: "Location", value: event.location },
    { icon: Building2, label: "Organizer", value: event.organizer },
    { icon: Users, label: "Participants", value: `${event.participants} registered` },
  ]

  return (
    <div className="mx-auto max-w-3xl">
      <Button
        variant="ghost"
        size="sm"
        className="mb-4"
        nativeButton={false}
        render={<Link href="/events" />}
      >
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to Events
      </Button>

      <Card>
        <CardHeader>
          <Badge variant="secondary" className="w-fit">
            {event.category}
          </Badge>
          <CardTitle className="mt-2 text-2xl">{event.name}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {details.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-start gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" />
                </span>
                <div>
                  <dt className="text-xs text-muted-foreground">{label}</dt>
                  <dd className="text-sm font-medium">{value}</dd>
                </div>
              </div>
            ))}
          </dl>

          <div>
            <h2 className="mb-1.5 font-semibold">Description</h2>
            <p className="text-muted-foreground">{event.description}</p>
          </div>

          <div>
            <h2 className="mb-2 font-semibold">Required Skills</h2>
            <div className="flex flex-wrap gap-1.5">
              {event.skills.map((skill) => (
                <Badge key={skill} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button className="flex-1 sm:flex-none">Register</Button>
            <Button
              variant="outline"
              className="flex-1 sm:flex-none"
              nativeButton={false}
              render={<Link href="/events" />}
            >
              Back to Events
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
