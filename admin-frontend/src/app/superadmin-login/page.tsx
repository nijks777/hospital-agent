import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { getCurrentUser } from "@/lib/api";

export const metadata: Metadata = {
  title: "Platform sign in · Hospital Agent",
  robots: { index: false }, // keep the admin door out of search results
};

const lifecycle = [
  { title: "A hospital applies", body: "They register and verify their email on our website." },
  { title: "You review it", body: "Approve to assign the default plan and agent settings." },
  { title: "Their agent goes live", body: "One line of code puts it on the hospital's website." },
];

export default async function SuperadminLoginPage() {
  const user = await getCurrentUser();
  if (user?.role === "platform_admin") redirect("/platform");

  return (
    <AuthShell
      title="Sign in"
      subtitle="Use your platform admin account."
      aside={
        <>
          <h1 className="text-3xl leading-tight font-semibold sm:text-4xl">
            Every hospital on the platform starts here.
          </h1>
          <ol className="mt-10 hidden sm:block">
            {lifecycle.map((step, i) => (
              <li key={step.title} className="relative flex gap-4 pb-8 last:pb-0">
                {i < lifecycle.length - 1 && (
                  <span
                    className="absolute top-7 left-[13px] h-[calc(100%-1.75rem)] w-px bg-ward/30"
                    aria-hidden="true"
                  />
                )}
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-ward/50 text-sm font-semibold">
                  {i + 1}
                </span>
                <div>
                  <p className="font-semibold">{step.title}</p>
                  <p className="mt-1 text-sm text-ward/75">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </>
      }
    >
      <AuthForm role="platform_admin" redirectTo="/platform" usernameLabel="Username" />
    </AuthShell>
  );
}
