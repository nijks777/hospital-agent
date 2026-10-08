import { redirect } from "next/navigation";

import { Logo } from "@/components/logo";
import { SignOutButton } from "@/components/sign-out-button";
import { getCurrentUser } from "@/lib/api";

const nav = [
  { label: "Overview", href: "/platform", ready: true },
  { label: "Hospitals", href: "/platform/hospitals", ready: false },
  { label: "Plans", href: "/platform/plans", ready: false },
  { label: "Settings", href: "/platform/settings", ready: false },
];

export default async function PlatformLayout({ children }: LayoutProps<"/platform">) {
  const user = await getCurrentUser();
  if (!user || user.role !== "platform_admin") redirect("/superadmin-login");

  return (
    <div className="min-h-screen md:grid md:grid-cols-[15rem_minmax(0,1fr)]">
      <aside className="bg-scrub px-4 py-5 text-ward md:min-h-screen md:py-6">
        <div className="px-2">
          <Logo />
        </div>
        <nav aria-label="Platform" className="mt-6 flex gap-1 overflow-x-auto md:mt-10 md:flex-col">
          {nav.map((item) =>
            item.ready ? (
              <a
                key={item.label}
                href={item.href}
                aria-current="page"
                className="rounded-md bg-scrub-soft px-3 py-2 font-medium whitespace-nowrap"
              >
                {item.label}
              </a>
            ) : (
              <span
                key={item.label}
                aria-disabled="true"
                className="flex items-center justify-between gap-3 rounded-md px-3 py-2 whitespace-nowrap text-ward/50"
              >
                {item.label}
                <span className="text-xs">Soon</span>
              </span>
            ),
          )}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="flex items-center justify-end gap-3 border-b border-line bg-surface px-4 py-3 sm:px-8">
          <span className="text-sm text-muted">
            Signed in as <span className="font-semibold text-ink">{user.username}</span>
          </span>
          <SignOutButton redirectTo="/superadmin-login" />
        </header>
        <main className="px-4 py-8 sm:px-8 lg:px-12">{children}</main>
      </div>
    </div>
  );
}
