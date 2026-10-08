"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { UserRole } from "@/lib/types";

export const inputClass =
  "mt-1.5 block w-full rounded-md border border-line bg-surface px-3 py-2.5 text-ink " +
  "placeholder:text-muted/60 focus:border-saline focus:outline-none focus:ring-2 focus:ring-saline/25";

export const primaryButtonClass =
  "w-full rounded-md bg-saline px-4 py-2.5 font-semibold text-white transition-colors " +
  "hover:bg-saline-dark disabled:cursor-wait disabled:opacity-70";

type Props = {
  /** Only this role may sign in on this page. */
  role: UserRole;
  redirectTo: string;
  usernameLabel: string;
  usernameType?: "text" | "email";
};

export function AuthForm({ role, redirectTo, usernameLabel, usernameType = "text" }: Props) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: form.get("username"), password: form.get("password") }),
      });
      const body = await res.json().catch(() => null);

      if (res.ok && body?.role === role) {
        router.replace(redirectTo);
        router.refresh();
        return;
      }
      if (res.ok) {
        // Valid account, wrong door: don't keep a session for it here.
        await fetch("/api/auth/logout", { method: "POST" });
        setError("This account can't sign in here.");
      } else if (res.status === 401) {
        setError(`Incorrect ${usernameLabel.toLowerCase()} or password.`);
      } else if (res.status === 403 && typeof body?.detail === "string") {
        setError(body.detail);
      } else {
        setError(`Sign-in failed (error ${res.status}). Try again.`);
      }
    } catch {
      setError("Can't reach the server. Check that the backend is running on port 8000.");
    }
    setSubmitting(false);
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-5">
      <div>
        <label htmlFor="username" className="text-sm font-medium text-ink">
          {usernameLabel}
        </label>
        <input
          id="username"
          name="username"
          type={usernameType}
          autoComplete={usernameType === "email" ? "email" : "username"}
          required
          autoFocus
          className={inputClass}
        />
      </div>
      <div>
        <label htmlFor="password" className="text-sm font-medium text-ink">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className={inputClass}
        />
      </div>

      <p role="alert" aria-live="polite" className="min-h-5 text-sm text-halt">
        {error}
      </p>

      <button type="submit" disabled={submitting} className={primaryButtonClass}>
        {submitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
