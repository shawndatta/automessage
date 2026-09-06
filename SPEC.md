# AutoMessage — Build Specification (v0.1, local-first)

This document is written to be handed to an AI coding tool (Cursor). Build in the milestone order in Section 12. Each milestone has acceptance criteria. Do not skip ahead; earlier milestones are dependencies for later ones.

---

## 1. What we are building

An open source, self-hosted ManyChat alternative. A local-first app that automates social media DMs with a visual flow builder and an agentic AI reply node. v0.1 targets Telegram (fully local via long polling) and lays the architecture for Instagram/Messenger later.

**Product principles:**
- Runs as a single local Python process. `automessage start` launches the API and opens the browser.
- No per-contact limits, no metering. The user brings their own LLM API key.
- The AI node is a tool-calling agent (contact lookup, knowledge retrieval, tagging, human handoff), not a single completion.
- Everything (contacts, conversations, flows, settings) lives in a local SQLite database.

**Explicitly out of scope for v0.1:** Instagram/Messenger/WhatsApp adapters (architecture only), broadcasts, drip campaign UI, multi-user auth, teams, email/SMS. Build the seams for these but do not implement them.

---

## 2. Tech stack (use these versions or newer minor)

- **Language:** Python 3.12
- **Web framework:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.x (async) with aiosqlite
- **Migrations:** Alembic
- **Validation/config:** Pydantic v2 + pydantic-settings
- **Scheduler:** APScheduler (in-process, SQLAlchemy job store so scheduled jobs survive restart)
- **DB:** SQLite (default). Vector search via `sqlite-vec` extension.
- **LLM client:** `openai` Python SDK, pointed at a configurable `base_url` so DeepSeek/OpenAI/Ollama all work through the OpenAI-compatible API. DeepSeek base_url `https://api.deepseek.com`.
- **Telegram:** call the Bot API over HTTP with `httpx` directly (do not pull in a heavy bot framework; we need a thin adapter, not a framework).
- **Frontend:** React 18 + Vite + TypeScript, Tailwind CSS, React Flow (`@xyflow/react`) for the node editor, TanStack Query for data fetching, WebSocket for the live inbox.
- **Encryption:** `cryptography` (Fernet) for credentials at rest.
- **Packaging:** installable via `pipx`; the CLI entry point launches the server and serves the built frontend as static files from the same process.

**Design rule that matters:** persistence and scheduling sit behind interfaces (`Store`, `Scheduler`) so that a future "server mode" can swap SQLite→Postgres and APScheduler→Redis worker without touching business logic. Implement only the SQLite/in-process versions now, but code to the interface.

---

## 3. Repository layout

```
automessage/
  pyproject.toml
  README.md
  SPEC.md                      # this file
  .env.example
  alembic/
  automessage/
    __init__.py
    cli.py                     # `automessage start` entry point
    main.py                    # FastAPI app factory, mounts routers + static frontend
    config.py                  # Settings (pydantic-settings), first-run detection
    db.py                      # async engine/session, Store interface
    crypto.py                  # Fernet encrypt/decrypt for credentials
    models/                    # SQLAlchemy models (Section 6)
    schemas/                   # Pydantic request/response models
    api/
      onboarding.py            # first-run wizard endpoints
      settings.py             # LLM + channel config
      flows.py                 # CRUD + publish
      contacts.py
      conversations.py         # inbox + WS
      knowledge.py             # KB upload + reindex
    channels/
      base.py                  # ChannelAdapter protocol, InboundEvent, OutboundAction (Section 4)
      telegram.py              # v0.1 adapter (long polling)
      registry.py              # maps channel name -> adapter
    engine/
      flow_engine.py           # resumable state machine (Section 5)
      nodes.py                 # node executors (Section 5.2)
      triggers.py              # trigger matching (Section 5.1)
      scheduler.py             # Scheduler interface + APScheduler impl
    agent/
      runtime.py               # tool-calling loop (Section 7)
      tools.py                 # built-in agent tools
      providers.py             # LLM provider config + cost table
      retrieval.py             # sqlite-vec embed + search
    events.py                  # internal event bus (inbound event -> engine)
  frontend/
    src/
      pages/  Onboarding, Flows, FlowEditor, Inbox, Contacts, Knowledge, Settings
      components/ nodes/ (React Flow custom nodes), inbox/, ...
      api/  (typed client)
    ...
```

---

## 4. Channel adapter interface (`channels/base.py`)

The engine never imports Telegram code. Adapters translate both directions.

```python
from typing import Protocol, Literal
from pydantic import BaseModel

Capability = Literal["text", "media", "quick_replies", "typing",
                     "comment_to_dm", "messaging_window"]

class InboundEvent(BaseModel):
    channel: str
    channel_account_id: int
    type: Literal["message_received", "postback_clicked", "comment_created"]
    external_contact_id: str
    external_conversation_id: str
    text: str | None = None
    payload: dict = {}          # media refs, button callback_data, etc.
    provider_message_id: str | None = None
    dedupe_key: str | None = None   # e.g. telegram update_id, for idempotency

class OutboundAction(BaseModel):
    type: Literal["send_text", "send_media", "send_quick_replies",
                  "typing_on", "mark_seen"]
    external_conversation_id: str
    text: str | None = None
    media_url: str | None = None
    buttons: list[dict] = []    # [{title, payload}]

class DeliveryResult(BaseModel):
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None
    unsubscribe: bool = False   # set true if user blocked the bot

class ChannelAdapter(Protocol):
    channel: str
    def capabilities(self) -> set[Capability]: ...
    async def validate_credentials(self, creds: dict) -> dict: ...  # returns bot/account info or raises
    async def start(self, account) -> None: ...   # begin polling (telegram) or register webhook
    async def stop(self, account) -> None: ...
    async def send(self, account, action: OutboundAction) -> DeliveryResult: ...
```

`start()` for Telegram launches a background long-polling task. For future webhook channels it registers a webhook and `parse_event` is called by an HTTP route instead. Keep the inbound path uniform: every adapter ultimately emits `InboundEvent` onto the internal event bus (`events.py`).

---

## 5. Flow engine (`engine/`)

A flow is stored as JSONB-in-SQLite: `{trigger: {...}, nodes: [...], edges: [...]}`. Each contact moving through a flow gets a `flow_run` row with `current_node_id`, `variables` (JSON), `status`, and `wake_at`. The engine is a resumable state machine so delays and awaited inputs survive process restarts.

### 5.1 Triggers (`triggers.py`)
On each inbound `message_received`:
1. If an open `flow_run` is awaiting input for this contact, route the message there first.
2. Else evaluate published flows' triggers in priority order:
   - `keyword` — match mode `exact | contains | regex` against text (case-insensitive default)
   - `new_conversation` — first ever message from this contact
   - (Instagram-only, later) `comment_keyword`
3. First match starts a new `flow_run` at the trigger's entry node.

### 5.2 Node executors (`nodes.py`)
Each node is `async def execute(node, run, ctx) -> NextStep`. `NextStep` is one of: `Goto(edge)`, `Wait(until=datetime)`, `AwaitInput(field)`, `End()`. v0.1 node set (exactly eight):

1. **send_message** — resolve variable templating in text, emit `send_text` / `send_quick_replies` / `send_media` OutboundAction(s) via the adapter. Follow the edge.
2. **delay** — compute `wake_at`, return `Wait`. The scheduler re-enters the run at `wake_at`.
3. **condition** — evaluate expression over contact tags/fields/last input; follow matching edge (`true`/`false` or labelled branches).
4. **collect_input** — send the prompt, return `AwaitInput(field)`. Next inbound message from this contact is stored to that field and the run resumes.
5. **tag** — add/remove a tag on the contact. Follow edge.
6. **set_field** — set a custom field (JSON on contact). Follow edge.
7. **ai_agent** — hand conversation to the agent runtime (Section 7). On return, follow edge based on agent outcome (`resolved` / `escalated`).
8. **handoff_human** — set conversation.state = "human", flag inbox, `End()`.

### 5.3 Scheduler (`engine/scheduler.py`)
`Scheduler` interface: `schedule(run_id, wake_at)`, `cancel(run_id)`. APScheduler implementation persists jobs in SQLite so a laptop that sleeps resumes pending delays on restart (catch-up: on boot, immediately fire any jobs whose `wake_at` has passed).

### 5.4 Guardrails
- Per-conversation rate limit (token bucket) to respect Telegram's ~1 msg/sec/chat.
- Loop protection: max N node executions per run (default 100) then force-end with an error state.
- Idempotency: drop inbound events whose `dedupe_key` was already processed.

---

## 6. Data model (`models/`)

SQLite tables (SQLAlchemy models). Use JSON columns where noted.

- **app_settings** — id, `llm` JSON (provider, base_url, model, encrypted api_key, embed_model), `onboarded` bool, `encryption_check`, created_at
- **channel_account** — id, channel, `credentials` JSON (encrypted), display_name, status (`active|inactive|error`), created_at
- **contact** — id, channel_account_id (FK), external_id, name, avatar_url, subscribed bool, `fields` JSON, created_at. Unique (channel_account_id, external_id).
- **tag** — id, name. **contact_tag** — contact_id, tag_id.
- **conversation** — id, contact_id (FK), external_id, state (`automated|human|closed`), last_message_at, created_at
- **message** — id, conversation_id (FK), direction (`in|out`), type, `payload` JSON, provider_message_id, status, created_at
- **flow** — id, name, status (`draft|published`), `definition` JSON, `trigger` JSON, version int, updated_at
- **flow_run** — id, flow_id (FK), contact_id (FK), current_node_id, `variables` JSON, status (`active|waiting|awaiting_input|done|error`), wake_at, awaiting_field, exec_count, created_at, updated_at
- **kb_document** — id, filename, status, created_at. **kb_chunk** — id, document_id (FK), text, `embedding` (sqlite-vec), token_count
- **agent_trace** — id, conversation_id (FK), flow_run_id, step int, kind (`llm|tool`), name, `input` JSON, `output` JSON, prompt_tokens, completion_tokens, cost_usd, created_at
- **processed_event** — dedupe_key (PK), created_at   # idempotency

---

## 7. AI agent runtime (`agent/`)

Per `ai_agent` node invocation, run a bounded tool-calling loop against the configured LLM.

**Node config:** `system_prompt`, `model` (override or inherit global), `temperature`, `max_turns` (default 6), `allowed_tools` (subset), `escalate_on_uncertain` bool.

**Loop (`runtime.py`):**
1. Build messages: system prompt + rendered contact context + recent conversation history.
2. Call LLM with tool schemas for `allowed_tools`.
3. If the model calls a tool, execute it, append the result, loop. If it returns text, send it as a reply.
4. Stop when: model produces a final reply and no further tool call, OR `max_turns` reached (then either send best reply or escalate), OR a tool called `escalate_to_human`.
5. Log every LLM call and tool call to `agent_trace` with token counts and computed `cost_usd`.

**Built-in tools (`tools.py`):**
- `get_contact_profile()` → name, tags, fields
- `get_conversation_history(limit)` 
- `search_knowledge_base(query)` → top-k chunks via `retrieval.py`
- `tag_contact(tag)` / `set_field(key, value)`
- `escalate_to_human(reason)` → ends loop, sets conversation.state="human"

**Providers & cost (`providers.py`):** a table mapping model → (input $/1M, output $/1M) so the cost meter is accurate. Seed with DeepSeek V4 Flash and a couple of OpenAI models; make it editable. If a model is unknown, record tokens and show cost as "unknown" rather than guessing.

**Retrieval (`retrieval.py`):** on KB upload, chunk (~500 tokens, overlap ~50), embed via the provider's embedding model (or a local `sentence-transformers` fallback if provider has none), store in `kb_chunk`. Search = embed query, `sqlite-vec` nearest neighbours, return top-k text.

---

## 8. First-run onboarding (`api/onboarding.py` + frontend)

On startup, if `app_settings.onboarded` is false, the frontend routes to the wizard and all other routes redirect there.

**Step 1 — LLM:** choose provider (DeepSeek default / OpenAI / Anthropic-compatible / Ollama). Fields: base_url (prefilled per provider), model (prefilled), API key (not required for Ollama). "Test connection" button → backend fires a 1-token completion; show success/failure. Save encrypted.

**Step 2 — Channel:** choose Telegram (available) or Instagram (shown but disabled with "requires deploy mode, see docs"). For Telegram: paste bot token → backend calls `getMe` to validate → store encrypted, create `channel_account`, start polling.

**Step 3 — Done:** mark `onboarded=true`, drop the user into an empty Flows page with a "Create your first flow" template.

Settings page lets them edit both later.

---

## 9. Telegram adapter specifics (`channels/telegram.py`)

- **Auth:** single bot token from BotFather. `validate_credentials` calls `getMe`.
- **Inbound:** long-polling loop calling `getUpdates` with `offset` and `timeout=30`. Map `message.text`→`message_received`; `callback_query`→`postback_clicked` (then call `answerCallbackQuery`); photo/document→`message_received` with media payload. `dedupe_key = update_id`. Contact `external_id = from.id`; conversation `external_id = chat.id`.
- **Outbound:** `send_text`→`sendMessage`; `send_quick_replies`→`sendMessage` with `inline_keyboard` (buttons carry `callback_data=payload`); `send_media`→`sendPhoto`/`sendDocument`; `typing_on`→`sendChatAction`.
- **Errors:** 403 → return `DeliveryResult(unsubscribe=True)`, mark contact unsubscribed, do not retry. 429 → respect `retry_after`.
- **capabilities():** `{text, media, quick_replies, typing}`. No comment_to_dm, no messaging_window.

---

## 10. API surface (REST + WS)

- `GET /api/state` → `{onboarded, channel_status}` (frontend boot)
- `POST /api/onboarding/llm/test`, `POST /api/onboarding/llm`, `POST /api/onboarding/channel`
- `GET/PUT /api/settings/llm`, `GET/POST/DELETE /api/settings/channels`
- `GET/POST/PUT/DELETE /api/flows`, `POST /api/flows/{id}/publish`
- `GET /api/contacts`, `GET /api/contacts/{id}`, tag/field edits
- `GET /api/conversations`, `GET /api/conversations/{id}/messages`
- `POST /api/conversations/{id}/takeover`, `POST /api/conversations/{id}/resume`, `POST /api/conversations/{id}/send`
- `WS /api/ws` → pushes new messages + conversation state changes to the inbox
- `POST /api/knowledge` (upload), `GET /api/knowledge`, `DELETE /api/knowledge/{id}`
- `GET /api/conversations/{id}/trace` → agent trace for the trace panel

All request/response bodies typed with Pydantic schemas; generate a typed TS client or hand-write one.

---

## 11. Frontend notes

- **Flow editor:** React Flow. Custom node components for the eight node types, each with an inline config panel. Palette on the left, canvas centre, node settings on the right. Save serialises to the `{nodes, edges, trigger}` JSON. Grey out capability-incompatible nodes based on the connected channel.
- **Inbox:** conversation list with state badges (`automated`/`human`), message thread, "Take over" / "Resume bot" buttons, and a collapsible **agent trace panel** showing each LLM/tool step with tokens and cost. This panel is a headline demo feature; make it look good.
- **Cost meter:** show running $ total per conversation and a global total, sourced from `agent_trace.cost_usd`.
- **Onboarding:** clean three-step wizard as in Section 8.
- Keep styling intentional, not default-Bootstrap. Tailwind, restrained palette, good empty states.

---

## 12. Build order (milestones with acceptance criteria)

**M1 — Skeleton & config.** FastAPI app, SQLite + Alembic, `Settings`, crypto, CLI `automessage start` serves an empty frontend and opens the browser.
*Done when:* `pipx`-installed app boots, creates the DB, serves a page.

**M2 — Onboarding + Telegram inbound/outbound.** First-run wizard (LLM test + Telegram token). Telegram adapter with polling. Inbound events land on the event bus; a hardcoded echo handler replies.
*Done when:* after the wizard, messaging the bot gets an echo reply, and contact/conversation/message rows are created.

**M3 — Flow engine core.** flow_run state machine, triggers (keyword + new_conversation), and nodes send_message + delay, with APScheduler persistence and restart catch-up. Flows defined via seeded JSON (no UI yet).
*Done when:* a keyword triggers a two-message flow with a working delay that survives a restart.

**M4 — Flow builder UI.** React Flow editor, all eight nodes with config panels, publish. condition / collect_input / tag / set_field / handoff_human executors.
*Done when:* a user can build, publish, and run a flow end to end from the UI, including collect_input storing an answer and condition branching on it.

**M5 — AI agent node.** Agent runtime + tools + providers/cost table + sqlite-vec retrieval + KB upload. ai_agent node wired into flows.
*Done when:* an ai_agent node answers a question using an uploaded KB doc, calls a tool, and every step appears in agent_trace with cost.

**M6 — Inbox & polish.** Live inbox over WS, human takeover/resume, agent trace panel, cost meter, README + demo GIF.
*Done when:* a human can take over a live conversation, resume the bot, and watch traces/cost update live.

---

## 13. Deploy-mode note (document, do not build in v0.1)

Instagram/Messenger require public HTTPS webhooks and Meta app review, so they run in "deploy mode" (VPS) rather than local mode. The adapter interface already supports a webhook inbound path; when built, an HTTP route calls the adapter's `parse_event` and emits the same `InboundEvent`. Persistence/scheduler interfaces allow swapping SQLite→Postgres and APScheduler→Redis for always-on server use. Keep these seams clean; do not implement them now.

---

## 14. Licensing & meta

MIT license. `.env.example` documents optional overrides (DB path, port, log level); real secrets go through the encrypted settings store, not env. CONTRIBUTING.md headlines "write a channel adapter" as the ideal first PR.
