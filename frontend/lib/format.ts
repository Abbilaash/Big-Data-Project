// Display helpers. Dates arrive as "YYYY-MM-DD" and times as "HH:MM" with no
// timezone, so they are formatted from their parts (never via `new Date(str)`,
// which would shift the day for viewers west of UTC).

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

function parseDate(iso: string): { y: number; m: number; d: number } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  if (!match) return null
  return { y: Number(match[1]), m: Number(match[2]), d: Number(match[3]) }
}

export function formatDate(iso: string): string {
  const p = parseDate(iso)
  if (!p) return iso
  const weekday = DAYS[new Date(p.y, p.m - 1, p.d).getDay()]
  return `${weekday}, ${p.d} ${MONTHS[p.m - 1]} ${p.y}`
}

export function formatShortDate(iso: string): { day: string; month: string } {
  const p = parseDate(iso)
  if (!p) return { day: "--", month: "" }
  return { day: String(p.d), month: MONTHS[p.m - 1].toUpperCase() }
}

export function formatTime(hhmm: string): string {
  const match = /^(\d{2}):(\d{2})$/.exec(hhmm)
  if (!match) return hhmm
  const h = Number(match[1])
  const suffix = h >= 12 ? "PM" : "AM"
  const h12 = h % 12 === 0 ? 12 : h % 12
  return `${h12}:${match[2]} ${suffix}`
}

export function formatTimeRange(start: string, end: string): string {
  return `${formatTime(start)} – ${formatTime(end)}`
}

export function todayLocalISO(): string {
  const now = new Date()
  const mm = String(now.getMonth() + 1).padStart(2, "0")
  const dd = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${mm}-${dd}`
}

export function isPast(dateIso: string): boolean {
  return dateIso < todayLocalISO()
}

export function formatRelative(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ""
  const seconds = Math.round((Date.now() - then) / 1000)
  if (seconds < 60) return "just now"
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

export function getInitials(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("") || "?"
  )
}

export function yearLabel(year: number | null | undefined): string {
  if (!year) return ""
  const suffix = year === 1 ? "st" : year === 2 ? "nd" : year === 3 ? "rd" : "th"
  return `${year}${suffix} year`
}

export function pluralize(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`
}
