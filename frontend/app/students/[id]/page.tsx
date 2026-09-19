import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft } from "lucide-react"

import { students } from "@/lib/data"
import { Button } from "@/components/ui/button"
import { ProfileView } from "@/components/profile-view"

export default async function StudentProfilePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const student = students.find((s) => s.id === id)

  if (!student) {
    notFound()
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          nativeButton={false}
          render={<Link href="/students" />}
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Students
        </Button>
        <Button>Connect</Button>
      </div>

      <ProfileView student={student} />
    </div>
  )
}
