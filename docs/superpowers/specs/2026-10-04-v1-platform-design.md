# V1 Design — Hospital Agent Platform

Status: **Approved** · Date: 2026-10-04

## 1. Goal

A multi-tenant SaaS platform that gives hospitals an AI chat agent they can embed on their website.
Hospitals apply, the platform admin approves them, they get a default plan + default agent config,
and patients on the hospital's website can ask questions and book appointments through the agent.

Built as a portfolio project: features are kept small, but structure, security and patterns are
production-style.

**Success criteria for V1 (demo script)**
1. A visitor fills the "Register your hospital" form on our website.
2. Platform admin logs in, sees the pending application, approves it.
3. The hospital automatically gets the default plan and default agent config.
4. Hospital admin logs in, adds departments, doctors, schedules and FAQs, copies the embed snippet.
5. On the demo hospital website, a patient chats with the agent: asks visiting hours (answered from
   FAQs via RAG), checks a doctor's free slots, books one. The booking appears in the hospital portal.
6. Typing an emergency phrase ("chest pain") returns the emergency message immediately, no booking flow.
7. Platform admin sees conversation usage per hospital against its plan limit.

## 2. Actors

| Actor | Logs in? | Can do |
|---|---|---|
| **Platform admin** (us) | Yes | Review/approve/reject/suspend hospitals, change a hospital's plan and agent config, edit platform defaults, see usage |
| **Hospital admin** | Yes, after approval | Manage departments, doctors, schedules, FAQs; edit allowed agent settings; see appointments, conversations, usage; get embed snippet + API keys |
| **Patient** | No | Chat with the agent on the hospital's website |

Platform admin account is created by a CLI seed command (no public sign-up for it).

## 3. Hospital lifecycle (state machine)

```
                verify email             approve                 suspend
PENDING_VERIFICATION ──────► PENDING_REVIEW ───────► ACTIVE ◄──────────────► SUSPENDED
                                   │                           reactivate
                                   └── reject ──► REJECTED
```

- Registration creates the hospital (`PENDING_VERIFICATION`) **and** its admin user (username = email),
  then emails a 6-digit code (10-min expiry, 5 attempts, 60 s resend cooldown, stored as an HMAC).
- Entering the code moves the hospital to `PENDING_REVIEW`; only these appear for the platform admin.
- Hospital-admin login is refused (with a status-specific message) unless the hospital is `ACTIVE`.
- Transitions are only allowed along the arrows (`Hospital.transition_to`); anything else raises.
- Every transition is written to an `audit_log` (who, when, from → to, reason). *(added with approve, M2)*
- Email goes through an `EmailSender` port: `ConsoleEmailSender` (dev) or `SmtpEmailSender` (Gmail app password).

**Approve** runs in one DB transaction (all or nothing):
1. status → `ACTIVE`
2. create subscription on the **default plan**
3. copy the **default agent config** into a hospital-owned config
4. generate API keys (publishable + secret)

## 4. Plans (business model)

| Plan | Conversations / month | Doctors | Voice minutes | Price (display only) |
|---|---|---|---|---|
| **Trial** (default, 14 days) | 100 | 5 | — | Free |
| **Starter** | 1,000 | 25 | — | ₹4,999/mo |
| **Pro** | 10,000 | Unlimited | V2 | ₹19,999/mo |

- Plans are DB rows, editable by the platform admin — not hard-coded.
- A *conversation* = one chat session. Usage is metered per hospital per month (also tokens, for cost tracking).
- At the limit, the agent replies with a polite "service unavailable, please call the hospital" message.
- **Payments are designed but not live.** A `PaymentGatewayPort` (create checkout, verify webhook,
  get payment status) has one V1 adapter: `ManualPaymentGateway` — the platform admin marks an
  invoice paid by hand. Stripe / Razorpay adapters are V2 and plug in without changing callers.
- Platform admin **Settings → Payments** shows the active gateway and the available adapters
  (Manual = active; Stripe, Razorpay = "coming soon"), selected from config via the same **Factory**.
- Changing a hospital's plan creates an `invoice` row (`PENDING` → `PAID`); the subscription switches
  plan when the invoice is paid.

## 5. Agent configuration (dynamic settings)

Two layers: **platform default config** (one row, edited by platform admin) is **copied** into each
hospital on approval. After that the hospital's copy is independent (changing defaults doesn't
silently change existing hospitals).

| Setting | Who can edit |
|---|---|
| Agent name, greeting, tone, languages | Hospital admin |
| Emergency phone number, escalation contact, working hours | Hospital admin |
| Allowed website domains (for the widget) | Hospital admin |
| Enabled tools (FAQ, availability, booking, cancel) | Platform admin |
| LLM provider, model, temperature | Platform admin |
| Core safety prompt (no diagnosis, emergency rules) | Nobody per hospital — fixed in code |

At runtime the agent is built per request from the hospital's config (**Factory**), so one deployment
serves all hospitals with different settings. LLM provider is a **Strategy** (OpenAI first).

## 6. Integration (how a hospital uses us)

Same model as Stripe:
- **Publishable key** (`pk_...`): safe in the browser; used by the chat widget. Only works from the
  hospital's allowed domains (checked via `Origin` header) and can only chat.
- **Secret key** (`sk_...`): server-to-server API for the hospital's own systems. Stored **hashed**;
  shown once at creation; can be rotated.

**Chat widget:** the hospital pastes one line:
```html
<script src="https://<our-app>/widget.js" data-key="pk_..."></script>
```
`widget.js` adds a chat bubble that opens an **iframe** pointing to our `/widget` page. The iframe
keeps our CSS/JS isolated from the hospital's site (same approach as Intercom). We also publish a
versioned path (`/widget/v1.0.0.js`) so hospitals that want Subresource Integrity can pin a hash.

## 7. Applications

| App | Folder | Contents |
|---|---|---|
| Backend API | `Agent_Backend/` | FastAPI, agent, DB |
| Our website + dashboards | `admin-frontend/` | `/` landing, `/onboard`, `/login` (hospital admin), `/superadmin-login` (unlisted), `/platform/*`, `/portal/*`, `/widget` |
| Demo hospital website | `demo-hospital-site/` (new) | A simple fake hospital site ("City Care Hospital") that embeds the widget — proves third-party integration |

## 8. Backend architecture

Ports & Adapters as in CLAUDE.md, plus:

- **Multi-tenancy:** shared database, every tenant table has `hospital_id`. Repositories require a
  `hospital_id` for every query, so one hospital can never read another's data.
- **Auth:** email + password (argon2 hash) → JWT access token in an httpOnly cookie. Roles:
  `PLATFORM_ADMIN`, `HOSPITAL_ADMIN`. Route guards check role + hospital ownership.
- **Hospital data source:** a `HospitalDataPort`; V1 adapter = our own DB ("native"). External
  hospital-system adapters are V2.
- **Agent (LangGraph):** guardrail input check → LLM with tools → tool execution → guardrail output
  check. Conversation memory via LangGraph Postgres checkpointer, keyed by conversation id.
- **Tools:** `search_hospital_info` (RAG over FAQs, pgvector), `list_departments`, `find_doctors`,
  `check_availability`, `book_appointment`, `cancel_appointment`.
- **Guardrails (Chain of Responsibility):** emergency detector (rules, runs first, no LLM) →
  PII masking for logs/traces → output check (no diagnosis).
- **Observability:** LangSmith traces tagged with `hospital_id`; structlog JSON logs.

### Data model (main tables)

`users` · `hospitals` · `email_verifications` · `plans` · `subscriptions` · `invoices` · `usage_records` · `platform_default_config` ·
`agent_configs` · `api_keys` · `departments` · `doctors` · `doctor_schedules` (weekly hours + slot
length) · `appointments` (**unique `(doctor_id, start_time)`** — prevents double booking) ·
`patients` (name, phone) · `knowledge_chunks` (FAQ text + embedding) · `conversations` · `messages` ·
`audit_log`

Free slots are computed from schedules minus existing appointments (not stored as rows).

## 9. Design patterns used (and why)

| Pattern | Where | Problem solved |
|---|---|---|
| State machine | Hospital lifecycle | Stops invalid moves like REJECTED → ACTIVE |
| Prototype (copy a template) | Default config → hospital config | Every new hospital starts ready to use; later default changes don't break them |
| Unit of Work (one transaction) | Approve hospital | Half-approved hospitals can't exist |
| Repository (tenant-scoped) | Data access | Isolation between hospitals; swappable storage |
| Factory | Build agent per hospital config | One deployment, many differently-configured agents |
| Strategy | LLM provider | Swap OpenAI for another provider via config |
| Chain of Responsibility | Guardrails | Add/remove safety checks without touching the agent |
| Ports & Adapters | Hospital data, LLM, payments, (V2) voice | Integrate new providers by adding an adapter |

## 10. Build order (V1 milestones)

Each milestone ends with something demoable and tested.

1. **Foundation** — Postgres (Docker), SQLAlchemy + Alembic, users, auth, roles, seed platform admin.
2. **Onboarding** — landing page, register form, platform admin approve/reject/suspend, plans,
   default config copy, audit log, payment port + manual gateway + invoices.
3. **Hospital portal** — departments, doctors, schedules, FAQs, agent settings, API keys + embed snippet.
4. **Agent core** — LangGraph agent, OpenAI, tools, RAG over FAQs, per-hospital Factory.
5. **Chat channel** — `POST /v1/chat`, widget (`widget.js` + iframe page), demo hospital website.
6. **Safety + metering** — guardrails, usage counting + plan limits, LangSmith.
7. **Polish** — platform usage dashboard, Dockerfiles + docker-compose, README with integration guide.

## 11. Out of scope for V1 (→ V2)

Voice calls (Vapi / LiveKit adapters, minute metering) · live payment adapters (Stripe / Razorpay) · email/SMS notifications ·
hospital-owned LLM keys · external hospital-system adapters · webhooks · multiple admins per hospital
· password reset by email.
