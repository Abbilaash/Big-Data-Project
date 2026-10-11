import { GraduationCap } from "lucide-react"

import { yearLabel } from "@/lib/format"
import { Card, CardContent } from "@/components/ui/card"
import { UserAvatar } from "@/components/user-avatar"

export function ProfileHeader({
  name,
  department,
  year,
  picture,
  email,
  followers,
  following,
  actions,
}: {
  name: string
  department: string | null
  year: number | null
  picture: string | null
  email?: string
  followers: number
  following: number
  actions?: React.ReactNode
}) {
  const meta = [department, yearLabel(year)].filter(Boolean).join(" · ")
  return (
    <Card>
      <CardContent className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center">
        <UserAvatar name={name} src={picture} className="h-20 w-20 text-xl" />
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-2xl font-bold tracking-tight">{name}</h1>
          {meta ? (
            <p className="mt-1 flex items-center gap-1.5 text-muted-foreground">
              <GraduationCap className="h-4 w-4" aria-hidden /> {meta}
            </p>
          ) : null}
          {email ? <p className="mt-0.5 truncate text-sm text-muted-foreground">{email}</p> : null}
          <dl className="mt-3 flex gap-6 text-sm">
            <div>
              <dt className="sr-only">Followers</dt>
              <dd>
                <span className="font-semibold">{followers}</span> <span className="text-muted-foreground">followers</span>
              </dd>
            </div>
            <div>
              <dt className="sr-only">Following</dt>
              <dd>
                <span className="font-semibold">{following}</span> <span className="text-muted-foreground">following</span>
              </dd>
            </div>
          </dl>
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </CardContent>
    </Card>
  )
}
