#!/usr/bin/env python3
"""
bb-huge MCP Server (stdio transport)
Exposes Finding CRUD tools so any MCP-compatible agent (gemini-cli, claude-code, etc.)
can create, read, update, and search findings directly.

Usage:
    python mcp_server.py

Configure in your agent:
    gemini-cli:   add to .gemini/settings.json -> mcpServers
    claude-code:  add to claude_desktop_config.json -> mcpServers
"""

import json
import sys
import os
import urllib.request
import urllib.error
import logging
from typing import Any

# ── Silence ALL stderr output immediately ─────────────────────────────────────
# gemini-cli (and most MCP clients) treat ANY non-JSON on stdout as a protocol
# error and close the connection.  Route everything to a log file instead.
_LOG_FILE = os.environ.get(
    "BB_MCP_LOG",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.log"),
)
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
# Redirect stderr to the log file so Flask/urllib noise never hits the pipe
sys.stderr = open(_LOG_FILE, "a", buffering=1)

# ── Config ───────────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("BB_HUGE_URL", "http://127.0.0.1:5000")
DEV_KEY = os.environ.get("DEV_KEY", "shulkwisec_123")
HEADERS = {"Content-Type": "application/json", "X-Dev-Key": DEV_KEY}

# ── HTTP helpers ──────────────────────────────────────────────────────────────


def _req(method: str, path: str, body: dict = None) -> Any:
    url = f"{BASE_URL}/api/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


def api_get(path):
    return _req("GET", path)


def api_post(path, b):
    return _req("POST", path, b)


def api_patch(path, b):
    return _req("PATCH", path, b)


def api_delete(path):
    return _req("DELETE", path)


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "bb_create_finding",
        "description": (
            "Create a new bug bounty finding in bb-huge. "
            "Use this immediately when you discover a vulnerability."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["title", "target", "severity"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short descriptive title of the finding",
                },
                "target": {
                    "type": "string",
                    "description": "Target domain or program name",
                },
                "program_id": {
                    "type": "integer",
                    "description": "Program ID to link this finding to",
                },
                "platform": {
                    "type": "string",
                    "description": "Bug bounty platform (HackerOne, Bugcrowd, private…)",
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational"],
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "discovered",
                        "debugging",
                        "confirmed",
                        "reported",
                        "rewarded",
                        "denied",
                        "duplicate",
                        "n/a",
                    ],
                    "default": "discovered",
                },
                "agent": {
                    "type": "string",
                    "enum": [
                        "gemini-cli",
                        "claude-code",
                        "claude",
                        "codex",
                        "emmu",
                        "manual",
                        "other",
                    ],
                    "default": "gemini-cli",
                },
                "cwe": {"type": "string", "description": "CWE identifier e.g. CWE-79"},
                "cvss": {"type": "number", "description": "CVSS score 0-10"},
                "description": {
                    "type": "string",
                    "description": "Markdown description of the vulnerability",
                },
                "poc": {
                    "type": "string",
                    "description": "Markdown proof of concept and steps to reproduce",
                },
            },
        },
    },
    {
        "name": "bb_list_findings",
        "description": "List findings with optional filters. Returns id, title, severity, status, agent, target.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query"},
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational", ""],
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "discovered",
                        "debugging",
                        "confirmed",
                        "reported",
                        "rewarded",
                        "denied",
                        "duplicate",
                        "n/a",
                        "",
                    ],
                },
                "agent": {"type": "string", "description": "Filter by agent"},
                "limit": {"type": "integer", "default": 20},
                "offset": {"type": "integer", "default": 0},
            },
        },
    },
    {
        "name": "bb_get_finding",
        "description": "Get full details of a finding by id.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer", "description": "Finding id"},
            },
        },
    },
    {
        "name": "bb_update_finding",
        "description": "Update any fields of an existing finding.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "target": {"type": "string"},
                "platform": {"type": "string"},
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational"],
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "discovered",
                        "debugging",
                        "confirmed",
                        "reported",
                        "rewarded",
                        "denied",
                        "duplicate",
                        "n/a",
                    ],
                },
                "agent": {"type": "string"},
                "cwe": {"type": "string"},
                "cvss": {"type": "number"},
                "description": {"type": "string"},
                "poc": {"type": "string"},
            },
        },
    },
    {
        "name": "bb_update_status",
        "description": "Quickly update just the status of a finding.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "status"],
            "properties": {
                "id": {"type": "integer"},
                "status": {
                    "type": "string",
                    "enum": [
                        "discovered",
                        "debugging",
                        "confirmed",
                        "reported",
                        "rewarded",
                        "denied",
                        "duplicate",
                        "n/a",
                    ],
                },
            },
        },
    },
    {
        "name": "bb_delete_finding",
        "description": "Permanently delete a finding by id.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_get_stats",
        "description": "Get overall statistics: totals by severity, status, and agent.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bb_upload_attachment",
        "description": "Upload a file as an attachment to an existing finding.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "file_path"],
            "properties": {
                "id": {"type": "integer", "description": "Finding ID"},
                "file_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file on disk",
                },
            },
        },
    },
    {
        "name": "bb_search_similar",
        "description": (
            "Search for existing findings similar to what you're about to log. "
            "Call this before bb_create_finding to avoid duplicates."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target domain or program name",
                },
                "cwe": {"type": "string", "description": "CWE identifier e.g. CWE-79"},
                "title": {
                    "type": "string",
                    "description": "Keywords from the finding title",
                },
            },
        },
    },
    {
        "name": "bb_add_note",
        "description": "Add a note/comment to an existing finding without overwriting any field. Use this to log progress, dead ends, or partial findings.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "content"],
            "properties": {
                "id": {"type": "integer", "description": "Finding ID"},
                "content": {"type": "string", "description": "Markdown note content"},
                "agent": {
                    "type": "string",
                    "description": "Agent name (defaults to 'manual')",
                },
            },
        },
    },
    {
        "name": "bb_bulk_update_status",
        "description": "Update the status of multiple findings at once.",
        "inputSchema": {
            "type": "object",
            "required": ["ids", "status"],
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of finding IDs",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "discovered",
                        "debugging",
                        "confirmed",
                        "reported",
                        "rewarded",
                        "denied",
                        "duplicate",
                        "n/a",
                    ],
                },
            },
        },
    },
    {
        "name": "bb_notify",
        "description": "Send a notification to all configured webhooks (Discord/Telegram). Use to alert the user about important discoveries.",
        "inputSchema": {
            "type": "object",
            "required": ["payload"],
            "properties": {
                "event": {
                    "type": "string",
                    "description": "Event name e.g. finding.confirmed",
                    "default": "finding.created",
                },
                "payload": {
                    "type": "object",
                    "description": "Notification content",
                    "properties": {
                        "title": {"type": "string"},
                        "message": {"type": "string"},
                    },
                },
            },
        },
    },
    {
        "name": "bb_create_program",
        "description": "Create a new bug bounty program entry with scope and platform info.",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Program name e.g. Acme Corp",
                },
                "platform": {
                    "type": "string",
                    "description": "HackerOne, Bugcrowd, Intigriti, private…",
                },
                "program_url": {
                    "type": "string",
                    "description": "URL to the program page",
                },
                "scope_in": {
                    "type": "string",
                    "description": "In-scope rules (Markdown)",
                },
                "scope_out": {
                    "type": "string",
                    "description": "Out-of-scope rules (Markdown)",
                },
                "notes": {
                    "type": "string",
                    "description": "General notes about this program",
                },
            },
        },
    },
    {
        "name": "bb_list_programs",
        "description": "List all bug bounty programs with their stats.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "bb_add_recon",
        "description": "Add a recon entry (subdomain, endpoint, technology, parameter, etc.) to a program.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id", "value"],
            "properties": {
                "program_id": {"type": "integer"},
                "category": {
                    "type": "string",
                    "enum": [
                        "subdomain",
                        "endpoint",
                        "technology",
                        "parameter",
                        "credential",
                        "ip",
                        "other",
                    ],
                    "default": "subdomain",
                },
                "value": {
                    "type": "string",
                    "description": "The actual data (domain, URL, tech name…)",
                },
                "notes": {"type": "string"},
                "source": {
                    "type": "string",
                    "description": "Tool or agent that found this",
                },
            },
        },
    },
]


# ── MCP message handlers ──────────────────────────────────────────────────────


def handle_initialize(msg_id, params):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "bb-huge", "version": "1.0.0"},
        },
    }


def handle_tools_list(msg_id):
    return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}


def handle_tool_call(msg_id, params):
    name = params.get("name", "")
    args = params.get("arguments", {})

    try:
        result = dispatch(name, args)
    except Exception as e:
        result = {"error": str(e)}

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
        },
    }


def dispatch(name: str, args: dict) -> Any:
    if name == "bb_create_finding":
        return api_post("/findings", args)

    elif name == "bb_list_findings":
        qs = "&".join(f"{k}={v}" for k, v in args.items() if v)
        return api_get(f"/findings{'?' + qs if qs else ''}")

    elif name == "bb_get_finding":
        return api_get(f"/findings/{args['id']}")

    elif name == "bb_update_finding":
        fid = args.pop("id")
        return api_patch(f"/findings/{fid}", args)

    elif name == "bb_update_status":
        return api_patch(f"/findings/{args['id']}/status", {"status": args["status"]})

    elif name == "bb_delete_finding":
        return api_delete(f"/findings/{args['id']}")

    elif name == "bb_get_stats":
        return api_get("/stats")

    elif name == "bb_upload_attachment":
        import base64

        fid = args["id"]
        path = args["file_path"]
        try:
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            return api_post(
                f"/findings/{fid}/attachments",
                {"filename": os.path.basename(path), "content": content},
            )
        except Exception as e:
            return {"error": str(e)}

    elif name == "bb_search_similar":
        qs = "&".join(f"{k}={v}" for k, v in args.items() if v)
        return api_get(f"/findings/similar{'?' + qs if qs else ''}")

    elif name == "bb_add_note":
        fid = args.pop("id")
        return api_post(f"/findings/{fid}/notes", args)

    elif name == "bb_bulk_update_status":
        return api_patch("/findings/bulk/status", args)

    elif name == "bb_notify":
        return api_post("/notify", args)

    elif name == "bb_create_program":
        return api_post("/programs", args)

    elif name == "bb_list_programs":
        return api_get("/programs")

    elif name == "bb_add_recon":
        pid = args.pop("program_id")
        return api_post(f"/programs/{pid}/recon", args)

    else:
        return {"error": f"Unknown tool: {name}"}


# ── stdio loop ────────────────────────────────────────────────────────────────


def _send(obj: dict) -> None:
    """Write a single JSON-RPC response to stdout, always line-buffered."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    # Use binary stdin so we never hit codec/buffering issues on Windows either
    stdin = open(sys.stdin.fileno(), "rb", buffering=0)

    while True:
        try:
            raw = stdin.readline()
        except Exception as e:
            logging.error("stdin read error: %s", e)
            break

        if not raw:  # EOF — client closed the pipe
            break

        line = raw.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
            method = msg.get("method", "")
            mid = msg.get("id")
            logging.debug("→ %s id=%s", method, mid)

            if method == "initialize":
                _send(handle_initialize(mid, msg.get("params", {})))
            elif method == "tools/list":
                _send(handle_tools_list(mid))
            elif method == "tools/call":
                _send(handle_tool_call(mid, msg.get("params", {})))
            elif method in ("notifications/initialized", "notifications/cancelled"):
                pass  # fire-and-forget, no response needed
            elif mid is not None:
                _send(
                    {
                        "jsonrpc": "2.0",
                        "id": mid,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}",
                        },
                    }
                )

        except json.JSONDecodeError as e:
            logging.warning("bad JSON: %s | raw: %s", e, raw[:120])
        except Exception as e:
            logging.exception("unhandled error")
            try:
                _send(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": str(e)},
                    }
                )
            except Exception:
                pass


if __name__ == "__main__":
    main()
