import { redirect } from "next/navigation";

import { Logo } from "@/components/logo";
import { SignOutButton } from "@/components/sign-out-button";
import { getCurrentUser } from "@/lib/api";

export default async function PortalLayout({ children }: LayoutProps<"/portal">) {
  const user = await getCurrentUser();
  if (!user || user.role !== "hospital_admin") redirect("/login");

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between gap-3 bg-scrub px-4 py-3 text-ward sm:px-8">
        <Logo />
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-ward/75 sm:inline">{user.email}</span>
          <SignOutButton redirectTo="/login" />
        </div>
      </header>
      <main className="px-4 py-8 sm:px-8 lg:px-12">{children}</main>
    </div>
  );
}
