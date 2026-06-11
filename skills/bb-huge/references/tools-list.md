## Available MCP Tools

### Findings Management

* `bb_create_finding` — Create a new bug bounty finding. Parameters: `field` (web|mobile|binary|source_code), `program_id`, `title`, `target`, `severity`, `status`, `agent`, `cwe`, `cvss`, `description`, `poc`
* `bb_list_findings` — List findings with filters/search. Filters: `q`, `severity`, `status`, `field`, `agent`, `limit`, `offset`
* `bb_get_finding` — Retrieve full finding details. Response includes `field`
* `bb_update_finding` — Update finding fields. Accepts `field`
* `bb_update_status` — Quickly change finding status
* `bb_delete_finding` — Delete a finding
* `bb_get_stats` — Retrieve statistics by severity, status, agent, and field (`by_field` breakdown)
* `bb_search_similar` — Search for similar findings. `field` parameter adds +15 similarity weight
* `bb_generate_report_context` — Generate report-ready context pack

### Notes & Collaboration

* `bb_add_note` — Add notes/comments to findings
* `bb_delete_note` — Delete a note from a finding
* `bb_bulk_update_status` — Bulk update finding statuses
* `bb_notify` — Send webhook notifications (Discord/Telegram/etc.)

### Attachments & Evidence

* `bb_upload_attachment` — Upload files to findings
* `bb_attach_http_pair` — Store structured HTTP request/response evidence

### Program Management

* `bb_create_program` — Create a bug bounty program. Parameters: `summary` (text), `tech_stack` (JSON array of strings)
* `bb_update_program` — Update an existing program's fields. Accepts `summary`, `tech_stack`
* `bb_delete_program` — Delete a program and all associated records
* `bb_list_programs` — List programs and metadata (includes `summary`, `tech_stack`)
* `bb_get_program_brief` — Retrieve compact hunt briefing/context

### Recon & Intelligence

* `bb_add_recon` — Store recon artifacts (subdomains/endpoints/etc.)
* `bb_delete_recon` — Delete a recon entry
* `bb_list_assets` — List program assets
* `bb_add_asset` — Add an asset to a program. `kind`: domain, subdomain, api_host, mobile_app, repo, binary, source_repo, other
* `bb_update_asset` — Update asset metadata
* `bb_delete_asset` — Delete an asset

### Endpoint Mapping

* `bb_list_endpoints` — List endpoints under an asset
* `bb_add_endpoint` — Add an endpoint/API route
* `bb_update_endpoint` — Update endpoint details
* `bb_delete_endpoint` — Delete an endpoint

### Context Persistence

* `bb_get_context` — Retrieve saved pre-hunt context/Q&A
* `bb_save_context` — Persist pre-hunt context/Q&A answers

### Observations & Hypotheses Workflow

* `bb_log_observation` — Log weak signals or suspicious behavior
* `bb_update_observation` — Update an existing observation's fields
* `bb_delete_observation` — Delete an observation
* `bb_log_hypothesis` — Log candidate vulnerabilities
* `bb_update_hypothesis` — Update an existing hypothesis's fields
* `bb_delete_hypothesis` — Delete a hypothesis
* `bb_promote_observation` — Convert observation → hypothesis
* `bb_promote_hypothesis` — Convert hypothesis → finding
* `bb_check_existing_work` — Check for duplicate/redundant work. Parameters: `program_id`, `target`, `title`, `cwe`, `field`, `description`

## Workflow Philosophy

The MCP server supports a staged investigation pipeline:

Observation → Hypothesis → Confirmed Finding

This enables agents and humans to:

* track low-confidence signals
* avoid premature findings
* preserve investigative context
* maintain structured evidence
* coordinate across multiple agents/tools

## Evidence Model

The server supports structured evidence storage including:

### HTTP Evidence (web, mobile)
```

* request method
* URL
* headers
* request body
* response status
* response headers
* response body
* auth context
* timestamps
* source tooling

This enables replayable investigations and richer report generation.

### Domain-Specific Evidence Types

| Evidence Type | Field | What It Captures |
|--------------|-------|-----------------|
| `binary_analysis_output` | binary | Raw output from Ghidra, IDA Pro, objdump, strings |
| `binary_ioc` | binary | IOCs extracted from binaries (hashes, IPs, domains, offsets) |
| `mobile_static_analysis` | mobile | JADX/MobSF analysis, Android manifest review, iOS plist |
| `source_code_vulnerability` | source_code | Vulnerable code patterns, SAST findings, manual review snippets |

## Supported Agent Types

Examples:

* Claude Code
* Gemini CLI
* Codex
* manual workflows
* custom MCP-compatible agents

## Primary Use Cases

* Bug bounty hunting
* Red team operations
* Recon management
* AI-assisted vulnerability research
* Multi-agent coordination
* Pentest evidence tracking
* Report generation
* Attack surface mapping
