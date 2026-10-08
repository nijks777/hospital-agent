# CLAUDE.md — Hospital Call Agent

## What this project is

An AI **call agent for hospitals**: it talks to patients (chat first, voice later), understands what they
want, and performs actions through **tools** (check doctor availability, book/cancel appointments, answer
hospital FAQs, escalate emergencies to a human).

It is **not** a full hospital system. It is a pluggable component that any third-party app (hospital
software, website widget, phone system) can integrate with through a clean API. The hospital's real data
lives in *their* system; we only talk to it through adapters.

Built as an interview portfolio project, so code must look and feel **industry standard**.

## Working agreement (how Claude works with the user)

- **Build step by step.** One small step at a time. Finish, verify, explain, then move to the next.
  Never jump ahead to a later version's features.
- **Explain everything in easy words.** The user is preparing for interviews. After every step, explain in
  chat: *what* was built, *why* it was built that way, and *which design pattern* (if any) was used.
  Use simple language and a real-world analogy where it helps.
- **Add an "Interview angle"** at the end of each explanation: 1–3 questions an interviewer might ask
  about this step, with short answers.
- **Log learnings** in `docs/LEARNING.md` (append, newest last): step name, what was built, pattern used,
  interview Q&A. This becomes the user's revision notes.
- Use design patterns **only where they solve a real problem here**, and say what problem they solve.
  A pattern with no problem is over-engineering — call that out instead.

## Coding principles (Karpathy guidelines)

Based on Andrej Karpathy's observations of common LLM coding mistakes.

1. **Think before coding.** State assumptions explicitly. If a request has more than one reasonable
   meaning, list the options and ask — don't silently pick one. If something is unclear, stop and ask.
2. **Simplicity first.** Write the minimum code that solves the current step. No speculative features,
   no "might need it later" config, no abstraction with a single caller unless it's a deliberate
   integration seam (see Architecture). If 200 lines could be 50, rewrite it.
3. **Surgical changes.** Touch only what the task needs. Don't reformat, rename, or "improve" unrelated
   code or comments. Remove only the dead code your own change created; mention other issues, don't fix them.
4. **Goal-driven execution.** Turn each task into a verifiable goal before coding
   (e.g. "`POST /chat` returns a booking confirmation; test X passes"). For multi-step work, write a
   short plan with a check for each step, then loop until the checks pass.

## Tech stack (V1)

- **Backend** (`Agent_Backend/`, package `src/hospital_agent/`): Python 3.13, FastAPI, Pydantic v2, `uv`
- **Agent orchestration**: LangGraph — confined to `agent/`; tools call our ports, never LangGraph directly
- **LLM**: OpenAI first (`langchain-openai`), behind an `LLMProvider` port so others can be added
- **Database**: PostgreSQL hosted on **Supabase** via the **session pooler** host
  `aws-0-ap-south-1.pooler.supabase.com:5432` (the direct `db.<ref>` host is IPv6-only and fails here) — business data
  (**SQLModel** on SQLAlchemy 2.0 async + Alembic; SQLModel pins SQLAlchemy < 2.1), RAG vectors (pgvector),
  agent memory (LangGraph Postgres checkpointer). SQL chosen for transactions (no double-booking).
- **Observability**: LangSmith (mask PII before tracing) + `structlog`
- **Frontend** (`admin-frontend/`): Next.js (App Router, TypeScript, Tailwind) — platform admin panel
- **Tests**: `pytest`; **lint/format**: `ruff`; **types**: `pyright`
- Secrets in `.env` (never committed), documented in `.env.example`

**Dynamic configuration principle:** `.env` holds only what's needed to boot (DB URL, secrets key).
Everything a hospital admin may want to change (LLM provider/model, voice provider, prompts, enabled
tools) is stored in the DB and edited from the admin panel. Adapters are chosen at runtime from that
config via a Factory. Design of this is pending a spec.

Install a dependency at the step that first uses it. Deferred: `presidio-analyzer` (guardrails step),
`livekit-agents` (V2 voice). Vapi needs no SDK — it calls our API.

## Architecture (layered + Ports & Adapters for integrations)

Request flow — each layer only calls the one below it:

```
routers ──► services ──► repositories ──► models ──► Postgres
   │            │
schemas      integrations/ (ports + adapters: LLM, payments, voice)   agent/ (LangGraph)
```

Backend layout (`Agent_Backend/src/hospital_agent/`) — **the 5 core layers are mandatory**:

- `models/` — SQLModel **table** classes (`table=True`). DB shape only.
- `schemas/` — Pydantic request/response models (`UserCreate`, `UserRead`). Never return a table model
  from a route — that leaks fields like `password_hash`.
- `repositories/` — the only place that runs DB queries. Tenant tables take `hospital_id` on every query.
- `services/` — business logic. They take a `UnitOfWork` (`db/unit_of_work.py`: all repositories + one
  `commit()`) and commit exactly once per use case. No HTTP, no raw SQL.
- `routers/` — FastAPI routes: parse input, call a service, return a schema. No business logic.
- `core/` — config, security (hashing, JWT), logging, errors. `db/` — engine, session dependency.
- Added at their milestones: `integrations/` (a port = abstract class + one adapter per provider,
  chosen by a Factory) and `agent/` (LangGraph graph + tools; tools call services, never the DB).

Integration seams that **are** abstract from day one (integration is the product's whole point):
LLM provider, payment gateway, hospital-data source, voice (V2).

## Design patterns we expect to use

Introduce each one only at the step where it's needed, and explain it then.

| Pattern | Where | Problem it solves |
|---|---|---|
| Ports & Adapters | whole layout | Swap hospital systems / LLMs without touching agent logic |
| Strategy | `LLMProvider` | Choose Claude vs another LLM at runtime via config |
| Repository | data access | Agent asks "get free slots", doesn't care if it's SQLite or an external API |
| Registry | tool registry | Add a new tool without editing the agent loop |
| Command | each tool | Every action has the same `execute(input) -> result` shape |
| Dependency Injection | FastAPI `Depends` | Easy testing with fakes; no hidden globals |
| Factory | adapter/provider creation | Build the right implementation from settings |

## Roadmap

**Version 1 — multi-tenant chat-agent platform.** Full design (source of truth):
`docs/superpowers/specs/2026-10-04-v1-platform-design.md`

0. ~~Project skeleton, config, health check~~ (done)
1. Foundation — Postgres, SQLAlchemy + Alembic, users, auth (JWT cookie), roles, seed platform admin
2. Onboarding — register form, approve/reject/suspend, plans, default config copy, audit log,
   payment port + manual gateway + invoices
3. Hospital portal — departments, doctors, schedules, FAQs, agent settings, API keys + embed snippet
4. Agent core — LangGraph, OpenAI, tools, RAG over FAQs, per-hospital Factory
5. Chat channel — `POST /v1/chat`, widget (`widget.js` + iframe), `demo-hospital-site/`
6. Safety + metering — guardrails, usage vs plan limits, LangSmith
7. Polish — usage dashboard, Docker, README with integration guide

**Version 2** — voice (Vapi / LiveKit adapters, minute metering), live payment adapters
(Stripe / Razorpay), notifications, external hospital-system adapters, webhooks.

## Rules specific to this domain

- The agent must **never diagnose or give medical advice**; it routes, books, and informs.
- Emergency keywords/intents (chest pain, can't breathe, etc.) → immediately tell the caller to contact
  emergency services and escalate. This check runs regardless of what the LLM decides.
- Don't log full patient personal data (names, phone numbers) in plain text — mask it.
- Tools validate their own input (Pydantic); never trust LLM-generated arguments blindly.

## Commands

Backend (run inside `Agent_Backend/`):
- `uv run fastapi dev src/hospital_agent/main.py` — dev server on :8000 (`/health`, `/docs`)
- `uv run pytest` — tests
- `uv run ruff check . && uv run ruff format .` — lint + format
- `uv run pyright src tests` — type check
- `uv add <pkg>` / `uv add --dev <pkg>` — add dependency
- `uv run alembic revision --autogenerate -m "<msg>"` then **review the file** — autogenerate misses
  things (e.g. Supabase RLS). Every new table's migration must `ENABLE ROW LEVEL SECURITY`.
  Constraint names come from the naming convention in `models/base.py` — never `None`.
- `uv run alembic upgrade head` / `uv run alembic downgrade -1`
- `uv run python -m hospital_agent.cli create-platform-admin <username>` — prompts for password

Frontend routes: `/` landing · `/onboard` (register + email code) · `/login` (hospital admin, email) ·
`/superadmin-login` (platform admin, not linked anywhere) · `/platform/*` · `/portal/*`.
Email: `EMAIL_BACKEND=console` prints verification codes in the backend log; `smtp` sends via Gmail
app password (see `.env.example`).

Frontend (run inside `admin-frontend/`):
- `npm run dev` — dev server on :3000 (needs backend on :8000)
- `npm run lint` / `npm run build` (run build before `npx tsc --noEmit`; it generates route types)
- Browser calls `/api/*` → rewritten to FastAPI (`next.config.ts`), so the auth cookie is same-origin.
  Server components call `BACKEND_URL` directly via `src/lib/api.ts`. Next 16: middleware is `src/proxy.ts`.
- UI tokens live in `src/app/globals.css` `@theme` (ward / scrub / saline / status colors, Public Sans).

Gotcha: `~/.npm` has root-owned files. Until fixed with `sudo chown -R $(id -u):$(id -g) ~/.npm`,
`npm install` needs `--cache <some-writable-dir>`.
