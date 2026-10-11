"use client"

import { useState } from "react"
import Link from "next/link"
import { Pencil } from "lucide-react"

import { api, ApiError } from "@/lib/api"
import { useAuth, useCurrentUser } from "@/lib/auth"
import { DEPARTMENTS, YEARS } from "@/lib/constants"
import { errorMessage, useAsync } from "@/lib/use-async"
import { yearLabel } from "@/lib/format"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PersonCard } from "@/components/person-card"
import { ProfileHeader } from "@/components/profile-header"
import { SelectField } from "@/components/select-field"
import { ErrorState, ListSkeleton, Spinner } from "@/components/state-views"
import { useToast } from "@/components/toast"
import { LinkButton } from "@/components/link-button"

function EditProfileDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const me = useCurrentUser()
  const { setUser } = useAuth()
  const toast = useToast()
  const [name, setName] = useState(me.name)
  const [year, setYear] = useState(me.year ? String(me.year) : "")
  const [department, setDepartment] = useState(me.department ?? "")
  const [picture, setPicture] = useState(me.profile_picture ?? "")
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)

  const departmentOptions = Array.from(new Set([...DEPARTMENTS, ...(me.department ? [me.department] : [])]))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = "Name can't be empty."
    if (!year) errs.year = "Choose your year."
    if (!department) errs.department = "Choose your department."
    if (picture.trim() && !/^https?:\/\//i.test(picture.trim())) errs.profile_picture = "Enter a full http(s) link."
    setErrors(errs)
    if (Object.keys(errs).length) return

    const body: Record<string, string | number> = {}
    if (name.trim() !== me.name) body.name = name.trim()
    if (Number(year) !== me.year) body.year = Number(year)
    if (department !== me.department) body.department = department
    if (picture.trim() && picture.trim() !== me.profile_picture) body.profile_picture = picture.trim()
    if (Object.keys(body).length === 0) {
      onOpenChange(false)
      return
    }

    setBusy(true)
    try {
      const updated = await api.updateMe(body)
      setUser(updated)
      toast.success("Profile updated.")
      onOpenChange(false)
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) setErrors(err.fields)
      setFormError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={submit} noValidate className="grid gap-4">
          <DialogHeader>
            <DialogTitle>Edit profile</DialogTitle>
            <DialogDescription>Update how you appear to other students.</DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            <Label htmlFor="edit-name">Name</Label>
            <Input id="edit-name" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} />
            {errors.name ? <p className="text-sm text-destructive">{errors.name}</p> : null}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="edit-year">Year</Label>
              <SelectField
                id="edit-year"
                value={year}
                onChange={setYear}
                className="w-full"
                options={YEARS.map((y) => ({ value: String(y), label: yearLabel(y) }))}
              />
              {errors.year ? <p className="text-sm text-destructive">{errors.year}</p> : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-dept">Department</Label>
              <SelectField
                id="edit-dept"
                value={department}
                onChange={setDepartment}
                className="w-full"
                options={departmentOptions.map((d) => ({ value: d, label: d }))}
              />
              {errors.department ? <p className="text-sm text-destructive">{errors.department}</p> : null}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-picture">Profile picture link (optional)</Label>
            <Input
              id="edit-picture"
              type="url"
              inputMode="url"
              value={picture}
              onChange={(e) => setPicture(e.target.value)}
              placeholder="https://…"
            />
            {errors.profile_picture ? <p className="text-sm text-destructive">{errors.profile_picture}</p> : null}
          </div>

          {formError ? (
            <p role="alert" className="text-sm text-destructive">
              {formError}
            </p>
          ) : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? <Spinner /> : null} Save changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function ProfilePage() {
  const me = useCurrentUser()
  const [editing, setEditing] = useState(false)
  const counts = useAsync(() => api.user(me.user_id), [me.user_id])
  const followers = useAsync(() => api.followers(me.user_id), [me.user_id])
  const following = useAsync(() => api.following(me.user_id), [me.user_id])

  return (
    <div className="space-y-6">
      <ProfileHeader
        name={me.name}
        department={me.department}
        year={me.year}
        picture={me.profile_picture}
        email={me.email}
        followers={counts.data?.followers_count ?? 0}
        following={counts.data?.following_count ?? 0}
        actions={
          <Button variant="outline" size="lg" onClick={() => setEditing(true)}>
            <Pencil className="h-4 w-4" aria-hidden /> Edit profile
          </Button>
        }
      />

      <div className="flex flex-wrap gap-3">
        <LinkButton variant="outline" href="/my-events?tab=hosted">
          My submitted events
        </LinkButton>
        {me.role === "ADMIN" ? (
          <LinkButton variant="outline" href="/admin">
            Admin console
          </LinkButton>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {[
          { title: "Followers", state: followers, empty: "No followers yet. Share an event or say hello." },
          { title: "Following", state: following, empty: "You're not following anyone yet — try the People page." },
        ].map(({ title, state, empty }) => (
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
                <p className="text-sm text-muted-foreground">{empty}</p>
              ) : (
                <div className="space-y-3">
                  {(state.data ?? []).map((p) => (
                    <PersonCard key={p.user_id} person={p} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {editing ? <EditProfileDialog open={editing} onOpenChange={setEditing} /> : null}
    </div>
  )
}
