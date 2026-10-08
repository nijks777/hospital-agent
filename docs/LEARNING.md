# Learning Log

Revision notes for interviews. One entry per step, newest last.

---

## Step 0 — Choosing the stack

**Decisions**
- **uv** for Python packages: fast, lock file (`uv.lock`) for reproducible installs, also manages Python versions.
- **LangGraph** for orchestration: a call is a *stateful flow* (greet → intent → check slots → confirm → book),
  with checkpoints (resume a dropped call) and interrupts (hand over to a human).
- **PostgreSQL (SQL), not NoSQL**: appointments need transactions + unique constraints so two callers can't book
  the same slot. One DB also covers vectors (pgvector) and agent memory (LangGraph checkpointer).
- **LiveKit / Vapi are NOT orchestration** — they are the voice layer ("ears and mouth"). LangGraph is the brain.
  Each voice provider becomes an adapter behind one `VoiceChannel` port.
- **LangSmith** for tracing, but mask patient data before it leaves our system.

**Interview Q&A**
- *Why SQL for a booking system?* ACID transactions and unique constraints prevent double-booking; data is relational.
- *Is Vapi an orchestration framework?* No — it's a managed voice/telephony platform that calls our API.
  Orchestration (deciding the next step, calling tools) happens in our LangGraph agent.

---

## Step 1 — Project skeleton

**What was built**
- `Agent_Backend/`: uv package with `src/` layout, FastAPI app with `GET /health`, settings via pydantic-settings, one test.
- `admin-frontend/`: Next.js (App Router, TypeScript, Tailwind).
- Root `.gitignore`, git repo initialised.

**Patterns / ideas**
- **App Factory** (`create_app()` in `main.py`): builds a fresh app on demand. Tests can create an app with
  different settings without touching global state.
- **12-Factor config**: settings come from environment variables, not hard-coded. `get_settings()` is cached so
  the env is read once.
- **`src/` layout**: tests import the *installed* package, so they catch packaging mistakes a flat layout hides.

**Interview Q&A**
- *Why an app factory instead of a global `app = FastAPI()`?* Testability and multiple configurations
  (test/dev/prod) from the same code.
- *Why a `/health` endpoint?* Load balancers, Kubernetes and Docker use it to decide whether to send traffic
  or restart the container.
- *Where do secrets go?* `.env` locally (git-ignored), a secret manager in production; `.env.example` documents
  the names without the values.

---

## Step 1.1 — Database connection (Supabase Postgres + SQLModel)

**What was built**
- `db/session.py`: async engine + session factory; `get_session` FastAPI dependency (one session per request).
- Engine is created in the app **lifespan** (startup) and disposed on shutdown — no global connection at import time.
- `GET /health` = liveness (process up). `GET /health/ready` = readiness (DB answers `SELECT 1`, else 503).
- Tests replace the real session with a `FakeSession` via `app.dependency_overrides`.

**Patterns / ideas**
- **Dependency Injection**: routes ask for a session (`Depends(get_session)`); tests inject a fake one.
- **Connection pooling**: opening a DB connection is slow; the engine keeps a pool and reuses them.
  `pool_pre_ping` checks a connection is alive before use (hosted DBs close idle connections).
- **Liveness vs readiness** (Kubernetes terms): if liveness fails → restart the container; if readiness fails →
  stop sending traffic but don't restart (the DB may be briefly down).

**SQLModel vs SQLAlchemy**
- SQLModel = SQLAlchemy + Pydantic in one class (same author as FastAPI). Less boilerplate.
- Trade-offs: it lags SQLAlchemy releases (needs SQLAlchemy < 2.1), and one class for both DB and API can leak
  fields like `password_hash` → always use separate response schemas (`UserRead`).

**Gotcha**: special characters in a DB password must be URL-encoded in the connection string (`@` → `%40`).

**Interview Q&A**
- *Why async DB access?* The agent waits on the LLM and DB a lot; async lets one worker serve other requests while waiting.
- *Why create the engine in lifespan, not at import?* Importing a module shouldn't open network connections;
  it makes tests and tooling fragile.
- *Liveness vs readiness?* See above — restart vs stop routing traffic.

---

## Step 1.1b — Layered folder structure + live Supabase connection

**What changed**
- Backend now uses 5 layers: `models/` → `repositories/` → `services/` → `routers/`, with `schemas/` for API I/O.
- Connected to Supabase through the **session pooler** — the direct `db.<ref>.supabase.co` host only has an
  IPv6 address, and this network has no IPv6. `/health/ready` → `{"status":"ok","database":"ok"}` live.

**Layered architecture in one line each**
- **Router** = waiter: takes the order, hands back the plate. No cooking.
- **Service** = chef: the business rules ("can this hospital be approved?").
- **Repository** = storeroom keeper: the only one who fetches from / puts into the DB.
- **Model** = the shape of the shelf (DB table). **Schema** = the shape of the menu card (API JSON).

**Interview Q&A**
- *Why separate schemas from models?* The API contract and the DB table change for different reasons; separating
  them stops leaking internal fields (password hash) and lets you change one without breaking the other.
- *Why a repository layer if SQLModel is already an abstraction?* Queries live in one place, services become
  testable with a fake repository, and tenant filtering (`hospital_id`) can't be forgotten in a random route.
- *Why did the direct Supabase host fail?* It's IPv6-only; the pooler offers IPv4. Pooler "session mode" (5432)
  keeps one server connection per client, so prepared statements and LangGraph's checkpointer work normally.

---

## Steps 1.2–1.5 — Migrations, users table, login (JWT cookie), platform admin UI

**What was built**
- **Alembic** migrations (async template). `users` table: `username` (unique), `password_hash`, `role`, `hospital_id`,
  `is_active`, timestamps. Upgrade *and* downgrade tested.
- **Supabase RLS** enabled on `users`: Supabase auto-exposes public tables over REST; RLS with no policies blocks that.
- **CLI** `create-platform-admin` (Typer) — there is no public sign-up for the admin role.
- **Auth API**: `POST /auth/login` (sets cookie), `POST /auth/logout`, `GET /auth/me`; `require_role(...)` dependency.
- **Next.js**: `/login`, protected `/platform` dashboard (live API + DB status), sign out.

**Security decisions (great interview material)**
- **Argon2id** password hashing (memory-hard → expensive to brute-force on GPUs). Never store plain passwords.
- **Same error for wrong username and wrong password**, plus a dummy hash check for unknown users → attackers
  can't discover valid usernames by message *or* response time.
- **JWT in an httpOnly cookie**, not localStorage: JavaScript can't read it, so an XSS bug can't steal it.
  `SameSite=Lax` blocks cookies on cross-site POSTs (basic CSRF protection). `Secure` outside local dev.
- JWT is **stateless**: the server verifies the signature, no session table. Trade-off: can't revoke before expiry →
  short expiry (8h) and we re-check `is_active` in the DB on every request.
- **Role stored as VARCHAR, not a Postgres ENUM**: adding a role later needs no `ALTER TYPE`.
- **Caller owns the transaction**: services don't commit; the CLI/request does. Lets one transaction span several
  services later (e.g. "approve hospital" = 4 writes, all or nothing).

**Frontend patterns**
- **Rewrite proxy** (`/api/*` → FastAPI): browser talks to one origin → cookie works, no CORS.
- **Two layers of route protection**: `proxy.ts` (fast, only checks the cookie *exists*) and the server layout
  (calls `/auth/me`, checks the role). The first is UX; the second is the real security.

**Interview Q&A**
- *Where do you store a JWT in the browser and why?* httpOnly cookie — immune to XSS token theft; add SameSite for CSRF.
- *How do you log a user out with stateless JWTs?* Delete the cookie; for forced logout use short expiry + DB
  `is_active` check (or a token denylist / token version column).
- *Why review autogenerated migrations?* Autogenerate only diffs models vs DB; it misses RLS, data migrations,
  renames (sees drop + add), and may pick types you didn't intend (it made `role` a Postgres ENUM here).

---

## Step 2a — Landing page, hospital registration, email verification (OTP)

**What was built**
- Tables `hospitals` and `email_verifications`; `users` gained `email` (unique), `email_verified_at`, FK to hospitals.
- `POST /onboarding/register` → hospital `pending_verification` + admin user + emailed 6-digit code.
- `POST /onboarding/verify-email` → hospital `pending_review`. `POST /onboarding/resend-code` (60 s cooldown).
- Hospital admins can't sign in until approved (clear message per status).
- Frontend: landing `/`, `/onboard` (2 steps), `/login` (hospital), `/superadmin-login` (platform, unlisted), `/portal`.

**Patterns**
- **Ports & Adapters + Factory (email)**: `EmailSender` port; `ConsoleEmailSender` (dev) and `SmtpEmailSender`
  (Gmail) adapters; `create_email_sender(settings)` picks one. Switching provider = config change.
- **Unit of Work**: registration writes 3 rows; all repos share one session and `commit()` runs once —
  *after* the email is sent. If sending fails, nothing is saved and the user can just retry.
- **State machine**: `Hospital.transition_to()` only allows listed moves; REJECTED → ACTIVE raises.
- **Fakes over mocks**: `tests/fakes.py` has in-memory repos/UoW/email sender — tests read like real usage.

**Security details**
- OTP stored as **HMAC-SHA256 with a server secret**, not plain and not a bare hash (only 10⁶ possible codes →
  a bare hash is cracked instantly if the DB leaks).
- **Attempt limit** (5) + **expiry** (10 min) + **resend cooldown** (60 s, `Retry-After` header) stop brute force/spam.
- `resend-code` returns 202 even for unknown emails → can't be used to discover registered emails.
- Constraint **naming convention**: autogenerate produced unnamed constraints, which made the downgrade impossible.

**Interview Q&A**
- *Link or code for email verification?* Code keeps the user on the same page (no tab switching, works on mobile
  mail apps); links are one click but need a landing route and are often pre-fetched by email scanners.
- *Why commit after sending the email?* If the email fails, the user would otherwise be stuck with a registered but
  unverifiable account ("email already exists"). Send first, then commit → failure leaves no trace.
- *Why a separate, unlisted superadmin login?* Smaller attack surface and clearer UX; but security comes from the
  role check on the server, never from hiding the URL.
