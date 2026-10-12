"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

import { api, ApiError } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { DEPARTMENTS, YEARS } from "@/lib/constants"
import { yearLabel } from "@/lib/format"
import { errorMessage } from "@/lib/use-async"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SelectField } from "@/components/select-field"
import { Spinner } from "@/components/state-views"

export function SignInCard({ defaultMode = "login" }: { defaultMode?: "login" | "register" } = {}) {
  const router = useRouter()
  const { signIn } = useAuth()
  const [mode, setMode] = useState<"login" | "register">(defaultMode)

  // Login form state
  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  // Register form state
  const [regName, setRegName] = useState("")
  const [regEmail, setRegEmail] = useState("")
  const [regPassword, setRegPassword] = useState("")
  const [regYear, setRegYear] = useState("1")
  const [regDepartment, setRegDepartment] = useState("CSE")

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await api.login(loginEmail.trim(), loginPassword)
      await signIn(result.access_token)
      router.push("/")
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!regName.trim()) {
      setError("Please enter your full name.")
      return
    }
    if (regPassword.length < 6) {
      setError("Password must be at least 6 characters.")
      return
    }

    setBusy(true)
    try {
      const result = await api.registerUser({
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        year: Number(regYear),
        department: regDepartment,
      })
      await signIn(result.access_token)
      router.push("/")
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section id="auth-card" className="rounded-2xl border bg-card p-6 shadow-sm sm:p-8">
      {/* Mode Toggle Tabs */}
      <div className="flex rounded-lg border bg-muted/40 p-1">
        <button
          type="button"
          onClick={() => {
            setMode("login")
            setError(null)
          }}
          className={`flex-1 rounded-md py-1.5 text-center text-sm font-medium transition-all ${
            mode === "login"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("register")
            setError(null)
          }}
          className={`flex-1 rounded-md py-1.5 text-center text-sm font-medium transition-all ${
            mode === "register"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Register Now
        </button>
      </div>

      {mode === "login" ? (
        /* Sign In Form */
        <form onSubmit={handleLogin} className="mt-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Welcome back</h2>
            <p className="mt-1 text-sm text-muted-foreground">Sign in with your email and password.</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="login-email">Email Address</Label>
            <Input
              id="login-email"
              type="email"
              autoComplete="email"
              required
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              placeholder="student@college.edu"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="login-password">Password</Label>
            <Input
              id="login-password"
              type="password"
              autoComplete="current-password"
              required
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error ? (
            <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          <Button type="submit" size="lg" className="h-10 w-full text-sm font-medium" disabled={busy}>
            {busy ? <Spinner className="mr-2" /> : null} Sign In
          </Button>

          <p className="pt-2 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <button
              type="button"
              onClick={() => {
                setMode("register")
                setError(null)
              }}
              className="font-medium text-primary underline underline-offset-4 hover:opacity-80"
            >
              Register now
            </button>
          </p>
        </form>
      ) : (
        /* Register Now Form */
        <form onSubmit={handleRegister} className="mt-6 space-y-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Create your account</h2>
            <p className="mt-1 text-sm text-muted-foreground">Join CampusConnect with your details.</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-name">Full Name</Label>
            <Input
              id="reg-name"
              required
              maxLength={100}
              value={regName}
              onChange={(e) => setRegName(e.target.value)}
              placeholder="Arun Kumar"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-email">Email Address</Label>
            <Input
              id="reg-email"
              type="email"
              autoComplete="email"
              required
              value={regEmail}
              onChange={(e) => setRegEmail(e.target.value)}
              placeholder="arun@college.edu"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-password">Password</Label>
            <Input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              value={regPassword}
              onChange={(e) => setRegPassword(e.target.value)}
              placeholder="Min 6 characters"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="reg-year">Year</Label>
              <SelectField
                id="reg-year"
                value={regYear}
                onChange={setRegYear}
                options={YEARS.map((y) => ({ value: String(y), label: yearLabel(y) }))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="reg-dept">Department</Label>
              <SelectField
                id="reg-dept"
                value={regDepartment}
                onChange={setRegDepartment}
                options={DEPARTMENTS.map((d) => ({ value: d, label: d }))}
              />
            </div>
          </div>

          {error ? (
            <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          <Button type="submit" size="lg" className="h-10 w-full text-sm font-medium" disabled={busy}>
            {busy ? <Spinner className="mr-2" /> : null} Register Now
          </Button>

          <p className="pt-2 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <button
              type="button"
              onClick={() => {
                setMode("login")
                setError(null)
              }}
              className="font-medium text-primary underline underline-offset-4 hover:opacity-80"
            >
              Sign in
            </button>
          </p>
        </form>
      )}
    </section>
  )
}

