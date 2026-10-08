import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/logo";

import { OnboardingFlow } from "./onboarding-flow";

export const metadata: Metadata = { title: "Register your hospital · Hospital Agent" };

export default function OnboardPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-8">
        <Link href="/" className="text-scrub">
          <Logo tone="on-light" />
        </Link>
        <Link href="/login" className="text-sm font-medium text-muted hover:text-ink">
          Already registered? <span className="font-semibold text-saline">Sign in</span>
        </Link>
      </header>
      <main className="mx-auto max-w-xl px-4 pt-6 pb-20 sm:px-8">
        <OnboardingFlow />
      </main>
    </div>
  );
}
