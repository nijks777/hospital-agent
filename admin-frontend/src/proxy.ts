import { NextResponse, type NextRequest } from "next/server";

// Optimistic check only: it looks for the cookie, it doesn't verify it.
// The real check (valid token + correct role) happens in each area's layout.tsx.
const SIGN_IN_PAGE: Record<string, string> = {
  "/platform": "/superadmin-login",
  "/portal": "/login",
};

export function proxy(request: NextRequest) {
  if (request.cookies.has("access_token")) return NextResponse.next();

  const area = Object.keys(SIGN_IN_PAGE).find((prefix) =>
    request.nextUrl.pathname.startsWith(prefix),
  );
  return area
    ? NextResponse.redirect(new URL(SIGN_IN_PAGE[area], request.url))
    : NextResponse.next();
}

export const config = {
  matcher: ["/platform/:path*", "/portal/:path*"],
};
