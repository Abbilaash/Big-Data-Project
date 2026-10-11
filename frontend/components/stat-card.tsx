import type { LucideIcon } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"

type StatCardProps = {
  label: string
  value: number | string
  icon: LucideIcon
}

/** Large numeral with a small mono caption (display-type stat block). */
export function StatCard({ label, value, icon: Icon }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-3 p-5">
        <div className="min-w-0">
          <p className="text-4xl font-bold leading-none tracking-tight tabular-nums">{value}</p>
          <p className="mt-3 font-mono text-xs lowercase tracking-wider text-muted-foreground">{label}</p>
        </div>
        <Icon className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
      </CardContent>
    </Card>
  )
}
