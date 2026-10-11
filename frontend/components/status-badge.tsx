import { CheckCircle2, Clock, XCircle } from "lucide-react"

import { cn } from "@/lib/utils"
import type { EventStatus } from "@/lib/types"

const STYLES: Record<EventStatus, { label: string; className: string; Icon: typeof Clock }> = {
  pending: {
    label: "Pending review",
    className: "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/30",
    Icon: Clock,
  },
  approved: {
    label: "Approved",
    className: "bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/30",
    Icon: CheckCircle2,
  },
  rejected: {
    label: "Rejected",
    className: "bg-red-50 text-red-800 ring-red-600/20 dark:bg-red-400/10 dark:text-red-300 dark:ring-red-400/30",
    Icon: XCircle,
  },
}

export function StatusBadge({ status, className }: { status: EventStatus; className?: string }) {
  const { label, className: tone, Icon } = STYLES[status]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        tone,
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {label}
    </span>
  )
}
