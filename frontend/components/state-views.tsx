"use client"

import type { LucideIcon } from "lucide-react"
import { AlertCircle, Inbox, Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ApiError } from "@/lib/api"

export function Spinner({ className, label = "Loading" }: { className?: string; label?: string }) {
  return (
    <span role="status" className="inline-flex items-center">
      <Loader2 className={cn("h-4 w-4 animate-spin", className)} aria-hidden />
      <span className="sr-only">{label}</span>
    </span>
  )
}

export function PageLoading({ label = "Initialising…" }: { label?: string }) {
  return (
    <div role="status" className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="h-5 w-5 animate-spin text-signal" aria-hidden />
      <p className="font-mono text-sm lowercase tracking-wide">{label}</p>
    </div>
  )
}

export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Loading content">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-64 animate-pulse rounded-xl border bg-muted/50" />
      ))}
    </div>
  )
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading content">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-16 animate-pulse rounded-xl border bg-muted/50" />
      ))}
    </div>
  )
}

export function ErrorState({
  error,
  onRetry,
  title,
  className,
}: {
  error: ApiError | Error | null
  onRetry?: () => void
  title?: string
  className?: string
}) {
  const network = (error as ApiError | null)?.status === 0
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center",
        className,
      )}
    >
      <AlertCircle className="h-8 w-8 text-destructive" aria-hidden />
      <div>
        <p className="font-medium">{title ?? (network ? "Server unreachable" : "Couldn't load this")}</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {error?.message ?? "Something went wrong. Please try again."}
        </p>
      </div>
      {onRetry ? (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw className="h-4 w-4" aria-hidden /> Try again
        </Button>
      ) : null}
    </div>
  )
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 rounded-xl border border-dashed px-6 py-12 text-center",
        className,
      )}
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <p className="font-medium">{title}</p>
      {description ? <p className="max-w-sm text-sm text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  )
}
