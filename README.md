# bb-huge 🤗

> `/bb-huge` — one command. Senior Bug Hunter, loaded.

Not a portal. A **Context Engineering Architecture** that converts your AI agent into a disciplined bug bounty hunter with a single slash command. The web UI is just the visible tip — the real power is what happens inside the agent's brain when the skill fires.

<!-- Demo Video -->
<video src="https://github.com/user-attachments/assets/02aaa777-1fd0-41f2-9dd1-5dee021fcb6a"
       autoplay loop muted playsinline controls width="100%">
</video>

---

## The Architecture — What's Actually Happening

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR AI AGENT                             │
│  (gemini-cli / claude-code / codex / emmu / any MCP client) │
└──────────┬─────────────────────────────────────┬────────────┘
           │  "/bb-huge"                         │  "find bugs on
           │  triggers skill                     │   example.com"
           ▼                                     ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│  SKILL.md (207 lines)    │    │  MCP stdio Server            │
│  • Senior Bug Hunter     │    │  • 12+ tools (CRUD + more)   │
│    persona injected      │    │  • stdio transport           │
│  • 4 SOPs loaded         │◄──►│  • stateless, fast           │
│  • Severity/Status refs  │    │  • any agent, same API       │
└──────────┬───────────────┘    └──────────┬───────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│  references/ (6 files)   │    │  PORTAL (Flask + SQLite)     │
│  • bb-orchestrator.md    │    │  • Dashboard, Charts         │
│  • bb-operator.md        │    │  • Findings CRUD             │
│  • bb-recon.md           │    │  • Programs tracking         │
│  • bb-eligible-vulns.md  │    │  • Attachments               │
│  • bb-standards.md       │    │  • Webhooks (Discord/TG)     │
│  • bb-report-templates   │    │  • REST API v1               │
└──────────────────────────┘    └──────────────────────────────┘
```

Two systems, one interface. The **skill layer** gives the agent knowledge & discipline. The **portal layer** gives it persistent memory. They never touch each other — they communicate through MCP.

---

## Why This Works (The Insight)

Every bug hunter has the same problem: **context resets to zero every session**.

You spend 30 minutes re-reading your own notes, re-downloading attachments, trying to remember where you left off. Between sessions, you forget the half-baked hypothesis, the endpoint you were about to fuzz, the parameter that looked interesting.

bb-huge fixes this at the architectural level:

| Problem | How bb-huge solves it |
|---------|----------------------|
| Agent forgets between sessions | Portal stores everything — findings, notes, attachments, status |
| You forget the methodology | Skill injects Senior Bug Hunter SOPs into every new session |
| You waste time on setup | `/bb-huge` command boots everything in one call |
| You skip logging "small" things | Skill enforces *capture-first* discipline |
| Multiple agents, no coordination | Each agent sets its own `agent` field, stats show all activity |
| Writing reports is painful | 5 ready-to-use templates (XSS, SQLi, IDOR, SSRF, Stored XSS) |
| Scope confusion | Standards reference loaded at session start |

---

## What `/bb-huge` Actually Loads

When you type the command, the agent's brain gets injected with:

```mermaid
graph TB
    C["/bb-huge command"] --> SKILL[SKILL.md]
    SKILL --> SOP1["SOP-1: New Target<br/>Recon setup, skill roster"]
    SKILL --> SOP2["SOP-2: Vulnerability Found<br/>Capture-first protocol"]
    SKILL --> SOP3["SOP-3: Resume Finding<br/>Restore full context"]
    SKILL --> SOP4["SOP-4: End Session<br/>Closeout checklist"]
    SKILL --> MCP["12 MCP Tools<br/>Create, Read, Update,<br/>Upload, Notify, Stats"]
    SKILL --> REFS["Reference Library"]
    REFS --> ORCH[bb-orchestrator.md<br/>Routing & coordination]
    REFS --> OP[bb-operator.md<br/>Hunting methodology]
    REFS --> RECON[bb-recon.md<br/>Recon playbook]
    REFS --> VULNS[bb-eligible-vulnerabilities.md<br/>Vulnerability taxonomy]
    REFS --> STD[bb-standards.md<br/>Scope & platform rules]
    REFS --> TEMPLATES[bb-report-templates.md<br/>Ready-to-fill templates]

    style C fill:#4a9,color:#fff
    style SKILL fill:#67b,color:#fff
    style MCP fill:#956,color:#fff
    style REFS fill:#567,color:#fff
```

**~1,300 lines of bug bounty knowledge** — every session. The reference library is lazy-loaded (you only pull what you need), but the core skill & tools are always there.

---

## I WANT TO...

<details>
<summary><strong>🚀 Set up bb-huge right now</strong></summary>

### Quick Start

```bash
git clone <your-repo>
cd bb-huge
cp .env.example .env
# Edit .env — set SECRET_KEY and DEV_KEY
```

#### Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

#### Or with Docker
```bash
docker compose up -d
```

Open [http://localhost:5000](http://localhost:5000) — enter your `DEV_KEY`.

</details>

<details>
<summary><strong>🤖 Connect my AI agent to bb-huge</strong></summary>

The MCP server (`mcp_server.py`) uses stdio transport. Any MCP-compatible agent connects in seconds.

#### gemini-cli

Add to `.gemini/settings.json` (project or global):

```json
{
  "mcpServers": {
    "bb-huge": {
      "command": "python",
      "args": ["/absolute/path/to/bb-huge/mcp_server.py"],
      "env": {
        "DEV_KEY": "your-dev-key",
        "BB_HUGE_URL": "http://127.0.0.1:5000"
      }
    }
  }
}
```

#### claude-code

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bb-huge": {
      "command": "python",
      "args": ["/absolute/path/to/bb-huge/mcp_server.py"],
      "env": {
        "DEV_KEY": "your-dev-key",
        "BB_HUGE_URL": "http://127.0.0.1:5000"
      }
    }
  }
}
```

See `mcp_config_examples.txt` for codex, emmu, and other agents.

</details>

<details>
<summary><strong>🧠 Load the Senior Bug Hunter skill</strong></summary>

Copy the skill into your agent's skill directory:

```bash
cp -r skills/bb-huge ~/.gemini/skills/
# Project-local also works: .gemini/skills/bb-huge/
```

Now every time you type `/bb-huge`, the agent loads:
- Senior Bug Hunter persona with capture-first discipline
- 4 Standard Operating Procedures (SOP-1 through SOP-4)
- Full severity & status reference
- 6 reference files (600+ lines of methodology)
- 12 MCP tools wired to your portal

**The agent doesn't just "know about" bug bounty. It becomes a bug bounty hunter.**

</details>

<details>
<summary><strong>📝 Log a finding immediately</strong></summary>

From your agent:

```
bb_create_finding(title="IDOR on /api/users", target="api.example.com", severity="high")
```

That's it. The MCP server routes it to the portal. No browser, no forms, no friction.

The skill's **#1 rule**: *capture first, enrich later*. A thin entry now beats a perfect entry that never gets written. Fill in CWE, CVSS, PoC, and description as evidence accumulates.

```mermaid
graph LR
    A["Vulnerability Spotted"] --> B["bb_create_finding<br/>(status: discovered)"]
    B --> C["bb_upload_attachment<br/>(evidence files)"]
    C --> D["bb_update_finding<br/>(append PoC)"]
    D --> E["bb_update_status<br/>(confirmed)"]
    E --> F["bb_update_status<br/>(reported 🎯)"]
    F --> G["bb_update_status<br/>(rewarded 💰)"]

    style A fill:#c44,color:#fff
    style G fill:#4a4,color:#fff
```

</details>

<details>
<summary><strong>🔍 Search and review findings</strong></summary>

```bash
# From terminal (CLI script)
python skills/bb-huge/scripts/bb.py list --severity critical --status confirmed

# From agent
bb_list_findings(q="xss", severity="high")

# Get full detail
bb_get_finding(id=42)
```

Or open the web UI: [http://localhost:5000/findings](http://localhost:5000/findings) — filter by severity, status, agent, platform. Full-text search. CSV export.

</details>

<details>
<summary><strong>📊 See my stats at a glance</strong></summary>

```bash
# From agent
bb_get_stats()

# From terminal
python skills/bb-huge/scripts/bb.py stats
```

Returns totals by severity, status, and agent. The dashboard also renders bar charts for each dimension.

</details>

<details>
<summary><strong>📎 Attach evidence to a finding</strong></summary>

```bash
# From agent
bb_upload_attachment(id=42, file_path="./burp_request.txt")

# From terminal
python skills/bb-huge/scripts/bb-dump-attachments.py 42
```

Both scripts pull auth from environment variables (`BB_HUGE_URL`, `DEV_KEY`). No credentials hardcoded. Ever.

</details>

<details>
<summary><strong>🔄 Resume work on a previous finding</strong></summary>

SOP-3 handles this. The agent:

1. `bb_get_finding(42)` — reads current state
2. `python scripts/bb-dump-attachments.py 42` — pulls all evidence to local disk
3. Reads every attachment to restore full context
4. Gives you a one-paragraph summary of where things stand before you continue

Zero context loss between sessions. Even between different agents.

</details>

<details>
<summary><strong>📬 Get notified when things happen</strong></summary>

The portal supports **Discord** and **Telegram** webhooks. Configure in Settings → Webhooks.

The agent can notify on any event:

```bash
bb_notify(event="finding.confirmed", payload={"title": "RCE on admin panel", "message": "Go write the report!"})
```

Webhooks fire automatically on create/status-change if configured.

</details>

<details>
<summary><strong>📋 Track multiple programs</strong></summary>

Programs are first-class citizens. Each program tracks:

- Platform (HackerOne, Bugcrowd, Intigriti, private)
- Scope rules (in-scope / out-of-scope)
- Findings linked to it
- Recon entries (subdomains, endpoints, technologies, parameters)

```bash
bb_create_program(name="Acme Corp", platform="HackerOne")
bb_add_recon(program_id=1, category="subdomain", value="admin.acme.com", source="subfinder")
bb_list_programs()
```

</details>

<details>
<summary><strong>🔌 Use the REST API directly</strong></summary>

All endpoints require `X-Dev-Key` header.

```
GET    /api/v1/stats
GET    /api/v1/findings?q=&severity=&status=&agent=&limit=&offset=
POST   /api/v1/findings
GET    /api/v1/findings/<id>
PATCH  /api/v1/findings/<id>
PATCH  /api/v1/findings/<id>/status
DELETE /api/v1/findings/<id>
GET    /api/v1/enums
```

Example:

```bash
curl -X POST http://localhost:5000/api/v1/findings \
  -H "X-Dev-Key: your-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"title":"Reflected XSS in search","target":"app.example.com","severity":"high","cwe":"CWE-79","cvss":7.2}'
```

</details>

<details>
<summary><strong>🧪 Test MCP manually</strong></summary>

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  DEV_KEY=your-dev-key python mcp_server.py
```

Expect a JSON-RPC response with server capabilities. You can then pipe `tools/list` and `tools/call` messages.

</details>

<details>
<summary><strong>🐳 Run everything in Docker</strong></summary>

```bash
docker compose up -d
```

That's the whole command. The `Dockerfile` + `docker-compose.yml` handle the rest. Portal on `:5000`, ready to connect.

</details>

---

## Everything in the Box

```
bb-huge/
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── models.py              # 6 models: Finding, Attachment, Program,
│   │                          #   ReconEntry, Note, WebhookConfig
│   ├── routes/
│   │   ├── auth.py            # Login / logout
│   │   ├── findings.py        # Web UI: CRUD, upload, CSV export
│   │   ├── api.py             # REST API v1 (full CRUD + extras)
│   │   ├── programs.py        # Program management
│   │   └── settings.py        # Webhooks, notes
│   ├── utils.py               # File validation, webhook dispatch
│   ├── templates/             # 11 Jinja2 templates (dark theme)
│   └── static/uploads/        # Attachment storage
├── skills/bb-huge/
│   ├── SKILL.md               # The brain — 207 lines of agent instruction
│   ├── references/
│   │   ├── bb-orchestrator.md         # Multi-skill routing & coordination
│   │   ├── bb-operator.md             # Full hunting methodology
│   │   ├── bb-recon.md                # Recon playbook + tool commands
│   │   ├── bb-eligible-vulnerabilities.md  # Vulnerability taxonomy & CWE ref
│   │   ├── bb-standards.md            # Scope rules, platform policies
│   │   └── bb-report-templates.md     # 5 ready-to-fill report templates
│   └── scripts/
│       ├── bb.py                      # CLI helper (stats/list/get/create/status)
│       ├── bb-dump-attachments.py     # Download all evidence for a finding
│       └── bb-orchestrator-list-skills.py  # Print available skill roster
├── mcp_server.py              # MCP stdio server (12+ tools)
├── config.py                  # App configuration
├── run.py                     # Entry point (Waitress)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## License

Personal use. Do whatever you want. Hunt bugs, get paid. 🤗
