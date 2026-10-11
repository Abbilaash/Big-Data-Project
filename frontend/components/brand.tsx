"use client"

import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

/** Small lowercase mono label that sits above a heading. */
export function Eyebrow({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p
      className={cn(
        "flex items-center gap-2 font-mono text-xs lowercase tracking-wider text-muted-foreground",
        className,
      )}
    >
      <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-signal" />
      {children}
    </p>
  )
}

/** Eyebrow + display heading + hairline rule. */
export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow: string
  title: React.ReactNode
  description?: string
  className?: string
}) {
  return (
    <div className={cn("mb-8 border-b pb-6", className)}>
      <Eyebrow>{eyebrow}</Eyebrow>
      <h2 className="mt-3 text-3xl font-bold leading-[1.1] tracking-tight sm:text-4xl">{title}</h2>
      {description ? <p className="mt-3 max-w-2xl text-muted-foreground">{description}</p> : null}
    </div>
  )
}

/** Large numeral with a small mono caption. */
export function StatBlock({
  value,
  caption,
  className,
}: {
  value: React.ReactNode
  caption: string
  className?: string
}) {
  return (
    <div className={cn("border-l pl-5", className)}>
      <p className="text-5xl font-bold leading-none tracking-tight tabular-nums sm:text-6xl">{value}</p>
      <p className="mt-3 font-mono text-xs lowercase tracking-wider text-muted-foreground">{caption}</p>
    </div>
  )
}

/** Numbered process step ("01"). */
export function StepCard({
  index,
  total,
  title,
  children,
}: {
  index: number
  total: number
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="flex h-full flex-col rounded-lg border bg-card p-6">
      <p className="font-mono text-xs tracking-wider text-muted-foreground">
        <span className="text-signal">{String(index).padStart(2, "0")}</span> / {String(total).padStart(2, "0")}
      </p>
      <h3 className="mt-10 text-xl font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{children}</p>
    </div>
  )
}

/** "The old way" vs "this app" comparison for one topic. */
export function CompareCard({
  topic,
  before,
  after,
}: {
  topic: string
  before: string
  after: string
}) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <p className="font-mono text-xs lowercase tracking-wider text-muted-foreground">{topic}</p>
      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">The old way</p>
          <p className="mt-2 text-sm text-muted-foreground line-through decoration-muted-foreground/40">{before}</p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-signal">CampusConnect</p>
          <p className="mt-2 text-sm font-medium">{after}</p>
        </div>
      </div>
    </div>
  )
}

/**
 * Terminal-style line that types itself out. Honours reduced-motion (shows the
 * full text immediately) and exposes the whole sentence to screen readers.
 */
export function TerminalLine({
  text,
  prefix = ">>>",
  className,
}: {
  text: string
  prefix?: string
  className?: string
}) {
  const [shown, setShown] = useState(0)

  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    if (reduce) {
      setShown(text.length)
      return
    }
    setShown(0)
    const id = window.setInterval(() => {
      setShown((n) => {
        if (n >= text.length) {
          window.clearInterval(id)
          return n
        }
        return n + 1
      })
    }, 28)
    return () => window.clearInterval(id)
  }, [text])

  return (
    <p className={cn("font-mono text-sm text-muted-foreground", className)} aria-label={`${prefix} ${text}`}>
      <span aria-hidden>
        <span className="text-signal">{prefix}</span> {text.slice(0, shown)}
        {shown < text.length ? <span className="caret" /> : null}
      </span>
    </p>
  )
}
