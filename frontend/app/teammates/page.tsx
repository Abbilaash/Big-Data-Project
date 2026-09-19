"use client"

import { useState } from "react"

import { students, allSkills } from "@/lib/data"
import { PageHeader } from "@/components/page-header"
import { SearchBar } from "@/components/search-bar"
import { StudentCard } from "@/components/student-card"
import { Badge } from "@/components/ui/badge"

export default function TeammatesPage() {
  const [query, setQuery] = useState("")
  const [activeSkills, setActiveSkills] = useState<string[]>([])

  function toggleSkill(skill: string) {
    setActiveSkills((prev) =>
      prev.includes(skill)
        ? prev.filter((s) => s !== skill)
        : [...prev, skill],
    )
  }

  const filtered = students.filter((student) => {
    const matchesQuery = student.name
      .toLowerCase()
      .includes(query.toLowerCase())
    const matchesSkills =
      activeSkills.length === 0 ||
      activeSkills.every((skill) => student.skills.includes(skill))
    return matchesQuery && matchesSkills
  })

  return (
    <div>
      <PageHeader
        title="Find Teammates"
        description="Discover students with the skills you need and connect for your next project or hackathon."
      />

      <div className="mb-4">
        <SearchBar
          value={query}
          onChange={setQuery}
          placeholder="Search students by name..."
        />
      </div>

      <div className="mb-6">
        <p className="mb-2 text-sm font-medium text-muted-foreground">
          Filter by skill
        </p>
        <div className="flex flex-wrap gap-2">
          {allSkills.map((skill) => {
            const active = activeSkills.includes(skill)
            return (
              <button
                key={skill}
                type="button"
                onClick={() => toggleSkill(skill)}
                aria-pressed={active}
                className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <Badge
                  variant={active ? "default" : "outline"}
                  className="cursor-pointer"
                >
                  {skill}
                </Badge>
              </button>
            )
          })}
        </div>
      </div>

      {filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((student) => (
            <StudentCard key={student.id} student={student} showConnect />
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-muted-foreground">
          No students match your filters. Try removing a skill or changing your
          search.
        </p>
      )}
    </div>
  )
}
