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
import urllib.parse
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
DEV_KEY = os.environ.get("DEV_KEY", "bb-huge-dev-key-change-me")
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


def api_put(path, b):
    return _req("PUT", path, b)


def api_delete(path):
    return _req("DELETE", path)


def _qs(params: dict) -> str:
    clean = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        clean[key] = value
    return urllib.parse.urlencode(clean, doseq=True)


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
    {
        "name": "bb_get_context",
        "description": "Retrieve pre-hunt context / Q&A data for a program. Call this at the start of a session to see if the user has already answered the pre-hunt questionnaire.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id"],
            "properties": {
                "program_id": {
                    "type": "integer",
                    "description": "Program ID",
                },
            },
        },
    },
    {
        "name": "bb_save_context",
        "description": "Save pre-hunt context / Q&A answers for a program. Use this after the questioning phase to persist the user's responses so they are never asked again.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id", "data"],
            "properties": {
                "program_id": {
                    "type": "integer",
                    "description": "Program ID",
                },
                "data": {
                    "type": "object",
                    "description": "Key-value pairs of context data collected from the user",
                },
            },
        },
    },
    {
        "name": "bb_get_program_brief",
        "description": "Get a compact briefing for a program: scope, saved context, recent findings, recent recon, open observations, and open hypotheses.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id"],
            "properties": {
                "program_id": {
                    "type": "integer",
                    "description": "Program ID",
                }
            },
        },
    },
    {
        "name": "bb_log_observation",
        "description": "Log a low-confidence signal or odd behavior under a program without creating a full finding yet.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id", "title"],
            "properties": {
                "program_id": {"type": "integer"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": [
                        "behavior",
                        "auth",
                        "access_control",
                        "input_handling",
                        "business_logic",
                        "rate_limit",
                        "recon",
                        "other",
                    ],
                    "default": "other",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "testing", "closed", "promoted"],
                    "default": "open",
                },
                "agent": {"type": "string"},
                "source_tool": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
            },
        },
    },
    {
        "name": "bb_log_hypothesis",
        "description": "Log a stronger candidate vulnerability under a program before promoting it to a full finding.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id", "title"],
            "properties": {
                "program_id": {"type": "integer"},
                "observation_id": {"type": "integer"},
                "title": {"type": "string"},
                "weakness_hint": {"type": "string"},
                "cwe": {"type": "string"},
                "severity_hint": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational"],
                },
                "attack_path": {"type": "string"},
                "impact_hypothesis": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": [
                        "open",
                        "testing",
                        "confirmed",
                        "rejected",
                        "duplicate",
                        "promoted",
                    ],
                    "default": "open",
                },
                "agent": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
            },
        },
    },
    {
        "name": "bb_attach_http_pair",
        "description": "Attach a structured HTTP request/response evidence record to a program and optionally link it to a finding, hypothesis, or observation.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id"],
            "properties": {
                "program_id": {"type": "integer"},
                "finding_id": {"type": "integer"},
                "hypothesis_id": {"type": "integer"},
                "observation_id": {"type": "integer"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "request_method": {"type": "string"},
                "request_url": {"type": "string"},
                "request_headers": {"type": "object"},
                "request_body_text": {"type": "string"},
                "response_status": {"type": "integer"},
                "response_headers": {"type": "object"},
                "response_body_text": {"type": "string"},
                "account_label": {"type": "string"},
                "auth_type": {"type": "string"},
                "source_tool": {"type": "string"},
                "occurred_at": {
                    "type": "string",
                    "description": "ISO-8601 timestamp when the exchange occurred",
                },
            },
        },
    },
    {
        "name": "bb_check_existing_work",
        "description": "Check for likely duplicate or related work across findings, observations, and hypotheses before creating a new record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "program_id": {"type": "integer"},
                "target": {"type": "string"},
                "title": {"type": "string"},
                "cwe": {"type": "string"},
                "description": {"type": "string"},
            },
        },
    },
    {
        "name": "bb_promote_observation",
        "description": "Promote an observation into a linked hypothesis when the signal becomes a serious candidate bug.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "weakness_hint": {"type": "string"},
                "cwe": {"type": "string"},
                "severity_hint": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational"],
                },
                "attack_path": {"type": "string"},
                "impact_hypothesis": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": [
                        "open",
                        "testing",
                        "confirmed",
                        "rejected",
                        "duplicate",
                        "promoted",
                    ],
                },
                "agent": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
        },
    },
    {
        "name": "bb_promote_hypothesis",
        "description": "Promote a hypothesis into a linked finding once the issue is mature enough for the main findings list.",
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
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "description": {"type": "string"},
                "poc": {"type": "string"},
            },
        },
    },
    {
        "name": "bb_generate_report_context",
        "description": "Get a report-ready context pack for a finding, including linked hypothesis data, evidence summary, attachments, notes, and unresolved gaps.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer", "description": "Finding ID"},
            },
        },
    },
    {
        "name": "bb_list_assets",
        "description": "List assets (domains, subdomains, API hosts, etc.) for a program.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id"],
            "properties": {
                "program_id": {"type": "integer"},
                "kind": {
                    "type": "string",
                    "enum": ["domain", "subdomain", "api_host", "mobile_app", "repo", "other"],
                    "description": "Filter by asset kind",
                },
            },
        },
    },
    {
        "name": "bb_add_asset",
        "description": "Add an asset (domain, subdomain, API host, etc.) to a program.",
        "inputSchema": {
            "type": "object",
            "required": ["program_id", "kind", "identifier"],
            "properties": {
                "program_id": {"type": "integer"},
                "kind": {
                    "type": "string",
                    "enum": ["domain", "subdomain", "api_host", "mobile_app", "repo", "other"],
                },
                "identifier": {"type": "string", "description": "Domain, URL, or identifier"},
                "environment": {
                    "type": "string",
                    "enum": ["prod", "staging", "dev", "test", "unknown"],
                    "default": "unknown",
                },
                "notes": {"type": "string"},
                "active": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "bb_update_asset",
        "description": "Update an existing asset's fields.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "kind": {
                    "type": "string",
                    "enum": ["domain", "subdomain", "api_host", "mobile_app", "repo", "other"],
                },
                "identifier": {"type": "string"},
                "environment": {
                    "type": "string",
                    "enum": ["prod", "staging", "dev", "test", "unknown"],
                },
                "notes": {"type": "string"},
                "active": {"type": "boolean"},
            },
        },
    },
    {
        "name": "bb_delete_asset",
        "description": "Delete an asset and all its associated endpoints.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_list_endpoints",
        "description": "List endpoints under an asset (API routes, web paths, etc.).",
        "inputSchema": {
            "type": "object",
            "required": ["asset_id"],
            "properties": {
                "asset_id": {"type": "integer"},
                "method": {"type": "string", "description": "Filter by HTTP method e.g. GET"},
            },
        },
    },
    {
        "name": "bb_add_endpoint",
        "description": "Add an endpoint (URL path, API route) under an asset.",
        "inputSchema": {
            "type": "object",
            "required": ["asset_id", "method", "path"],
            "properties": {
                "asset_id": {"type": "integer"},
                "method": {"type": "string", "default": "GET"},
                "path": {"type": "string", "description": "URL path e.g. /api/users"},
                "protocol": {
                    "type": "string",
                    "enum": ["http", "https", "graphql", "ws", "wss", "other"],
                    "default": "https",
                },
                "content_type": {"type": "string", "description": "e.g. application/json"},
                "auth_required": {"type": "boolean"},
                "discovered_by": {"type": "string", "description": "Tool or agent that found this"},
                "notes": {"type": "string"},
            },
        },
    },
    {
        "name": "bb_update_endpoint",
        "description": "Update an existing endpoint's fields.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "method": {"type": "string"},
                "path": {"type": "string"},
                "protocol": {
                    "type": "string",
                    "enum": ["http", "https", "graphql", "ws", "wss", "other"],
                },
                "content_type": {"type": "string"},
                "auth_required": {"type": "boolean"},
                "discovered_by": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
    },
    {
        "name": "bb_delete_endpoint",
        "description": "Delete an endpoint.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_update_program",
        "description": "Update an existing program's fields (name, platform, scope, etc.).",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "platform": {"type": "string"},
                "program_url": {"type": "string"},
                "logo_url": {"type": "string"},
                "scope_in": {"type": "string"},
                "scope_out": {"type": "string"},
                "notes": {"type": "string"},
                "active": {"type": "boolean"},
            },
        },
    },
    {
        "name": "bb_delete_program",
        "description": "Delete a program and all its associated records (cascade).",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_update_observation",
        "description": "Update an existing observation's fields.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": [
                        "behavior",
                        "auth",
                        "access_control",
                        "input_handling",
                        "business_logic",
                        "rate_limit",
                        "recon",
                        "other",
                    ],
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "testing", "closed", "promoted"],
                },
                "agent": {"type": "string"},
                "source_tool": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
        },
    },
    {
        "name": "bb_delete_observation",
        "description": "Delete an observation.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_update_hypothesis",
        "description": "Update an existing hypothesis's fields.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
                "weakness_hint": {"type": "string"},
                "cwe": {"type": "string"},
                "severity_hint": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "informational"],
                },
                "attack_path": {"type": "string"},
                "impact_hypothesis": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": [
                        "open",
                        "testing",
                        "confirmed",
                        "rejected",
                        "duplicate",
                        "promoted",
                    ],
                },
                "agent": {"type": "string"},
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
            },
        },
    },
    {
        "name": "bb_delete_hypothesis",
        "description": "Delete a hypothesis.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_delete_recon",
        "description": "Delete a recon entry.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
            },
        },
    },
    {
        "name": "bb_delete_note",
        "description": "Delete a note from a finding.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
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
        qs = _qs(args)
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
        qs = _qs(args)
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

    elif name == "bb_get_context":
        return api_get(f"/programs/{args['program_id']}/context")

    elif name == "bb_save_context":
        pid = args.pop("program_id")
        return api_put(f"/programs/{pid}/context", {"data": args})

    elif name == "bb_get_program_brief":
        return api_get(f"/programs/{args['program_id']}/brief")

    elif name == "bb_log_observation":
        pid = args.pop("program_id")
        return api_post(f"/programs/{pid}/observations", args)

    elif name == "bb_log_hypothesis":
        pid = args.pop("program_id")
        return api_post(f"/programs/{pid}/hypotheses", args)

    elif name == "bb_attach_http_pair":
        payload = {"evidence_type": "http_exchange"}
        payload.update(args)
        return api_post("/evidence", payload)

    elif name == "bb_check_existing_work":
        return api_post("/similarity/check", args)

    elif name == "bb_promote_observation":
        oid = args.pop("id")
        return api_post(f"/observations/{oid}/promote", args)

    elif name == "bb_promote_hypothesis":
        hid = args.pop("id")
        return api_post(f"/hypotheses/{hid}/promote", args)

    elif name == "bb_generate_report_context":
        return api_get(f"/findings/{args['id']}/report-pack")

    elif name == "bb_list_assets":
        pid = args.pop("program_id")
        qs = _qs(args)
        return api_get(f"/programs/{pid}/assets{'?' + qs if qs else ''}")

    elif name == "bb_add_asset":
        pid = args.pop("program_id")
        return api_post(f"/programs/{pid}/assets", args)

    elif name == "bb_update_asset":
        aid = args.pop("id")
        return api_patch(f"/assets/{aid}", args)

    elif name == "bb_delete_asset":
        return api_delete(f"/assets/{args['id']}")

    elif name == "bb_list_endpoints":
        aid = args.pop("asset_id")
        qs = _qs(args)
        return api_get(f"/assets/{aid}/endpoints{'?' + qs if qs else ''}")

    elif name == "bb_add_endpoint":
        aid = args.pop("asset_id")
        return api_post(f"/assets/{aid}/endpoints", args)

    elif name == "bb_update_endpoint":
        eid = args.pop("id")
        return api_patch(f"/endpoints/{eid}", args)

    elif name == "bb_delete_endpoint":
        return api_delete(f"/endpoints/{args['id']}")

    elif name == "bb_update_program":
        pid = args.pop("id")
        return api_patch(f"/programs/{pid}", args)

    elif name == "bb_delete_program":
        return api_delete(f"/programs/{args['id']}")

    elif name == "bb_update_observation":
        oid = args.pop("id")
        return api_patch(f"/observations/{oid}", args)

    elif name == "bb_delete_observation":
        return api_delete(f"/observations/{args['id']}")

    elif name == "bb_update_hypothesis":
        hid = args.pop("id")
        return api_patch(f"/hypotheses/{hid}", args)

    elif name == "bb_delete_hypothesis":
        return api_delete(f"/hypotheses/{args['id']}")

    elif name == "bb_delete_recon":
        return api_delete(f"/recon/{args['id']}")

    elif name == "bb_delete_note":
        return api_delete(f"/notes/{args['id']}")

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
