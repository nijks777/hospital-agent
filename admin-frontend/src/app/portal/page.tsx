import type { Metadata } from "next";

export const metadata: Metadata = { title: "Your hospital · Hospital Agent" };

export default function PortalHomePage() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold text-ink">Your hospital is approved</h1>
      <p className="mt-2 max-w-prose text-muted">
        Next you&apos;ll add departments, doctors and their timings, then copy one line of code
        onto your website to switch the receptionist on.
      </p>
    </div>
  );
}
