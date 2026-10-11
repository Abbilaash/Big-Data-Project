"use client"

import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"

type Theme = "dark" | "light"
const KEY = "cc_theme"

function apply(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark")
}

/**
 * Dark is the default (server-rendered on <html>). A stored "light" choice is
 * applied after mount. Storage access is guarded: it can be blocked.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>("dark")

  useEffect(() => {
    let stored: string | null = null
    try {
      stored = window.localStorage.getItem(KEY)
    } catch {
      /* ignore */
    }
    if (stored === "light") {
      setTheme("light")
      apply("light")
    }
  }, [])

  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark"
    setTheme(next)
    apply(next)
    try {
      window.localStorage.setItem(KEY, next)
    } catch {
      /* ignore */
    }
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className={className}
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  )
}
