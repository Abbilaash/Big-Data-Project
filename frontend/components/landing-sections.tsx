import { CompareCard, SectionHeading, StatBlock, StepCard } from "@/components/brand"

const STEPS = [
  { title: "Discover", body: "Search one feed of approved campus events instead of scrolling posters and group chats." },
  { title: "Register", body: "Commit in one tap. Your registration is visible to the people who follow you." },
  { title: "Follow", body: "Connect with classmates and see what they register for, share, like and view." },
  { title: "Compound", body: "The more your network does, the better your feed ranks what is worth your time." },
]

// These are the real weights the backend feed ranking uses (feed_service.py).
const SIGNALS = [
  { value: "4", caption: "a connection registered" },
  { value: "3", caption: "a connection shared it" },
  { value: "2", caption: "a connection liked it" },
  { value: "1", caption: "a connection viewed it" },
]

const COMPARISONS = [
  {
    topic: "discovery",
    before: "Posters, forwarded messages and word of mouth.",
    after: "One searchable feed, filtered by category and date.",
  },
  {
    topic: "trust",
    before: "Anyone can post anything.",
    after: "Every event is reviewed by an administrator before it is public.",
  },
  {
    topic: "relevance",
    before: "Newest first, the same for everyone.",
    after: "Ranked by what the people you follow actually did.",
  },
  {
    topic: "context",
    before: "No idea who else is going.",
    after: "Each recommendation says which connection did what.",
  },
]

export function LandingSections() {
  return (
    <div className="mt-24 space-y-24">
      <section id="how" aria-labelledby="how-title" className="scroll-mt-24">
        <SectionHeading
          eyebrow="how it works"
          title={<span id="how-title">From discovery to your network.</span>}
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <StepCard key={s.title} index={i + 1} total={STEPS.length} title={s.title}>
              {s.body}
            </StepCard>
          ))}
        </div>
      </section>

      <section id="signals" aria-labelledby="signals-title" className="scroll-mt-24">
        <SectionHeading
          eyebrow="the feed"
          title={<span id="signals-title">Your feed is ranked by signal.</span>}
          description="Events your connections interacted with are scored by what they did. These are the actual weights; stronger actions count for more."
        />
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {SIGNALS.map((s) => (
            <StatBlock key={s.caption} value={s.value} caption={s.caption} />
          ))}
        </div>
      </section>

      <section id="compare" aria-labelledby="compare-title" className="scroll-mt-24">
        <SectionHeading
          eyebrow="the difference"
          title={<span id="compare-title">Less noise. More signal.</span>}
        />
        <div className="grid gap-4 md:grid-cols-2">
          {COMPARISONS.map((c) => (
            <CompareCard key={c.topic} topic={c.topic} before={c.before} after={c.after} />
          ))}
        </div>
      </section>
    </div>
  )
}
