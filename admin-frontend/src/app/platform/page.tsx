import type { Metadata } from "next";

import { getSystemStatus } from "@/lib/api";

export const metadata: Metadata = { title: "Overview · Hospital Agent" };

function StatusRow({ name, ok }: { name: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between py-3">
      <dt className="text-ink">{name}</dt>
      <dd className="flex items-center gap-2 text-sm font-medium">
        <span
          className={`h-2 w-2 rounded-full ${ok ? "bg-active" : "bg-halt"}`}
          aria-hidden="true"
        />
        <span className={ok ? "text-active" : "text-halt"}>{ok ? "Operational" : "Down"}</span>
      </dd>
    </div>
  );
}

export default async function PlatformOverviewPage() {
  const status = await getSystemStatus();

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-semibold text-ink">Overview</h1>

      <section aria-labelledby="applications" className="mt-8">
        <h2 id="applications" className="text-lg font-semibold text-ink">
          Applications awaiting review
        </h2>
        <div className="mt-3 rounded-lg border border-dashed border-line bg-surface px-6 py-10">
          <p className="font-medium text-ink">No applications yet</p>
          <p className="mt-1 max-w-prose text-muted">
            When a hospital registers on the website, its application appears here. Approving it
            assigns the default plan and agent settings.
          </p>
        </div>
      </section>

      <section aria-labelledby="system" className="mt-10">
        <h2 id="system" className="text-lg font-semibold text-ink">
          System status
        </h2>
        <dl className="mt-3 divide-y divide-line rounded-lg border border-line bg-surface px-6">
          <StatusRow name="API" ok={status.api} />
          <StatusRow name="Database" ok={status.database} />
        </dl>
      </section>
    </div>
  );
}
