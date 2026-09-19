import Link from "next/link"
import { Calendar, MapPin, Users, Building2 } from "lucide-react"

import type { EventItem } from "@/lib/data"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export function EventCard({ event }: { event: EventItem }) {
  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <Badge variant="secondary" className="w-fit">
          {event.category}
        </Badge>
        <CardTitle className="mt-2 text-lg">{event.name}</CardTitle>
      </CardHeader>

      <CardContent className="flex-1 space-y-3">
        <p className="text-sm text-muted-foreground">{event.description}</p>
        <ul className="space-y-1.5 text-sm">
          <li className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-4 w-4 shrink-0" />
            {event.date}
          </li>
          <li className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="h-4 w-4 shrink-0" />
            {event.location}
          </li>
          <li className="flex items-center gap-2 text-muted-foreground">
            <Building2 className="h-4 w-4 shrink-0" />
            {event.organizer}
          </li>
          <li className="flex items-center gap-2 text-muted-foreground">
            <Users className="h-4 w-4 shrink-0" />
            {event.participants} participants
          </li>
        </ul>
      </CardContent>

      <CardFooter className="gap-2">
        <Button
          variant="outline"
          className="flex-1"
          nativeButton={false}
          render={<Link href={`/events/${event.id}`} />}
        >
          View Details
        </Button>
        <Button className="flex-1">Register</Button>
      </CardFooter>
    </Card>
  )
}
