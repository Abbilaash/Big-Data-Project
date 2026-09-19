import { Pencil } from "lucide-react"

import { currentUser } from "@/lib/data"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/page-header"
import { ProfileView } from "@/components/profile-view"

export default function MyProfilePage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex items-start justify-between">
        <PageHeader
          title="My Profile"
          description="This is how other students see you on CampusConnect."
        />
        <Button variant="outline">
          <Pencil className="mr-1 h-4 w-4" />
          Edit Profile
        </Button>
      </div>

      <ProfileView student={currentUser} />
    </div>
  )
}
