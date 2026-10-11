import Link from "next/link"

import { cn } from "@/lib/utils"

export interface RankedItem {
  id: string
  label: string
  value: number
  href?: string
}

/**
 * Single-series horizontal bars for comparing magnitude.
 *
 * Follows the dataviz mark spec: bars are capped thin (<= 24px), grow from one
 * baseline with a rounded data-end, use ONE hue (identity is the label, so no
 * legend), and carry the value at the bar tip in text ink — never in the
 * series color. The list itself is the accessible table view.
 */
export function RankedBars({
  items,
  unit,
  emptyLabel = "No data yet.",
  className,
}: {
  items: RankedItem[]
  /** Singular noun for the tooltip, e.g. "event". */
  unit: string
  emptyLabel?: string
  className?: string
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>
  }
  const max = Math.max(...items.map((i) => i.value), 1)

  return (
    <ul className={cn("space-y-3", className)}>
      {items.map((item) => {
        const pct = Math.max((item.value / max) * 100, 1.5)
        const title = `${item.label}: ${item.value} ${unit}${item.value === 1 ? "" : "s"}`
        const label = item.href ? (
          <Link href={item.href} className="truncate hover:underline">
            {item.label}
          </Link>
        ) : (
          <span className="truncate">{item.label}</span>
        )
        return (
          <li key={item.id} title={title} className="grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-3 text-sm sm:grid-cols-[minmax(0,12rem)_1fr_auto]">
            {label}
            <span className="h-5 rounded-r-[4px] bg-primary/10" aria-hidden>
              <span
                className="block h-full rounded-r-[4px] bg-primary"
                style={{ width: `${pct}%` }}
              />
            </span>
            <span className="min-w-[2ch] text-right font-medium tabular-nums">{item.value}</span>
          </li>
        )
      })}
    </ul>
  )
}
