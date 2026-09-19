import Link from "next/link"

import { type Student, commonSkills, getInitials } from "@/lib/data"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card"

type StudentCardProps = {
  student: Student
  // Show the "connect" action and common-skill highlights (teammates page).
  showConnect?: boolean
}

export function StudentCard({ student, showConnect = false }: StudentCardProps) {
  const common = showConnect ? commonSkills(student) : []

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <Avatar className="h-12 w-12">
          <AvatarFallback className="bg-primary/10 text-primary">
            {getInitials(student.name)}
          </AvatarFallback>
        </Avatar>
        <div>
          <p className="font-semibold leading-tight">{student.name}</p>
          <p className="text-sm text-muted-foreground">
            {student.department} · {student.year}
          </p>
        </div>
      </CardHeader>

      <CardContent className="flex-1 space-y-3">
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">Skills</p>
          <div className="flex flex-wrap gap-1.5">
            {student.skills.map((skill) => (
              <Badge key={skill} variant="secondary">
                {skill}
              </Badge>
            ))}
          </div>
        </div>

        {showConnect ? (
          <div>
            <p className="mb-1.5 text-xs font-medium text-muted-foreground">
              Common skills
            </p>
            {common.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {common.map((skill) => (
                  <Badge key={skill}>{skill}</Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No skills in common</p>
            )}
          </div>
        ) : null}
      </CardContent>

      <CardFooter className="gap-2">
        <Button
          variant="outline"
          className="flex-1"
          nativeButton={false}
          render={<Link href={`/students/${student.id}`} />}
        >
          View Profile
        </Button>
        {showConnect ? <Button className="flex-1">Connect</Button> : null}
      </CardFooter>
    </Card>
  )
}
