"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, CalendarHeart, Users } from "lucide-react"

import { api } from "@/lib/api"
import { useCurrentUser } from "@/lib/auth"
import { useAsync } from "@/lib/use-async"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FollowButton } from "@/components/follow-button"
import { PersonCard } from "@/components/person-card"
import { ProfileHeader } from "@/components/profile-header"
import { EmptyState, ErrorState, ListSkeleton, PageLoading } from "@/components/state-views"
import { LinkButton } from "@/components/link-button"

export default function PersonProfilePage() {
  const { id } = useParams<{ id: string }>()
  const me = useCurrentUser()
  const router = useRouter()

  useEffect(() => {
    if (id === me.user_id) router.replace("/profile")
  }, [id, me.user_id, router])

  const profile = useAsync(() => api.user(id), [id])
  const status = useAsync(() => api.followStatus(id), [id])
  const mutuals = useAsync(() => api.mutuals(id), [id])
  const common = useAsync(() => api.commonInterests(id), [id])
  const followers = useAsync(() => api.followers(id), [id])
  const following = useAsync(() => api.following(id), [id])

  if (id === me.user_id) return <PageLoading />

  return (
    <div className="space-y-6">
      <Link
        href="/people"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> All people
      </Link>

      {profile.loading ? (
        <PageLoading label="Loading profile…" />
      ) : profile.error ? (
        profile.error.status === 404 ? (
          <EmptyState
            title="Profile not found"
            description="This person doesn't exist or hasn't finished setting up their profile."
            action={
              <LinkButton href="/people">
                Browse people
              </LinkButton>
            }
          />
        ) : (
          <ErrorState error={profile.error} onRetry={profile.reload} />
        )
      ) : profile.data ? (
        <>
          <ProfileHeader
            name={profile.data.name}
            department={profile.data.department}
            year={profile.data.year}
            picture={profile.data.profile_picture}
            followers={profile.data.followers_count}
            following={profile.data.following_count}
            actions={
              status.loading ? null : (
                <FollowButton
                  size="lg"
                  userId={id}
                  name={profile.data.name}
                  initialFollowing={status.data?.is_following ?? false}
                  onChange={() => {
                    profile.reload()
                    mutuals.reload()
                    followers.reload()
                  }}
                />
              )
            }
          />

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-4 w-4" aria-hidden /> Mutual connections
                </CardTitle>
              </CardHeader>
              <CardContent>
                {mutuals.loading ? (
                  <ListSkeleton rows={2} />
                ) : mutuals.error ? (
                  <ErrorState error={mutuals.error} onRetry={mutuals.reload} />
                ) : (mutuals.data ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    You don&apos;t follow any of the same people yet.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {(mutuals.data ?? []).map((p) => (
                      <PersonCard key={p.user_id} person={p} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarHeart className="h-4 w-4" aria-hidden /> Events you have in common
                </CardTitle>
              </CardHeader>
              <CardContent>
                {common.loading ? (
                  <ListSkeleton rows={2} />
                ) : common.error ? (
                  <ErrorState error={common.error} onRetry={common.reload} />
                ) : (common.data ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No shared events yet. Like or register for the same events to see them here.
                  </p>
                ) : (
                  <ul className="space-y-3">
                    {(common.data ?? []).map((c) => (
                      <li key={c.event_id}>
                        <Link
                          href={`/events/${c.event_id}`}
                          className="block rounded-lg border p-3 transition-colors hover:bg-accent/50"
                        >
                          <span className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">{c.title}</span>
                            <Badge variant="secondary">{c.category}</Badge>
                          </span>
                          <span className="text-sm text-muted-foreground">{c.interaction_type}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {[
              { title: "Followers", state: followers },
              { title: "Following", state: following },
            ].map(({ title, state }) => (
              <Card key={title}>
                <CardHeader>
                  <CardTitle>{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  {state.loading ? (
                    <ListSkeleton rows={2} />
                  ) : state.error ? (
                    <ErrorState error={state.error} onRetry={state.reload} />
                  ) : (state.data ?? []).length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nobody yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {(state.data ?? []).map((p) => (
                        <PersonCard key={p.user_id} person={p} showFollow={p.user_id !== me.user_id} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      ) : null}
    </div>
  )
}
