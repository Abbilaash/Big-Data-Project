"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { getInitials } from "@/lib/format"
import { cn } from "@/lib/utils"

export function UserAvatar({
  name,
  src,
  className,
}: {
  name: string
  src?: string | null
  className?: string
}) {
  return (
    <Avatar className={cn("h-10 w-10", className)}>
      {src ? <AvatarImage src={src} alt="" referrerPolicy="no-referrer" /> : null}
      <AvatarFallback className="bg-primary/10 font-medium text-primary">{getInitials(name)}</AvatarFallback>
    </Avatar>
  )
}
