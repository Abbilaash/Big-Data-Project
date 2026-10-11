"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { api, ApiError } from "@/lib/api"
import { errorMessage } from "@/lib/use-async"
import { todayLocalISO } from "@/lib/format"
import { useToast } from "@/components/toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { PageHeader } from "@/components/page-header"
import { SelectField } from "@/components/select-field"
import { Spinner } from "@/components/state-views"

const FALLBACK_CATEGORIES = ["Hackathon", "Workshop", "Bootcamp", "Seminar", "Contest", "Meetup", "Cultural", "Sports", "Other"]

interface Form {
  title: string
  category: string
  date: string
  start_time: string
  end_time: string
  venue: string
  description: string
  registration_url: string
  poster_url: string
  tags: string
}

const EMPTY: Form = {
  title: "",
  category: "",
  date: "",
  start_time: "",
  end_time: "",
  venue: "",
  description: "",
  registration_url: "",
  poster_url: "",
  tags: "",
}

function isHttpUrl(v: string): boolean {
  try {
    const u = new URL(v)
    return u.protocol === "http:" || u.protocol === "https:"
  } catch {
    return false
  }
}

/** Client-side mirror of the backend rules, for immediate feedback. */
function validate(f: Form): Record<string, string> {
  const e: Record<string, string> = {}
  if (f.title.trim().length < 3) e.title = "Give your event a title (at least 3 characters)."
  if (!f.category) e.category = "Choose a category."
  if (!f.date) e.date = "Pick a date."
  else if (f.date < todayLocalISO()) e.date = "The date can't be in the past."
  if (!f.start_time) e.start_time = "Set a start time."
  if (!f.end_time) e.end_time = "Set an end time."
  else if (f.start_time && f.end_time <= f.start_time) e.end_time = "End time must be after the start time."
  if (f.venue.trim().length < 2) e.venue = "Where is it happening?"
  if (f.description.trim().length < 10) e.description = "Describe the event (at least 10 characters)."
  if (f.registration_url.trim() && !isHttpUrl(f.registration_url.trim()))
    e.registration_url = "Enter a full http(s) link."
  if (f.poster_url.trim() && !isHttpUrl(f.poster_url.trim())) e.poster_url = "Enter a full http(s) image link."
  const tags = f.tags.split(",").map((t) => t.trim()).filter(Boolean)
  if (tags.length > 10) e.tags = "Use at most 10 tags."
  else if (tags.some((t) => t.length > 30)) e.tags = "Each tag must be 30 characters or fewer."
  return e
}

function Field({
  id,
  label,
  error,
  hint,
  children,
}: {
  id: string
  label: string
  error?: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? (
        <p id={`${id}-err`} role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-muted-foreground">{hint}</p>
      ) : null}
    </div>
  )
}

export default function NewEventPage() {
  const router = useRouter()
  const toast = useToast()
  const [form, setForm] = useState<Form>(EMPTY)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [categories, setCategories] = useState<string[]>(FALLBACK_CATEGORIES)
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    api.categories().then((r) => setCategories(r.categories)).catch(() => undefined)
  }, [])

  const set = <K extends keyof Form>(key: K, value: Form[K]) => {
    setForm((f) => ({ ...f, [key]: value }))
    if (errors[key]) setErrors((e) => ({ ...e, [key]: "" }))
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length) {
      document.getElementById(Object.keys(found)[0])?.focus()
      return
    }
    setBusy(true)
    try {
      await api.createEvent({
        title: form.title.trim(),
        category: form.category,
        date: form.date,
        start_time: form.start_time,
        end_time: form.end_time,
        venue: form.venue.trim(),
        description: form.description.trim(),
        registration_url: form.registration_url.trim() || null,
        poster_url: form.poster_url.trim() || null,
        tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      })
      toast.success("Event submitted. It will appear publicly once an admin approves it.")
      router.push("/my-events?tab=hosted")
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) setErrors(err.fields)
      setFormError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const invalid = (k: keyof Form) => (errors[k] ? true : undefined)

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Host an event"
        description="Submit your event for review. Admins approve events before they appear to everyone."
      />

      <form onSubmit={submit} noValidate className="space-y-6 rounded-2xl border bg-card p-6 shadow-sm">
        <Field id="title" label="Title" error={errors.title}>
          <Input
            id="title"
            value={form.title}
            maxLength={200}
            aria-invalid={invalid("title")}
            onChange={(e) => set("title", e.target.value)}
            placeholder="e.g. 24-hour AI Hackathon"
          />
        </Field>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="category" label="Category" error={errors.category}>
            <SelectField
              id="category"
              value={form.category}
              onChange={(v) => set("category", v)}
              placeholder="Select a category"
              className="w-full"
              options={categories.map((c) => ({ value: c, label: c }))}
            />
          </Field>
          <Field id="venue" label="Venue" error={errors.venue}>
            <Input
              id="venue"
              value={form.venue}
              maxLength={150}
              aria-invalid={invalid("venue")}
              onChange={(e) => set("venue", e.target.value)}
              placeholder="e.g. Main Auditorium"
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          <Field id="date" label="Date" error={errors.date}>
            <Input
              id="date"
              type="date"
              min={todayLocalISO()}
              value={form.date}
              aria-invalid={invalid("date")}
              onChange={(e) => set("date", e.target.value)}
            />
          </Field>
          <Field id="start_time" label="Starts" error={errors.start_time}>
            <Input
              id="start_time"
              type="time"
              value={form.start_time}
              aria-invalid={invalid("start_time")}
              onChange={(e) => set("start_time", e.target.value)}
            />
          </Field>
          <Field id="end_time" label="Ends" error={errors.end_time}>
            <Input
              id="end_time"
              type="time"
              value={form.end_time}
              aria-invalid={invalid("end_time")}
              onChange={(e) => set("end_time", e.target.value)}
            />
          </Field>
        </div>

        <Field id="description" label="Description" error={errors.description}>
          <Textarea
            id="description"
            rows={6}
            value={form.description}
            maxLength={5000}
            aria-invalid={invalid("description")}
            onChange={(e) => set("description", e.target.value)}
            placeholder="What's it about, who is it for, what should people bring?"
          />
        </Field>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field id="registration_url" label="Registration link (optional)" error={errors.registration_url}>
            <Input
              id="registration_url"
              type="url"
              inputMode="url"
              value={form.registration_url}
              aria-invalid={invalid("registration_url")}
              onChange={(e) => set("registration_url", e.target.value)}
              placeholder="https://…"
            />
          </Field>
          <Field id="poster_url" label="Poster image link (optional)" error={errors.poster_url}>
            <Input
              id="poster_url"
              type="url"
              inputMode="url"
              value={form.poster_url}
              aria-invalid={invalid("poster_url")}
              onChange={(e) => set("poster_url", e.target.value)}
              placeholder="https://…/poster.jpg"
            />
          </Field>
        </div>

        <Field id="tags" label="Tags (optional)" error={errors.tags} hint="Comma-separated, e.g. ai, python, beginners">
          <Input
            id="tags"
            value={form.tags}
            aria-invalid={invalid("tags")}
            onChange={(e) => set("tags", e.target.value)}
          />
        </Field>

        {formError ? (
          <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
            {formError}
          </p>
        ) : null}

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" size="lg" className="h-10 px-4 text-sm" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" size="lg" className="h-10 px-5 text-sm" disabled={busy}>
            {busy ? <Spinner /> : null} Submit for review
          </Button>
        </div>
      </form>
    </div>
  )
}
