import Link from "next/link";

import { Logo } from "@/components/logo";

const exampleChat: { from: "patient" | "agent"; text: string }[] = [
  { from: "patient", text: "Is Dr. Mehta free on Thursday?" },
  {
    from: "agent",
    text: "Dr. Anil Mehta (Cardiology) has 10:30 am and 4:00 pm open on Thursday. Which one suits you?",
  },
  { from: "patient", text: "10:30 please. It's for my father, Ramesh Kulkarni." },
  {
    from: "agent",
    text: "Booked: Thursday 10:30 am with Dr. Mehta for Ramesh Kulkarni. Please arrive 15 minutes early at the OPD on the ground floor.",
  },
];

const capabilities = [
  {
    title: "Books, moves and cancels appointments",
    body: "It checks each doctor's real timings, so patients never land on a slot that's taken.",
  },
  {
    title: "Answers from your hospital's own information",
    body: "Visiting hours, departments, insurance desks, parking. You write it once; it answers every time.",
  },
  {
    title: "Hands emergencies to people, immediately",
    body: "Chest pain or breathing trouble skips the conversation and shows your emergency number.",
  },
];

const steps = [
  { title: "Register and verify your email", body: "Takes about two minutes." },
  { title: "We review your application", body: "You get a plan and ready-made agent settings." },
  {
    title: "Add your doctors, then paste one line",
    body: "The chat appears on your website. No developers needed.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-5 sm:px-8">
        <Link href="/" className="text-scrub">
          <Logo tone="on-light" />
        </Link>
        <nav className="flex items-center gap-2 sm:gap-4">
          <Link
            href="/login"
            className="rounded-md px-3 py-2 text-sm font-medium text-ink hover:bg-line/60"
          >
            Sign in
          </Link>
          <Link
            href="/onboard"
            className="rounded-md bg-saline px-3 py-2 text-sm font-semibold text-white hover:bg-saline-dark"
          >
            Register
          </Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pt-10 pb-20 sm:px-8 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:pt-16">
          <div>
            <h1 className="text-4xl leading-[1.1] font-semibold tracking-tight text-scrub sm:text-5xl">
              A receptionist for your hospital that never puts patients on hold.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-muted">
              Hospital Agent answers patients on your website, finds a free slot with the right
              doctor and books it, day or night.
            </p>
            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/onboard"
                className="rounded-md bg-saline px-5 py-3 text-center font-semibold text-white hover:bg-saline-dark"
              >
                Register your hospital
              </Link>
              <Link
                href="/login"
                className="rounded-md border border-scrub/25 bg-surface px-5 py-3 text-center font-semibold text-scrub hover:border-scrub/50"
              >
                Hospital admin sign in
              </Link>
            </div>
          </div>

          <figure className="rounded-2xl bg-scrub p-5 text-ward shadow-[0_24px_60px_-30px_rgba(14,59,54,0.6)] sm:p-6">
            <figcaption className="flex items-center justify-between border-b border-ward/15 pb-4 text-sm">
              <span className="font-semibold">City Care Hospital</span>
              <span className="text-ward/60">Example conversation</span>
            </figcaption>
            <ol className="mt-5 space-y-3">
              {exampleChat.map((msg, i) => (
                <li
                  key={i}
                  className={
                    msg.from === "patient"
                      ? "ml-10 rounded-xl rounded-br-sm bg-ward px-4 py-2.5 text-ink"
                      : "mr-10 rounded-xl rounded-bl-sm bg-scrub-soft px-4 py-2.5"
                  }
                >
                  <span className="sr-only">{msg.from === "patient" ? "Patient: " : "Agent: "}</span>
                  {msg.text}
                </li>
              ))}
            </ol>
          </figure>
        </section>

        <section aria-labelledby="capabilities" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
            <h2 id="capabilities" className="text-2xl font-semibold text-scrub">
              What it handles for your front desk
            </h2>
            <ul className="mt-10 grid gap-10 md:grid-cols-3">
              {capabilities.map((c) => (
                <li key={c.title} className="border-t-2 border-scrub pt-5">
                  <h3 className="font-semibold text-ink">{c.title}</h3>
                  <p className="mt-2 text-muted">{c.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section aria-labelledby="how" className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
          <h2 id="how" className="text-2xl font-semibold text-scrub">
            Getting started
          </h2>
          <ol className="mt-10 grid gap-10 md:grid-cols-3">
            {steps.map((s, i) => (
              <li key={s.title} className="flex gap-4">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-scrub text-sm font-semibold text-ward">
                  {i + 1}
                </span>
                <div>
                  <h3 className="font-semibold text-ink">{s.title}</h3>
                  <p className="mt-1 text-muted">{s.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <Link
            href="/onboard"
            className="mt-12 inline-block rounded-md bg-saline px-5 py-3 font-semibold text-white hover:bg-saline-dark"
          >
            Register your hospital
          </Link>
        </section>
      </main>

      <footer className="border-t border-line">
        <p className="mx-auto max-w-6xl px-4 py-6 text-sm text-muted sm:px-8">
          Hospital Agent. The agent never gives medical advice; it books, informs and escalates.
        </p>
      </footer>
    </div>
  );
}
