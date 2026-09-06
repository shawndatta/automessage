# AutoMessage

Open-source, self-hosted DM automation — a local-first ManyChat alternative.

v0.1 targets Telegram (long polling) with a visual flow builder and an agentic AI reply node. Everything lives in a local SQLite database.

## Quick start

```bash
# Backend
python -m pip install -e .
cd frontend && npm install && npm run build && cd ..
automessage start
```

Opens http://127.0.0.1:8741 — creates `~/.automessage/automessage.db` on first run.

On a normal start you **sign up or sign in**. For a disposable local demo account:

```bash
automessage start default
```

That seeds `default@example.com` / `automessage` and auto-signs you in.

```bash
automessage stop
```

Stops the server (uses `~/.automessage/server.pid`, or the process listening on the configured port).

### Development

```bash
# API (reload)
automessage start --reload --no-browser

# Frontend (Vite, proxies /api to :8741)
cd frontend && npm run dev
```

## Configuration

Optional overrides go in `.env` (see `.env.example`). LLM keys and bot tokens are stored encrypted in SQLite — not in env files.

| Variable | Default | Meaning |
|---|---|---|
| `AUTOMESSAGE_PORT` | `8741` | HTTP port |
| `AUTOMESSAGE_HOST` | `127.0.0.1` | Bind host |
| `AUTOMESSAGE_DB_PATH` | `~/.automessage/automessage.db` | SQLite path |
| `AUTOMESSAGE_LOG_LEVEL` | `INFO` | Log level |
| `AUTOMESSAGE_OPEN_BROWSER` | `true` | Open browser on start |

## Build status

Following `SPEC.md` milestones:

- **M1** — Skeleton & config (current)
- M2 — Onboarding + Telegram echo
- M3 — Flow engine core
- M4 — Flow builder UI
- M5 — AI agent node
- M6 — Inbox & polish

## License

MIT
