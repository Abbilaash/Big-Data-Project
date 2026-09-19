"use client"

import { useState } from "react"

import { students, departments } from "@/lib/data"
import { PageHeader } from "@/components/page-header"
import { SearchBar } from "@/components/search-bar"
import { StudentCard } from "@/components/student-card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function StudentsPage() {
  const [query, setQuery] = useState("")
  const [department, setDepartment] = useState("All")

  const filtered = students.filter((student) => {
    const matchesQuery = student.name
      .toLowerCase()
      .includes(query.toLowerCase())
    const matchesDept =
      department === "All" || student.department === department
    return matchesQuery && matchesDept
  })

  return (
    <div>
      <PageHeader
        title="Students Directory"
        description="Browse students across departments and explore their profiles."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <SearchBar
          value={query}
          onChange={setQuery}
          placeholder="Search students..."
        />
        <Select value={department} onValueChange={setDepartment}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Department" />
          </SelectTrigger>
          <SelectContent>
            {departments.map((dept) => (
              <SelectItem key={dept} value={dept}>
                {dept === "All" ? "All Departments" : dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((student) => (
            <StudentCard key={student.id} student={student} />
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-muted-foreground">
          No students found. Try a different search or department.
        </p>
      )}
    </div>
  )
}
