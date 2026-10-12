import { Eyebrow, TerminalLine } from "@/components/brand"
import { LandingSections } from "@/components/landing-sections"
import { SignInCard } from "@/components/sign-in-card"

export default function RegisterPage() {
  return (
    <div className="relative">
      <div aria-hidden className="grid-bg pointer-events-none absolute inset-x-0 -top-8 h-[34rem] -z-10" />

      <div className="grid items-center gap-12 pt-6 lg:grid-cols-[1.25fr_1fr] lg:pt-14">
        <section>
          <Eyebrow>campusconnect // registration</Eyebrow>
          <h1 className="mt-5 text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            Join your campus network.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-muted-foreground">
            Connect with classmates, find campus events, and build your student circle.
          </p>
          <TerminalLine className="mt-8" text="student account registration ... ready" />
        </section>

        <SignInCard defaultMode="register" />
      </div>

      <LandingSections />

      <footer className="mt-24 flex flex-wrap items-center justify-between gap-2 border-t py-6 font-mono text-xs text-muted-foreground">
        <span>CampusConnect</span>
        <span>Events, ranked by your network.</span>
      </footer>
    </div>
  )
}
