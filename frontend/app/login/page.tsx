import { Eyebrow, TerminalLine } from "@/components/brand"
import { LandingSections } from "@/components/landing-sections"
import { SignInCard } from "@/components/sign-in-card"

export default function LoginPage() {
  return (
    <div className="relative">
      <div aria-hidden className="grid-bg pointer-events-none absolute inset-x-0 -top-8 h-[34rem] -z-10" />

      <div className="grid items-center gap-12 pt-6 lg:grid-cols-[1.25fr_1fr] lg:pt-14">
        <section>
          <Eyebrow>campusconnect // events &amp; network</Eyebrow>
          <h1 className="mt-5 text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            A new class of campus network.
          </h1>
          <p className="mt-5 max-w-xl text-lg text-muted-foreground">
            Find the events worth showing up for, and see who else is going. Built on a social graph, not a
            guess.
          </p>
          <TerminalLine className="mt-8" text="student access requested ... ready for sign-in" />
        </section>

        <SignInCard />
      </div>

      <LandingSections />

      <footer className="mt-24 flex flex-wrap items-center justify-between gap-2 border-t py-6 font-mono text-xs text-muted-foreground">
        <span>CampusConnect</span>
        <span>Events, ranked by your network.</span>
      </footer>
    </div>
  )
}
