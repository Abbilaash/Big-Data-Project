"use client"

import Link from "next/link"

import type { PersonSummary } from "@/lib/types"
import { yearLabel } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { FollowButton } from "@/components/follow-button"
import { UserAvatar } from "@/components/user-avatar"

export function PersonCard({
  person,
  showFollow = true,
}: {
  person: PersonSummary
  showFollow?: boolean
}) {
  const meta = [person.department, yearLabel(person.year)].filter(Boolean).join(" · ")
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <Link href={`/people/${person.user_id}`} aria-label={`View ${person.name}'s profile`}>
          <UserAvatar name={person.name} src={person.profile_picture} className="h-12 w-12" />
        </Link>
        <div className="min-w-0 flex-1">
          <Link
            href={`/people/${person.user_id}`}
            className="block truncate font-semibold leading-tight hover:underline"
          >
            {person.name}
          </Link>
          {meta ? <p className="truncate text-sm text-muted-foreground">{meta}</p> : null}
          {person.mutual_count ? (
            <Badge variant="secondary" className="mt-1">
              {person.mutual_count} mutual {person.mutual_count === 1 ? "connection" : "connections"}
            </Badge>
          ) : null}
        </div>
        {showFollow ? (
          <FollowButton
            userId={person.user_id}
            name={person.name}
            initialFollowing={!!person.is_following}
            size="sm"
          />
        ) : null}
      </CardContent>
    </Card>
  )
}
