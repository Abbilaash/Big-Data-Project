import type { LucideIcon } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"

type StatCardProps = {
  label: string
  value: number | string
  icon: LucideIcon
}

export function StatCard({ label, value, icon: Icon }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 p-4 sm:flex-row sm:items-center sm:gap-4 sm:p-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary sm:h-11 sm:w-11">
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="text-2xl font-bold leading-none">{value}</p>
          <p className="mt-1 text-sm leading-snug text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}
