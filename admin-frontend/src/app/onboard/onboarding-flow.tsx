"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

import { inputClass, primaryButtonClass } from "@/components/auth-form";

type Stage = "details" | "verify" | "done";

const FIELDS = [
  { name: "hospital_name", label: "Hospital name", type: "text", autoComplete: "organization" },
  { name: "city", label: "City", type: "text", autoComplete: "address-level2" },
  { name: "contact_name", label: "Your name", type: "text", autoComplete: "name" },
  { name: "email", label: "Work email", type: "email", autoComplete: "email" },
  { name: "phone", label: "Phone", type: "tel", autoComplete: "tel" },
  { name: "password", label: "Password", type: "password", autoComplete: "new-password" },
] as const;

type FieldName = (typeof FIELDS)[number]["name"];

// Friendly messages for the backend's 422 validation errors, per field.
const FIELD_HINTS: Record<FieldName, string> = {
  hospital_name: "Enter your hospital's name.",
  city: "Enter the city.",
  contact_name: "Enter your name.",
  email: "Enter a valid email address.",
  phone: "Enter a phone number, e.g. +91 98765 43210.",
  password: "Use at least 8 characters.",
};

const RESEND_COOLDOWN_SECONDS = 60;

async function postJson(path: string, body: unknown) {
  const res = await fetch(`/api/onboarding/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => null);
  return { res, data };
}

function StepLabel({ step, title }: { step: number; title: string }) {
  return (
    <>
      <p className="text-sm font-medium text-muted">Step {step} of 2</p>
      <h1 className="mt-1 text-3xl font-semibold text-scrub">{title}</h1>
    </>
  );
}

export function OnboardingFlow() {
  const [stage, setStage] = useState<Stage>("details");
  const [email, setEmail] = useState("");
  const [hospitalName, setHospitalName] = useState("");

  if (stage === "details") {
    return (
      <DetailsStep
        onRegistered={(registeredEmail, name) => {
          setEmail(registeredEmail);
          setHospitalName(name);
          setStage("verify");
        }}
      />
    );
  }
  if (stage === "verify") {
    return <VerifyStep email={email} onVerified={() => setStage("done")} />;
  }
  return (
    <div>
      <h1 className="text-3xl font-semibold text-scrub">Application submitted</h1>
      <p className="mt-4 text-muted">
        Your email is verified. We&apos;ll review {hospitalName}&apos;s application; once it&apos;s
        approved you can sign in with <span className="font-semibold text-ink">{email}</span>.
      </p>
      <Link
        href="/login"
        className="mt-8 inline-block rounded-md bg-saline px-5 py-3 font-semibold text-white hover:bg-saline-dark"
      >
        Go to sign in
      </Link>
    </div>
  );
}

function DetailsStep({ onRegistered }: { onRegistered: (email: string, name: string) => void }) {
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});
    setSubmitting(true);
    const values = Object.fromEntries(new FormData(event.currentTarget)) as Record<
      FieldName,
      string
    >;

    try {
      const { res, data } = await postJson("register", values);
      if (res.ok) {
        onRegistered(data.email, values.hospital_name);
        return;
      }
      if (res.status === 422 && Array.isArray(data?.detail)) {
        const errors: Partial<Record<FieldName, string>> = {};
        for (const item of data.detail) {
          const field = item.loc?.[1] as FieldName | undefined;
          if (field && field in FIELD_HINTS) errors[field] = FIELD_HINTS[field];
        }
        setFieldErrors(errors);
      } else {
        setError(typeof data?.detail === "string" ? data.detail : "Registration failed. Try again.");
      }
    } catch {
      setError("Can't reach the server. Check your connection and try again.");
    }
    setSubmitting(false);
  }

  return (
    <>
      <StepLabel step={1} title="Register your hospital" />
      <p className="mt-3 text-muted">
        We&apos;ll send a code to your email to confirm it&apos;s you. Your application is reviewed
        before your agent goes live.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 grid gap-5 sm:grid-cols-2">
        {FIELDS.map((f) => (
          <div
            key={f.name}
            className={f.name === "hospital_name" || f.name === "email" ? "sm:col-span-2" : ""}
          >
            <label htmlFor={f.name} className="text-sm font-medium text-ink">
              {f.label}
            </label>
            <input
              id={f.name}
              name={f.name}
              type={f.type}
              autoComplete={f.autoComplete}
              required
              minLength={f.name === "password" ? 8 : undefined}
              aria-invalid={Boolean(fieldErrors[f.name])}
              aria-describedby={fieldErrors[f.name] ? `${f.name}-error` : undefined}
              className={`${inputClass} ${fieldErrors[f.name] ? "border-halt" : ""}`}
            />
            {f.name === "password" && !fieldErrors.password && (
              <p className="mt-1 text-xs text-muted">At least 8 characters.</p>
            )}
            {fieldErrors[f.name] && (
              <p id={`${f.name}-error`} className="mt-1 text-sm text-halt">
                {fieldErrors[f.name]}
              </p>
            )}
          </div>
        ))}

        <p role="alert" aria-live="polite" className="text-sm text-halt sm:col-span-2">
          {error}
        </p>

        <button type="submit" disabled={submitting} className={`${primaryButtonClass} sm:col-span-2`}>
          {submitting ? "Sending code…" : "Send verification code"}
        </button>
      </form>
    </>
  );
}

function VerifyStep({ email, onVerified }: { email: string; onVerified: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    const code = String(new FormData(event.currentTarget).get("code") ?? "").trim();

    try {
      const { res, data } = await postJson("verify-email", { email, code });
      if (res.ok) {
        onVerified();
        return;
      }
      setError(
        res.status === 422
          ? "Enter the 6-digit code from the email."
          : typeof data?.detail === "string"
            ? data.detail
            : "Verification failed. Try again.",
      );
    } catch {
      setError("Can't reach the server. Check your connection and try again.");
    }
    setSubmitting(false);
  }

  async function handleResend() {
    setError(null);
    setNotice(null);
    try {
      const { res, data } = await postJson("resend-code", { email });
      if (res.ok) {
        setNotice("A new code is on its way. Earlier codes no longer work.");
        setCooldown(RESEND_COOLDOWN_SECONDS);
      } else {
        const retryAfter = Number(res.headers.get("Retry-After"));
        if (retryAfter > 0) setCooldown(retryAfter);
        setError(typeof data?.detail === "string" ? data.detail : "Couldn't send a new code.");
      }
    } catch {
      setError("Can't reach the server. Check your connection and try again.");
    }
  }

  return (
    <>
      <StepLabel step={2} title="Check your email" />
      <p className="mt-3 text-muted">
        We sent a 6-digit code to <span className="font-semibold text-ink">{email}</span>. It
        expires in 10 minutes.
      </p>

      <form onSubmit={handleVerify} className="mt-8 max-w-sm space-y-5">
        <div>
          <label htmlFor="code" className="text-sm font-medium text-ink">
            Verification code
          </label>
          <input
            id="code"
            name="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="\d{6}"
            maxLength={6}
            required
            autoFocus
            className={`${inputClass} text-center text-2xl tracking-[0.5em]`}
          />
        </div>

        <p role="alert" aria-live="polite" className="min-h-5 text-sm">
          {error && <span className="text-halt">{error}</span>}
          {notice && <span className="text-active">{notice}</span>}
        </p>

        <button type="submit" disabled={submitting} className={primaryButtonClass}>
          {submitting ? "Verifying…" : "Verify email"}
        </button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Didn&apos;t get it? Check spam, or{" "}
        {cooldown > 0 ? (
          <span>send a new code in {cooldown}s.</span>
        ) : (
          <button
            type="button"
            onClick={handleResend}
            className="font-semibold text-saline hover:underline"
          >
            send a new code
          </button>
        )}
      </p>
    </>
  );
}
