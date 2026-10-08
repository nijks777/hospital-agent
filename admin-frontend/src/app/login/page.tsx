import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { getCurrentUser } from "@/lib/api";

export const metadata: Metadata = { title: "Hospital sign in · Hospital Agent" };

export default async function HospitalLoginPage() {
  const user = await getCurrentUser();
  if (user?.role === "hospital_admin") redirect("/portal");

  return (
    <AuthShell
      title="Sign in to your hospital"
      subtitle="Use the email you registered with."
      aside={
        <>
          <h1 className="text-3xl leading-tight font-semibold sm:text-4xl">
            Your hospital&apos;s receptionist, managed from one place.
          </h1>
          <p className="mt-6 text-ward/75">
            Update doctors and timings, check bookings, and see what patients asked.
          </p>
        </>
      }
    >
      <AuthForm
        role="hospital_admin"
        redirectTo="/portal"
        usernameLabel="Email"
        usernameType="email"
      />
      <p className="mt-6 text-sm text-muted">
        New to Hospital Agent?{" "}
        <Link href="/onboard" className="font-semibold text-saline hover:underline">
          Register your hospital
        </Link>
      </p>
    </AuthShell>
  );
}
