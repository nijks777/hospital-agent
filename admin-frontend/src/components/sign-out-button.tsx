"use client";

import { useRouter } from "next/navigation";

export function SignOutButton({ redirectTo }: { redirectTo: string }) {
  const router = useRouter();

  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace(redirectTo);
    router.refresh();
  }

  return (
    <button
      type="button"
      onClick={signOut}
      className="rounded-md px-3 py-1.5 text-sm font-medium text-muted hover:bg-line/60 hover:text-ink"
    >
      Sign out
    </button>
  );
}
