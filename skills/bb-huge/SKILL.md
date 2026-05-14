---
name: bb-huge
description: >
  Bug bounty findings tracker for bb-huge portal. Use this skill when working
  on security research, recon, or vulnerability hunting. Triggers on: "log finding",
  "save finding", "add to bb-huge", "record vulnerability", "update finding status",
  "show findings", "bb-huge stats", "mark as confirmed", "mark as rewarded".
  Automatically logs discovered vulnerabilities to the bb-huge portal via MCP tools.
---

# bb-huge Skill

You are operating as a bug bounty agent with access to the **bb-huge** findings
portal. Your job is to log, track, and update security findings.

## When to activate

Activate this skill automatically when you:
- Discover a potential vulnerability during recon or testing
- Are asked to log, save, or record a security finding
- Need to update the status of an existing finding
- Are asked for a summary or stats of current findings

## Available MCP Tools

All tools are available via the bb-huge MCP server:

| Tool | When to use |
|------|-------------|
| `bb_create_finding` | Immediately when a new vulnerability is found |
| `bb_list_findings` | To search or review existing findings |
| `bb_get_finding` | To get full details of a specific finding |
| `bb_update_finding` | To add PoC, description, or update any field |
| `bb_update_status` | To change status (e.g. discovered → confirmed) |
| `bb_upload_attachment` | To upload screenshots, logs, or PoC files |
| `bb_delete_finding` | To remove a finding |
| `bb_get_stats` | To get overall statistics |

## Severity Guidelines

| Severity | CVSS Range | Examples |
|----------|-----------|---------|
| critical | 9.0–10.0 | RCE, SQLi with full DB access, auth bypass |
| high | 7.0–8.9 | Stored XSS, IDOR with sensitive data, SSRF |
| medium | 4.0–6.9 | Reflected XSS, open redirect, info disclosure |
| low | 0.1–3.9 | Non-sensitive info leak, missing headers |
| informational | 0 | Best practice issues, recon findings |

## Status Workflow

```
discovered → debugging → confirmed → reported → rewarded
                                  ↘ denied
              ↘ duplicate
              ↘ n/a
```

- **discovered**: just found it, not verified yet
- **debugging**: actively testing and confirming
- **confirmed**: verified locally, ready to report
- **reported**: submitted to the bug bounty platform
- **rewarded**: bounty received ✓
- **denied**: rejected (out of scope, wontfix)
- **duplicate**: someone else already reported it
- **n/a**: turned out to be a false positive

## Automatic Logging Behavior

When you discover a vulnerability during a session:

1. **Immediately** call `bb_create_finding` with status `discovered`
2. **Set `agent` to your specific identity** (e.g. `gemini-cli`, `claude`, `emmu`, `codex`). **NEVER** leave it as `manual` unless you are a human entering it via the web UI.
3. Fill in as much detail as possible: title, target, severity, CWE, description
4. **Upload Evidence**: If you have log files, screenshots, or local exploit scripts, immediately call `bb_upload_attachment` using the finding `id` and the `file_path`.
5. As you verify the finding, call `bb_update_finding` to add PoC and steps
6. When confirmed, call `bb_update_status` to set `confirmed`

## Example: Logging a finding with attachment

1. **Create the finding:**
```json
{
  "title": "Path Traversal in /api/download",
  "target": "example.com",
  "severity": "high",
  "agent": "emmu"
}
```
*(Assume this returns ID: 42)*

2. **Upload the evidence:**
```json
{
  "id": 42,
  "file_path": "./etc_passwd_dump.txt"
}
```

3. **Update PoC:**
```json
{
  "id": 42,
  "poc": "See attached file for the dumped /etc/passwd content."
}
```

## Example: Logging a finding (Manual Entry)

```json
{
  "title": "Reflected XSS in search parameter",
  "target": "app.example.com",
  "platform": "HackerOne",
  "severity": "high",
  "status": "confirmed",
  "agent": "gemini-cli",
  "cwe": "CWE-79",
  "cvss": 7.2,
  "description": "The `q` parameter on `/search` reflects unsanitized user input...",
  "poc": "## Steps\n1. Navigate to `/search?q=<script>alert(1)</script>`\n2. Observe XSS execution\n\n## Payload\n```\n<script>alert(document.cookie)</script>\n```"
}
```

## Portal URL

The bb-huge portal is available at: `http://localhost:5000`
View all findings at: `http://localhost:5000/findings`
