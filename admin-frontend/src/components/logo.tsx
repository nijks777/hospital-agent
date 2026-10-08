type Tone = "on-dark" | "on-light";

const colors: Record<Tone, { bubble: string; cross: string }> = {
  "on-dark": { bubble: "var(--color-ward)", cross: "var(--color-scrub)" },
  "on-light": { bubble: "var(--color-scrub)", cross: "var(--color-ward)" },
};

/** Brand mark: a speech bubble (the agent) carrying a medical cross (the hospital). */
export function LogoMark({
  className = "h-8 w-8",
  tone = "on-dark",
}: {
  className?: string;
  tone?: Tone;
}) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <path
        d="M6 4h20a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H14l-6 5v-5H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3Z"
        fill={colors[tone].bubble}
      />
      <path d="M14 8h4v4h4v4h-4v4h-4v-4h-4v-4h4z" fill={colors[tone].cross} />
    </svg>
  );
}

export function Logo({ tone = "on-dark" }: { tone?: Tone }) {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark tone={tone} />
      <span className="text-lg font-semibold tracking-tight">Hospital Agent</span>
    </span>
  );
}
