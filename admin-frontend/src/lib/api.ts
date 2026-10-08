import "server-only";

import { cookies } from "next/headers";

import type { User } from "./types";

export type { User, UserRole } from "./types";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
export const AUTH_COOKIE = "access_token";

/** The signed-in user, or null if there is no valid session. */
export async function getCurrentUser(): Promise<User | null> {
  const token = (await cookies()).get(AUTH_COOKIE)?.value;
  if (!token) return null;

  const res = await fetch(`${BACKEND_URL}/auth/me`, {
    headers: { cookie: `${AUTH_COOKIE}=${token}` },
    cache: "no-store",
  });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`/auth/me failed with ${res.status}`);
  return res.json();
}

export type SystemStatus = { api: boolean; database: boolean };

export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const res = await fetch(`${BACKEND_URL}/health/ready`, { cache: "no-store" });
    return { api: true, database: res.ok };
  } catch {
    return { api: false, database: false };
  }
}
