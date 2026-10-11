// End-to-end browser scenario for CampusConnect.
//
// Drives the real frontend against a real backend. It expects a FRESH backend
// (it creates asha@/bala@/admin@campus.local and assumes ADMIN_EMAIL is
// admin@campus.local with ENABLE_DEV_LOGIN=true). See e2e/README.md.
import { chromium } from "playwright-core"
import fs from "node:fs"
import path from "node:path"

const BASE = process.env.BASE_URL ?? "http://localhost:3000"
const SHOTS = path.join(import.meta.dirname, "shots")
fs.mkdirSync(SHOTS, { recursive: true })

const results = []
const consoleProblems = []

let currentPage = null
async function step(name, fn) {
  try {
    await fn()
    results.push({ name, ok: true })
    console.log("PASS  " + name)
  } catch (err) {
    results.push({ name, ok: false, err: String(err).split("\n")[0] })
    console.log("FAIL  " + name + "\n      " + String(err).split("\n").slice(0, 3).join("\n      "))
  }
}

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  channel: process.env.CHROME_PATH ? undefined : "chrome",
  headless: true,
})

async function newUser(label, viewport = { width: 1280, height: 900 }) {
  const ctx = await browser.newContext({ viewport })
  // Optional: send the app's API calls to a different backend (e.g. the mock
  // harness on :8001) without rebuilding the frontend. Format: "8000:8001".
  if (process.env.API_PORT_REWRITE) {
    const [from, to] = process.env.API_PORT_REWRITE.split(":")
    await ctx.route(`http://localhost:${from}/**`, (r) =>
      r.continue({ url: r.request().url().replace(`localhost:${from}`, `localhost:${to}`) }),
    )
  }
  const page = await ctx.newPage()
  page.setDefaultTimeout(8000)
  const origGoto = page.goto.bind(page)
  page.goto = async (...a) => { currentPage = page; return origGoto(...a) }
  page.on("console", (m) => {
    if (m.type() === "error") consoleProblems.push(`[${label}] console: ${m.text().slice(0, 200)}`)
  })
  page.on("pageerror", (e) => consoleProblems.push(`[${label}] pageerror: ${String(e).slice(0, 200)}`))
  return { ctx, page }
}

async function devLogin(page, email, name) {
  await page.goto(BASE + "/login")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Name").fill(name)
  await page.getByRole("button", { name: /Sign in \(development\)/ }).click()
}

async function completeProfile(page, year, dept) {
  await page.waitForURL("**/complete-profile")
  await page.locator("#year").click()
  await page.getByRole("option", { name: year }).click()
  await page.locator("#department").click()
  await page.getByRole("option", { name: dept, exact: true }).click()
  await page.getByRole("button", { name: "Continue" }).click()
  await page.waitForURL(BASE + "/")
}

const future = new Date(Date.now() + 10 * 86400000).toISOString().slice(0, 10)

// ---------------------------------------------------------------- anonymous
const anon = await newUser("anon")
await step("unauthenticated visit to / redirects to /login", async () => {
  await anon.page.goto(BASE + "/")
  await anon.page.waitForURL("**/login")
})
await step("login page shows Google button and dev sign-in", async () => {
  await anon.page.getByRole("link", { name: /Continue with Google/ }).waitFor()
  await anon.page.getByRole("button", { name: /Sign in \(development\)/ }).waitFor()
  await anon.page.screenshot({ path: path.join(SHOTS, "01-login.png") })
})
await step("OAuth error fragment is displayed and stripped from URL", async () => {
  await anon.page.goto("about:blank")
  await anon.page.goto(BASE + "/login#error=Sign-in+session+expired")
  await anon.page.getByRole("alert").filter({ hasText: "Sign-in session expired" }).waitFor()
  if (anon.page.url().includes("#")) throw new Error("fragment still in URL")
})
await step("old /students route redirects to /people (then login)", async () => {
  await anon.page.goto(BASE + "/students")
  await anon.page.waitForURL(/\/(login|people)/)
})

// ------------------------------------------------------------------- host
const asha = await newUser("asha")
await step("Asha: dev login -> forced onboarding", async () => {
  await devLogin(asha.page, "asha@campus.local", "Asha Raman")
  await asha.page.waitForURL("**/complete-profile")
})
await step("Asha: onboarding validation blocks empty selection", async () => {
  await asha.page.getByRole("button", { name: "Continue" }).click()
  await asha.page.getByText("Please choose your year.").waitFor()
})
await step("Asha: completes profile and lands on dashboard", async () => {
  await completeProfile(asha.page, "3rd year", "CSE")
  await asha.page.getByRole("heading", { name: /Welcome back, Asha/ }).waitFor()
})
await step("Asha: dashboard empty states render", async () => {
  await asha.page.getByText("No upcoming events yet").waitFor()
  await asha.page.screenshot({ path: path.join(SHOTS, "02-dashboard-empty.png"), fullPage: true })
})
await step("Asha: host-event form rejects invalid input client-side", async () => {
  await asha.page.goto(BASE + "/events/new")
  await asha.page.getByRole("button", { name: "Submit for review" }).click()
  await asha.page.getByText("Give your event a title").waitFor()
  await asha.page.getByLabel("Title").fill("AI Hackathon")
  await asha.page.getByLabel("Registration link (optional)").fill("javascript:alert(1)")
  await asha.page.getByRole("button", { name: "Submit for review" }).click()
  await asha.page.getByText("Enter a full http(s) link.").waitFor()
})
await step("Asha: submits a valid event -> pending in My Events", async () => {
  await asha.page.getByLabel("Registration link (optional)").fill("")
  await asha.page.locator("#category").click()
  await asha.page.getByRole("option", { name: "Hackathon" }).click()
  await asha.page.getByLabel("Venue").fill("Main Auditorium")
  await asha.page.getByLabel("Date").fill(future)
  await asha.page.getByLabel("Starts").fill("09:00")
  await asha.page.getByLabel("Ends").fill("17:30")
  await asha.page.getByLabel("Description").fill("Build something with machine learning in 24 hours.")
  await asha.page.getByLabel("Tags (optional)").fill("ai, python")
  await asha.page.screenshot({ path: path.join(SHOTS, "03-host-form.png"), fullPage: true })
  await asha.page.getByRole("button", { name: "Submit for review" }).click()
  await asha.page.waitForURL("**/my-events?tab=hosted")
  await asha.page.getByText("AI Hackathon").waitFor()
  await asha.page.getByText("Pending review").first().waitFor()
})
await step("public events list does not show the pending event", async () => {
  await asha.page.goto(BASE + "/events")
  await asha.page.getByText("No events yet").waitFor()
})

// ------------------------------------------------------------------ admin
const admin = await newUser("admin")
await step("Admin: signs in with ADMIN_EMAIL and sees Admin nav", async () => {
  await devLogin(admin.page, "admin@campus.local", "Admin User")
  await completeProfile(admin.page, "4th year", "IT")
  await admin.page.getByRole("link", { name: "Admin" }).first().waitFor()
})
await step("Admin: pending event is in the queue and can be approved", async () => {
  await admin.page.goto(BASE + "/admin")
  await admin.page.getByRole("heading", { name: "AI Hackathon" }).waitFor()
  await admin.page.screenshot({ path: path.join(SHOTS, "04-admin-queue.png"), fullPage: true })
  await admin.page.getByRole("button", { name: "Approve" }).click()
  await admin.page.getByText("The queue is clear").waitFor()
})
await step("Non-admin cannot see the admin console", async () => {
  await asha.page.goto(BASE + "/admin")
  await asha.page.getByText("Administrators only").waitFor()
})

// --------------------------------------------------------------- attendee
const bala = await newUser("bala")
await step("Bala: signs up and completes profile", async () => {
  await devLogin(bala.page, "bala@campus.local", "Bala Kumar")
  await completeProfile(bala.page, "2nd year", "ECE")
})
await step("Bala: approved event shows in list with category filter + search", async () => {
  await bala.page.goto(BASE + "/events")
  await bala.page.getByRole("heading", { name: "AI Hackathon" }).waitFor()
  await bala.page.getByPlaceholder(/Search by title/).fill("zzzz-no-match")
  await bala.page.getByText("No events match your filters").waitFor()
  await bala.page.getByRole("button", { name: "Clear filters" }).click()
  await bala.page.getByRole("heading", { name: "AI Hackathon" }).waitFor()
})
await step("Bala: registers and likes from the card (optimistic, persisted)", async () => {
  await bala.page.getByRole("button", { name: "Register" }).click()
  await bala.page.getByRole("button", { name: /Registered/ }).waitFor()
  await bala.page.getByRole("button", { name: /^Like/ }).click()
  await bala.page.getByRole("button", { name: /^Unlike/ }).waitFor()
  await bala.page.reload()
  await bala.page.getByRole("button", { name: /Registered/ }).waitFor()
  await bala.page.getByRole("button", { name: /^Unlike \(1 likes\)/ }).waitFor()
})
await step("Bala: event detail shows counts, posts and deletes a comment", async () => {
  await bala.page.getByRole("link", { name: "Details" }).click()
  await bala.page.getByRole("heading", { name: "AI Hackathon", level: 1 }).waitFor()
  await bala.page.getByText("1 registration").first().waitFor()
  await bala.page.getByLabel("Add a comment").fill("Count me in!")
  await bala.page.getByRole("button", { name: "Post comment" }).click()
  await bala.page.getByText("Count me in!").waitFor()
  await bala.page.screenshot({ path: path.join(SHOTS, "05-event-detail.png"), fullPage: true })
  await bala.page.getByRole("button", { name: "Delete comment" }).click()
  await bala.page.getByText("No comments yet").waitFor()
})
await step("Bala: follows Asha from the People directory", async () => {
  await bala.page.goto(BASE + "/people")
  await bala.page.getByRole("link", { name: "Asha Raman" }).first().waitFor()
  await bala.page.getByRole("button", { name: "Follow Asha Raman" }).click()
  await bala.page.getByRole("button", { name: "Following Asha Raman" }).waitFor()
  await bala.page.screenshot({ path: path.join(SHOTS, "06-people.png"), fullPage: true })
})
await step("Bala: Asha's profile shows 1 follower and following state", async () => {
  await bala.page.getByRole("link", { name: "Asha Raman" }).first().click()
  await bala.page.getByRole("button", { name: "Following Asha Raman" }).waitFor()
  await bala.page.getByText("followers").first().waitFor()
})

// ------------------------------------------------- social feed (the point)
await step("Asha follows Bala, then feed explains 'Bala Kumar registered for this event'", async () => {
  await asha.page.goto(BASE + "/people")
  await asha.page.getByRole("link", { name: "Bala Kumar" }).first().waitFor()
  await asha.page.getByRole("button", { name: "Follow Bala Kumar" }).click()
  await asha.page.getByRole("button", { name: "Following Bala Kumar" }).waitFor()
  await asha.page.goto(BASE + "/")
  await asha.page.getByText("Bala Kumar registered for this event").waitFor()
  await asha.page.screenshot({ path: path.join(SHOTS, "07-dashboard-feed.png"), fullPage: true })
})
await step("Asha: profile lists Bala as follower and common interests work", async () => {
  await asha.page.goto(BASE + "/profile")
  await asha.page.getByRole("heading", { name: "Asha Raman" }).waitFor()
  await asha.page.getByText("Bala Kumar").first().waitFor()
})
await step("Asha: edits profile through the dialog", async () => {
  await asha.page.getByRole("button", { name: "Edit profile" }).click()
  await asha.page.getByLabel("Name", { exact: true }).fill("Asha R. Raman")
  await asha.page.getByRole("button", { name: "Save changes" }).click()
  await asha.page.getByRole("heading", { name: "Asha R. Raman" }).waitFor()
})
await step("Bala: My Events lists the registration", async () => {
  await bala.page.goto(BASE + "/my-events")
  await bala.page.getByRole("heading", { name: "AI Hackathon" }).waitFor()
})
await step("Admin: analytics tab renders both Mongo and graph sections", async () => {
  await admin.page.goto(BASE + "/admin")
  await admin.page.getByRole("tab", { name: "Analytics" }).click()
  await admin.page.getByText("Approved events by category").waitFor()
  await admin.page.getByText("Most followed students").waitFor()
  await admin.page.screenshot({ path: path.join(SHOTS, "08-admin-analytics.png"), fullPage: true })
})

// -------------------------------------------------------------- robustness
await step("Expired/invalid token is cleared and user returns to /login", async () => {
  await asha.page.evaluate(() => localStorage.setItem("cc_token", "not-a-jwt"))
  await asha.page.goto(BASE + "/events")
  await asha.page.waitForURL("**/login")
})
await step("Unknown event id shows a friendly not-found state", async () => {
  await bala.page.goto(BASE + "/events/EV_DOESNOTEXIST")
  await bala.page.getByText("Event not found").waitFor()
})
await step("Backend outage shows a recoverable error, not a blank page", async () => {
  await bala.page.route("**/api/feed**", (r) => r.abort())
  await bala.page.goto(BASE + "/")
  await bala.page.getByText("Couldn't load your feed").waitFor()
  await bala.page.unroute("**/api/feed**")
})

// ------------------------------------------------------------------ mobile
const mobile = await newUser("mobile", { width: 390, height: 800 })
await step("Mobile: dashboard has no horizontal overflow and menu opens", async () => {
  await mobile.page.goto(BASE + "/login")
  await mobile.page.getByLabel("Email").fill("bala@campus.local")
  await mobile.page.getByLabel("Name").fill("Bala Kumar")
  await mobile.page.getByRole("button", { name: /Sign in \(development\)/ }).click()
  await mobile.page.waitForURL(BASE + "/")
  await mobile.page.getByRole("heading", { name: /Welcome back/ }).waitFor()
  const overflow = await mobile.page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  if (overflow > 1) throw new Error("horizontal overflow of " + overflow + "px")
  await mobile.page.getByRole("button", { name: "Open menu" }).click()
  await mobile.page.getByRole("link", { name: "My Events" }).waitFor()
  await mobile.page.screenshot({ path: path.join(SHOTS, "09-mobile-menu.png") })
})

await browser.close()

const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} steps passed`)
if (consoleProblems.length) {
  console.log("\nBrowser console problems:")
  for (const p of [...new Set(consoleProblems)]) console.log("  " + p)
}
process.exit(failed.length ? 1 : 0)
