# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

bb-huge is two things wired together over MCP:

1. **Portal** (`app/`) — a Flask + SQLAlchemy (SQLite) web app that stores bug bounty findings,
   programs, recon data, observations/hypotheses, evidence, assets, and endpoints. It has a
   dashboard UI and a REST API.
2. **Skill layer** (`skills/bb-huge/`) — a `SKILL.md` persona + reference docs that, when loaded
   into an AI agent (Claude Code, gemini-cli, codex, etc.), turns it into a disciplined bug bounty
   hunter that calls the portal's API via MCP tools as it works.

`mcp_server.py` is the bridge: a stdio MCP server that translates ~35 MCP tool calls
(`bb_create_finding`, `bb_get_program_brief`, ...) into REST calls against the running Flask portal.
Any MCP-compatible agent can drive the portal through it.

`skills/curated/` is a separate, large (350+) bundle of community security skills (per vuln class,
per platform, per technique) that get lazy-loaded on demand — not core to the portal itself.

## Running the portal

```bash
cp .env.example .env        # set SECRET_KEY and DEV_KEY before anything else
python -m venv .venv && source .venv/bin/activate   # (or .venv\Scripts\activate on Windows)
pip install -r requirements.txt
python run.py                # serves on :5000 (waitress in prod, Flask dev server if FLASK_DEBUG=1)
```

Docker: `docker compose up -d` (same port).

Auth is a single shared `DEV_KEY`, not per-user accounts:
- Web UI: session cookie set via `/login` (form posts `dev_key`, compared in `app/routes/auth.py`).
- REST API: `X-Dev-Key` header (or `?dev_key=`) checked in `app/routes/api.py`, required on every
  `/api/v1/*` call.

## Tests

```bash
python -m unittest tests/test_api.py -v          # whole file
python -m unittest tests.test_api.V2ApiTests.test_program_brief_includes_new_entities  # single test
```

Tests spin up a real `create_app()` instance against a temp SQLite DB + temp upload dir per test
(see `TestConfig` / `setUp` in `tests/test_api.py`) — no mocking of the DB layer. Follow this pattern
(fresh app + tempdir per test) for new API tests rather than reusing a shared instance.

## Architecture inside `app/`

- `app/__init__.py` — app factory (`create_app`). Registers all blueprints, runs `db.create_all()`
  and `run_migrations()` on every startup (see below), and injects sidebar stats into every template
  via `context_processor`.
- `app/models.py` — all 11 models in one file (`Finding`, `Program`, `Attachment`, `ReconEntry`,
  `Note`, `WebhookConfig`, `TargetContext`, `Observation`, `Hypothesis`, `EvidenceRecord`, `Asset`,
  `Endpoint`), plus the enum-like constants (`SEVERITIES`, `STATUSES`, `AGENTS`, `PLATFORMS`,
  `RECON_CATEGORIES`, `WEBHOOK_EVENTS`, `ASSET_KINDS`, ...) and color-mapping dicts used by Jinja.
- `app/migrations.py` — hand-rolled additive schema migrations (no Alembic). Runs automatically on
  every app start inside `create_app()`. When adding a column/table, add a migration function here
  rather than relying on `db.create_all()` alone (it won't alter existing tables).
- `app/routes/`:
  - `auth.py` — dev-key login/logout, session-based `login_required` decorator for UI routes.
  - `findings.py` — web UI CRUD for findings (list/detail/form/upload/CSV export/report-pack).
  - `programs.py` — web UI + logic for programs and their nested entities (observations,
    hypotheses, evidence, assets, recon).
  - `api.py` (~2000 lines) — the entire REST API (`/api/v1/...`, ~45 endpoints), all gated by the
    `X-Dev-Key` check at the top of the file. This is what `mcp_server.py` talks to exclusively —
    UI routes in `findings.py`/`programs.py` are session-authed and not used by the MCP layer.
  - `settings.py` — webhook config (Discord/Telegram) and note management.
- `app/utils.py` — upload validation and webhook dispatch (fired on finding create/status-change
  events defined in `WEBHOOK_EVENTS`).

## The data model / signal pipeline

Findings aren't the only unit of record. There's a deliberate promotion chain used to capture
partial signal before it's a confirmed bug:

```
Observation (raw signal) --promote--> Hypothesis (candidate) --promote--> Finding (confirmed)
```

Each promoted record keeps a back-reference to where it came from, so a Finding can trace back
through its Hypothesis to the original Observation and any linked EvidenceRecord. Programs, Assets,
and Endpoints are separate first-class entities that findings/recon attach to — a Program has many
Assets, an Asset has many Endpoints, and ReconEntry rows (subdomains, params, credentials, tech)
hang off a Program directly.

Findings also carry a `field` (`web` / `mobile` / `binary` / `source_code`) that determines which
methodology/report-template reference the skill layer loads — this is not just metadata, it changes
agent behavior (see `skills/bb-huge/SKILL.md` "FIELD DISPATCH").

## `mcp_server.py`

- stdio transport; **all logging goes to `mcp_server.log`**, never stdout/stderr, because MCP
  clients (gemini-cli etc.) treat any non-JSON on stdout as a protocol error and drop the connection.
  If you add debug output, use the `logging` module already configured here — never `print()`.
- Every tool function is a thin wrapper that calls `api_get/api_post/api_patch/api_put/api_delete`
  against `BB_HUGE_URL` (default `http://127.0.0.1:5000`) with the `DEV_KEY` env var — it has no
  direct DB access and no business logic of its own. If the API shape changes in `app/routes/api.py`,
  update the corresponding tool wrapper here.
- Requires the Flask portal to already be running (`python run.py`) — the MCP server is just an API
  client, not a standalone service.

## Editing the skill layer (`skills/bb-huge/`)

- `SKILL.md` is the persona + SOPs (SOP-0 through SOP-6) loaded into an agent's context on
  `/bb-huge`. It's long (~1000 lines) and prescriptive by design — read it before changing agent
  behavior, since instructions like "capture first, enrich later" and the field-dispatch table are
  load-bearing for how findings get logged.
- `skills/bb-huge/references/*.md` are lazy-loaded reference docs (methodology per field, report
  templates per field, recon playbook, standards, scheduled-mission routing). Keep new methodology
  content here rather than growing `SKILL.md` further.
- `skills/bb-huge/scripts/bb.py` and `bb-dump-attachments.py` are standalone CLI helpers that hit the
  same `/api/v1` REST API using `BB_HUGE_URL`/`DEV_KEY` env vars — same auth contract as
  `mcp_server.py`.
