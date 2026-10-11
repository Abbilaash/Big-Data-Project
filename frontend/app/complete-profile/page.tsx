"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { api, ApiError, getToken } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { DEPARTMENTS, YEARS } from "@/lib/constants"
import { errorMessage } from "@/lib/use-async"
import { yearLabel } from "@/lib/format"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SelectField } from "@/components/select-field"
import { Spinner } from "@/components/state-views"

export default function CompleteProfilePage() {
  const router = useRouter()
  const { signIn } = useAuth()
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [year, setYear] = useState("")
  const [department, setDepartment] = useState("")
  const [picture, setPicture] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  // Prefill from the Google identity the backend already holds.
  useEffect(() => {
    let cancelled = false
    api
      .session()
      .then((s) => {
        if (cancelled) return
        setEmail(s.email)
        setName((current) => current || s.name)
        setPicture(s.profile_picture || null)
      })
      .catch(() => {
        /* the form still works without prefill */
      })
    return () => {
      cancelled = true
    }
  }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = "Please enter your name."
    if (!year) errs.year = "Please choose your year."
    if (!department) errs.department = "Please choose your department."
    setFieldErrors(errs)
    if (Object.keys(errs).length) return

    setBusy(true)
    try {
      const result = await api.completeProfile(
        { name: name.trim(), year: Number(year), department, profile_picture: picture },
        getToken(),
      )
      await signIn(result.access_token)
      router.replace("/")
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) setFieldErrors(err.fields)
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md py-6 sm:py-12">
      <h1 className="text-2xl font-bold tracking-tight">Finish setting up your profile</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        A few details so classmates can find you{email ? ` (signed in as ${email})` : ""}.
      </p>

      <form onSubmit={submit} noValidate className="mt-6 space-y-5 rounded-2xl border bg-card p-6 shadow-sm">
        <div className="space-y-1.5">
          <Label htmlFor="name">Full name</Label>
          <Input
            id="name"
            value={name}
            maxLength={100}
            onChange={(e) => setName(e.target.value)}
            aria-invalid={!!fieldErrors.name}
            aria-describedby={fieldErrors.name ? "name-err" : undefined}
          />
          {fieldErrors.name ? (
            <p id="name-err" className="text-sm text-destructive">
              {fieldErrors.name}
            </p>
          ) : null}
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="year">Year of study</Label>
            <SelectField
              id="year"
              value={year}
              onChange={setYear}
              placeholder="Select year"
              className="w-full"
              options={YEARS.map((y) => ({ value: String(y), label: yearLabel(y) }))}
            />
            {fieldErrors.year ? <p className="text-sm text-destructive">{fieldErrors.year}</p> : null}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="department">Department</Label>
            <SelectField
              id="department"
              value={department}
              onChange={setDepartment}
              placeholder="Select department"
              className="w-full"
              options={DEPARTMENTS.map((d) => ({ value: d, label: d }))}
            />
            {fieldErrors.department ? (
              <p className="text-sm text-destructive">{fieldErrors.department}</p>
            ) : null}
          </div>
        </div>

        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <Button type="submit" size="lg" className="h-10 w-full text-sm" disabled={busy}>
          {busy ? <Spinner /> : null} Continue
        </Button>
      </form>
    </div>
  )
}
