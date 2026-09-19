import { Mail, GraduationCap, CalendarClock, FolderGit2, Users2 } from "lucide-react"

import { type Student, getInitials } from "@/lib/data"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

function TagList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <Badge key={item} variant="secondary">
          {item}
        </Badge>
      ))}
    </div>
  )
}

function ListSection({
  title,
  icon: Icon,
  items,
}: {
  title: string
  icon: typeof FolderGit2
  items: string[]
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2 space-y-0 pb-3">
        <Icon className="h-4 w-4 text-primary" />
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          {items.map((item) => (
            <li key={item} className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {item}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

export function ProfileView({ student }: { student: Student }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:text-left">
          <Avatar className="h-20 w-20">
            <AvatarFallback className="bg-primary/10 text-xl text-primary">
              {getInitials(student.name)}
            </AvatarFallback>
          </Avatar>
          <div className="space-y-1">
            <h1 className="text-2xl font-bold">{student.name}</h1>
            <p className="flex items-center justify-center gap-1.5 text-muted-foreground sm:justify-start">
              <GraduationCap className="h-4 w-4" />
              {student.department} · {student.year}
            </p>
            <p className="flex items-center justify-center gap-1.5 text-muted-foreground sm:justify-start">
              <Mail className="h-4 w-4" />
              {student.email}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Skills</CardTitle>
          </CardHeader>
          <CardContent>
            <TagList items={student.skills} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Interests</CardTitle>
          </CardHeader>
          <CardContent>
            <TagList items={student.interests} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <ListSection title="Events" icon={CalendarClock} items={student.events} />
        <ListSection title="Projects" icon={FolderGit2} items={student.projects} />
        <ListSection title="Clubs" icon={Users2} items={student.clubs} />
      </div>
    </div>
  )
}
