"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { LogOut, Menu, Plus, Shield } from "lucide-react"

import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet"
import { UserAvatar } from "@/components/user-avatar"
import { ThemeToggle } from "@/components/theme-toggle"
import { LinkButton } from "@/components/link-button"

interface NavLink {
  href: string
  label: string
}

const BASE_LINKS: NavLink[] = [
  { href: "/", label: "Home" },
  { href: "/events", label: "Events" },
  { href: "/people", label: "People" },
  { href: "/my-events", label: "My Events" },
]

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/"
  return pathname === href || pathname.startsWith(href + "/")
}

export function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { status, user, signOut } = useAuth()
  const [open, setOpen] = useState(false)

  const signedIn = status === "ready" && user !== null
  const links: NavLink[] = signedIn
    ? [...BASE_LINKS, ...(user.role === "ADMIN" ? [{ href: "/admin", label: "Admin" }] : [])]
    : []

  const handleSignOut = () => {
    setOpen(false)
    signOut()
    router.replace("/login")
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Link href={signedIn ? "/" : "/login"} className="flex items-center gap-2" aria-label="CampusConnect home">
          <span className="flex h-8 w-8 items-center justify-center rounded-md border border-foreground/30 font-mono text-xs font-bold tracking-tight">
            CC
          </span>
          <span className="text-base font-semibold tracking-tight">CampusConnect</span>
        </Link>

        {signedIn ? (
          <>
            <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={isActive(pathname, link.href) ? "page" : undefined}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                    isActive(pathname, link.href) ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                  )}
                >
                  {link.href === "/admin" ? <Shield className="h-4 w-4" aria-hidden /> : null}
                  {link.label}
                </Link>
              ))}
            </nav>

            <div className="flex items-center gap-2">
              <LinkButton className="hidden sm:inline-flex" size="lg" href="/events/new">
                <Plus className="h-4 w-4" aria-hidden /> Host event
              </LinkButton>

              <ThemeToggle className="hidden md:inline-flex" />

              <Link href="/profile" className="hidden rounded-full md:block" aria-label="Your profile">
                <UserAvatar name={user.name} src={user.profile_picture} className="h-9 w-9" />
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="hidden md:inline-flex"
                onClick={handleSignOut}
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </Button>

              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger
                  className="md:hidden"
                  render={<Button variant="outline" size="icon" aria-label="Open menu" />}
                >
                  <Menu className="h-5 w-5" />
                </SheetTrigger>
                <SheetContent side="right" className="w-72 p-4">
                  <SheetTitle className="mb-4 px-1">Menu</SheetTitle>
                  <div className="mb-4 flex items-center gap-3 px-1">
                    <UserAvatar name={user.name} src={user.profile_picture} />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{user.name}</p>
                      <p className="truncate text-xs text-muted-foreground">{user.department}</p>
                    </div>
                  </div>
                  <nav className="flex flex-col gap-1" aria-label="Mobile">
                    {[...links, { href: "/events/new", label: "Host an event" }, { href: "/profile", label: "Profile" }].map(
                      (link) => (
                        <Link
                          key={link.href}
                          href={link.href}
                          onClick={() => setOpen(false)}
                          aria-current={isActive(pathname, link.href) ? "page" : undefined}
                          className={cn(
                            "rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                            isActive(pathname, link.href)
                              ? "bg-accent text-accent-foreground"
                              : "text-muted-foreground",
                          )}
                        >
                          {link.label}
                        </Link>
                      ),
                    )}
                    <div className="mt-2 flex items-center justify-between px-3 py-1 text-sm font-medium text-muted-foreground">
                      Theme <ThemeToggle />
                    </div>
                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    >
                      <LogOut className="h-4 w-4" aria-hidden /> Sign out
                    </button>
                  </nav>
                </SheetContent>
              </Sheet>
            </div>
          </>
        ) : (
          <nav className="hidden items-center gap-1 md:flex" aria-label="Sections">
            {[
              { href: "/login#how", label: "How it works" },
              { href: "/login#signals", label: "The feed" },
              { href: "/login#compare", label: "Difference" },
            ].map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                {l.label}
              </a>
            ))}
            <ThemeToggle />
          </nav>
        )}
      </div>
    </header>
  )
}
