# bb-huge 🤗

> Personal bug bounty findings portal — powered by Flask + Jinja, with MCP server support for AI agents.

---

<!-- Demo Video -->
<video src="https://github.com/user-attachments/assets/02aaa777-1fd0-41f2-9dd1-5dee021fcb6a"
       autoplay
       loop
       muted
       playsinline
       controls
       width="100%">
</video>


## Features

- **Dashboard** — stats by severity, status, and agent; recent findings table
- **Findings list** — filter by severity / status / agent / platform, full-text search, CSV export
- **Finding detail** — rendered Markdown description & PoC, attachment management, quick status update
- **Add / Edit form** — EasyMDE Markdown editor, file uploads, CWE & CVSS fields
- **8 Bug-bounty statuses** — `discovered → debugging → confirmed → reported → rewarded / denied / duplicate / n/a`
- **REST API** — full CRUD via `/api/v1/` secured by dev key header
- **MCP stdio server** — plug into gemini-cli, claude-code, codex or any MCP client
- **Gemini CLI skill** — auto-logs findings during recon sessions
- **Docker** — single `docker compose up` to run

---

## Quick Start

### 1. Clone & configure

```bash
git clone <your-repo>
cd bb-huge
cp .env.example .env
# Edit .env — set SECRET_KEY and DEV_KEY
```

### 2a. Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000 and enter your `DEV_KEY`.

### 2b. Run with Docker

```bash
docker compose up -d
```

---

## MCP Server — Connect your agent

The MCP server (`mcp_server.py`) uses **stdio transport** and is compatible with any MCP client.

### gemini-cli

Add to `.gemini/settings.json` (project-local or `~/.gemini/settings.json`):

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

### claude-code

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

See `mcp_config_examples.txt` for codex and other agents.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `bb_create_finding` | Create a new finding |
| `bb_list_findings` | List/search findings |
| `bb_get_finding` | Get full finding details |
| `bb_update_finding` | Update any field |
| `bb_update_status` | Quick status update |
| `bb_delete_finding` | Delete a finding |
| `bb_get_stats` | Overall statistics |

### Test MCP manually

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  DEV_KEY=your-dev-key python mcp_server.py
```

---

## Gemini CLI Skill

Copy the skill folder to your Gemini CLI skills directory:

```bash
cp -r .gemini/skills/bb-huge ~/.gemini/skills/
```

Or keep it project-local (`.gemini/skills/bb-huge/`) — gemini-cli picks it up automatically.

The skill tells the agent to:
- Auto-log findings during recon with `bb_create_finding`
- Update status as you progress through the workflow
- Use correct severity and CWE classification

---

## REST API

All endpoints require `X-Dev-Key: <your-key>` header.

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

### Example

```bash
# Create a finding
curl -X POST http://localhost:5000/api/v1/findings \
  -H "X-Dev-Key: your-dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Reflected XSS in search",
    "target": "app.example.com",
    "platform": "HackerOne",
    "severity": "high",
    "agent": "gemini-cli",
    "cwe": "CWE-79",
    "cvss": 7.2
  }'

# Update status
curl -X PATCH http://localhost:5000/api/v1/findings/1/status \
  -H "X-Dev-Key: your-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"status": "confirmed"}'

# Get stats
curl http://localhost:5000/api/v1/stats \
  -H "X-Dev-Key: your-dev-key"
```

---

## Project Structure

```
bb-huge/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Finding + Attachment models
│   ├── routes/
│   │   ├── auth.py          # Login / logout
│   │   ├── findings.py      # CRUD + upload
│   │   └── api.py           # REST API
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── auth/login.html
│   │   └── findings/
│   │       ├── list.html
│   │       ├── detail.html
│   │       └── form.html
│   └── static/uploads/
├── mcp_server.py            # MCP stdio server
├── .gemini/skills/bb-huge/  # Gemini CLI skill
│   ├── SKILL.md
│   └── scripts/bb.py
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Status Workflow

```
discovered → debugging → confirmed → reported → rewarded 💰
                                  ↘ denied ❌
              ↘ duplicate 🔁
              ↘ n/a ➖
```

---

## License

Personal use. Do whatever you want with it. Hunt bugs, get paid. 🤗
