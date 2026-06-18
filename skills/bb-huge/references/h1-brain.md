# h1-brain — HackerOne MCP Server Reference

**Repo:** `/mnt/d/Tools/h1-brain/`  
**MCP server name (opencode.json):** `h1-brain`  
**Server type:** Python FastMCP  
**Command:** `python3 /mnt/d/Tools/h1-brain/server.py`  
**Auth env vars:** `H1_USERNAME`, `H1_API_TOKEN`

---

## Overview

Python-based MCP server that connects AI assistants to HackerOne. Pulls your bounty history, program scopes, and report details into a local SQLite database. Ships with a pre-built database of **3,600+ public disclosed bounty-awarded reports** with full vulnerability write-ups (FTS5 full-text search).

**Databases:**

| Database | Contains | Source |
|----------|----------|--------|
| `h1_data.db` | Your personal reports, programs, scopes, attachments | HackerOne API (your account) |
| `disclosed_reports.db` | 3,600+ public disclosed reports that paid a bounty | Pre-built, ships via Git LFS |

---

## First Run

Before using search/analysis tools, populate your personal database:

1. **`fetch_rewarded_reports()`** — Pull all bounty-awarded reports with full write-ups
2. **`fetch_programs()`** — Pull all accessible programs

These are one-time setup calls. Re-run periodically to sync new data.

---

## Tools

### `hack(handle: str)` — Primary Entry Point: Attack Briefing

Single-call attack briefing for a program. Does everything:
1. Fetches fresh scopes from HackerOne API
2. Pulls your past rewarded reports for this program
3. Cross-references your full report history for weakness patterns
4. Identifies untouched bounty-eligible assets
5. Pulls public disclosed reports for the program
6. Suggests attack vectors based on weaknesses that paid elsewhere but aren't found here
7. Returns a complete attack briefing with offensive-mode instructions

**Usage:**
```
hack(handle="program_handle")
```

The output follows the template in `hack_instructions.md` — organized into scope summary, finding history, weakness analysis, untouched assets, public disclosures, and suggested attack paths.

---

### Your Reports (local DB queries — instant, no API calls)

#### `search_reports(query="", program="", weakness="", severity="", limit=20)`

Search your rewarded reports by title, program, weakness, or severity.

| Param | Type | Description |
|-------|------|-------------|
| `query` | `str` | Keyword search across report titles |
| `program` | `str` | Filter by program handle |
| `weakness` | `str` | Filter by weakness type (e.g. "IDOR", "XSS") |
| `severity` | `str` | Filter by severity rating |
| `limit` | `int` | Max results (default 20) |

**Returns:** List of reports with ID, title, program, weakness, severity, and bounty amount.

#### `get_report(report_id: str)`

Full report details with vulnerability write-up and attachments.

| Param | Type | Description |
|-------|------|-------------|
| `report_id` | `str` | HackerOne report ID (numeric string) |

**Returns:** Full report object with title, vulnerability_information, weakness, severity, CVSS vector/score, bounty, attachments metadata, reporter, assignee, created_at.

#### `get_report_summary()`

Reports grouped by program with counts and totals.

**Returns:** Summary object with per-program breakdown (total reports, by severity, by weakness, total bounty).

#### `search_programs(query="", bounty_only=False, limit=20)`

Search stored programs by handle or name.

| Param | Type | Description |
|-------|------|-------------|
| `query` | `str` | Search term for program handle or name |
| `bounty_only` | `bool` | Filter to only bounty-eligible programs |
| `limit` | `int` | Max results (default 20) |

**Returns:** List of programs with ID, handle, name, and bounty eligibility.

#### `search_scopes(program="", asset="", bounty_only=False, limit=30)`

Search in-scope assets across programs.

| Param | Type | Description |
|-------|------|-------------|
| `program` | `str` | Filter by program handle |
| `asset` | `str` | Search within asset identifier |
| `bounty_only` | `bool` | Only bounty-eligible assets |
| `limit` | `int` | Max results (default 30) |

**Returns:** List of scope entries with asset type, identifier, and bounty eligibility.

#### `fetch_attachment(report_id: str, attachment_id: str="")`

Get fresh download URLs for report attachments.

| Param | Type | Description |
|-------|------|-------------|
| `report_id` | `str` | HackerOne report ID |
| `attachment_id` | `str` | Specific attachment ID (optional — if omitted, returns all) |

**Returns:** Download URLs for attachment files. **URLs expire ~1 hour** — download immediately.

---

### Public Disclosed Reports (local DB — 3,600+ reports)

#### `search_disclosed_reports(query="", program="", weakness="", limit=20)`

Full-text search across public disclosed reports — titles and vulnerability write-ups.

| Param | Type | Description |
|-------|------|-------------|
| `query` | `str` | Full-text search term |
| `program` | `str` | Filter by program handle |
| `weakness` | `str` | Filter by weakness type |
| `limit` | `int` | Max results (default 20) |

**Returns:** List of disclosed reports with ID, title, program, weakness, severity, and bounty. Supports FTS5 full-text search for deep content searching.

#### `get_disclosed_report(report_id: int)`

Full details of a public disclosed report.

| Param | Type | Description |
|-------|------|-------------|
| `report_id` | `int` | Numeric report ID |

**Returns:** Full report object including vulnerability_information write-up, weakness, severity, CVSS, bounty, and reporter.

---

### Data Sync (API calls — rate limited)

#### `fetch_rewarded_reports()`

Sync your bounty-awarded reports from HackerOne API into local DB.

**Returns:** Count of new/updated reports. Uses pagination internally — pulls all pages.

#### `fetch_programs()`

Sync your accessible programs from HackerOne API into local DB.

**Returns:** Count of new/updated programs.

#### `fetch_program_scopes(handle: str)`

Sync scopes for a specific program.

| Param | Type | Description |
|-------|------|-------------|
| `handle` | `str` | Program handle |

**Returns:** Count of new/updated scope entries. Called automatically by `hack()`.

---

## Workflows

### Starting a New Program Hunt

```
hack(handle="program_handle")
```

→ Get attack briefing with scope, past findings, untouched assets, suggested vectors, and public disclosures.

### Researching Weakness Patterns

```
# What weaknesses did other researchers find on this program?
search_disclosed_reports(program="uber", weakness="IDOR", limit=10)

# Read full write-up of a specific disclosed report
get_disclosed_report(report_id=12345)
```

### Analyzing Your Performance

```
# What have I found on this program?
search_reports(program="uber", limit=50)

# Full report details
get_report(report_id="123456")

# Summary across all programs
get_report_summary()
```

### Syncing Data

```
fetch_rewarded_reports()
fetch_programs()
```

---

## Known Issues

- **First run:** `search_reports` / `get_report` / `search_programs` / `search_scopes` return "No stored reports" until `fetch_rewarded_reports()` and `fetch_programs()` are called at least once.
- **Rate limiting:** API fetch calls (`fetch_*`, `hack()`) use internal rate limiting. Be patient with large accounts.
- **Attachment URLs:** Expire ~1 hour. Download immediately after `fetch_attachment()`.
- **Auth failures:** Server crashes on startup if `H1_USERNAME` or `H1_API_TOKEN` are missing or invalid. Check environment variables in opencode.json.
- **Disclosed reports DB:** Uses Git LFS. `git lfs pull` may be needed after clone.
- **`mcp` package:** Requires `mcp>=1.6.0`. The `mcp` package name can conflict with `mcp-tool` or other variants.

---

## Complementary to `hackerone-mcp` (Node.js)

h1-brain is **read-only research-focused** — use alongside the existing `hackerone-mcp` Node.js server for report submission.

| Capability | `hackerone-mcp` (Node.js) | `h1-brain` (Python) |
|------------|--------------------------|---------------------|
| Submit reports | ✅ Create, submit | ❌ |
| `hack()` attack briefing | ❌ | ✅ Auto-generated attack plan |
| Disclosed reports search | ❌ | ✅ 3,600+ FTS5 full-text |
| Personal analytics | ❌ | ✅ Summary, earnings, patterns |
| Attachment download | ❌ | ✅ Expiring URLs |
| Cross-program scope search | ❌ | ✅ |
