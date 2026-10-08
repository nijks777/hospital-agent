import Link from "next/link";
import type { ReactNode } from "react";

import { LogoMark } from "@/components/logo";

type Props = {
  aside: ReactNode;
  title: string;
  subtitle: string;
  children: ReactNode;
};

/** Split screen used by both sign-in pages: brand panel on the left, form on the right. */
export function AuthShell({ aside, title, subtitle, children }: Props) {
  return (
    <main className="grid min-h-screen lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <section className="flex flex-col bg-scrub px-6 py-8 text-ward sm:px-12 lg:py-12">
        <Link href="/" className="flex items-center gap-2.5 self-start">
          <LogoMark />
          <span className="text-lg font-semibold tracking-tight">Hospital Agent</span>
        </Link>
        <div className="my-12 max-w-md lg:my-auto">{aside}</div>
      </section>

      <section className="flex items-center justify-center px-6 py-12 sm:px-12">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold text-ink">{title}</h2>
          <p className="mt-2 text-muted">{subtitle}</p>
          {children}
        </div>
      </section>
    </main>
  );
}
