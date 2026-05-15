# bb-orchestrator — Multi-Skill Coordination & Routing Logic

This file defines how the bb-huge agent coordinates across all available skills,
routes tasks to the right specialist, and handles evidence, conflicts, and session state.

---

## Skill Roster & Routing Table

When you receive a task, route it to the correct reference file before acting:

| Task Type | Reference to Load |
|-----------|------------------|
| "scan this target", "enumerate subdomains", "fingerprint the app" | → `bb-recon.md` |
| "test for XSS / SQLi / SSRF / auth bypass / IDOR / …" | → `bb-eligible-vulnerabilities.md` |
| "what's in scope?", "is this target valid?" | → `bb-standards.md` |
| "write the report", "format for HackerOne" | → `bb-report-templates.md` |
| "what methodology should I follow?" | → `bb-operator.md` |
| "log this finding", "update status", "dump attachments" | → Stay in `SKILL.md` (MCP tools) |
| "create or look up a program", "add recon to a program" | → Stay in `SKILL.md` (MCP tools) |

**Load only the reference you need.** Do not load all files at once.

---

## Session Initialization Protocol

When starting any new session or receiving a new target:

```
1. bb_get_stats                        — check current portal state
2. Load bb-operator.md                 — get the active methodology
3. Load bb-standards.md                — confirm what's in scope
4. bb_list_findings (q=<target>)       — check if prior work exists
5. bb_list_programs                    — check if target program exists in portal
6. bb_get_context(program_id)          — load pre-hunt Q&A; if empty, run SOP-5
7. If prior work exists → bb_get_finding + bb-dump-attachments.py
8. Report a one-paragraph status summary before starting any testing
```

---

## Evidence Handling Rules

**Rule 1 — Capture first, organize later.**
Create the finding with `bb_create_finding` the moment a vulnerability is suspected.
Do not wait for a clean PoC.

**Rule 2 — Attach everything.**
Any file produced during testing (Burp exports, scripts, curl output, screenshots,
nmap results, nuclei output) should be attached via `bb_upload_attachment`.

**Rule 3 — Evidence chain in `description`.**
The `description` field is a running log. Append, never overwrite.
Format:
```
## Initial Discovery — [date/session]
<what was found and how>

## Evidence — [date/session]
<what files/payloads confirmed it>

## PoC — [date/session]
<reproducible steps>
```

**Rule 4 — Never delete unless certain it's junk.**
Use `status: n/a` or `status: duplicate` instead of deleting.

---

## Conflict Resolution

**Finding already exists for this target + vulnerability type:**
1. `bb_list_findings` with `q=<vulnerability type>` and filter by target
2. If match found → `bb_update_finding` on existing entry, do not create duplicate
3. If unclear → create new with `status: debugging`, note "possible duplicate" in description

**Scope conflict (not sure if target is in scope):**
1. Load `bb-standards.md`
2. If still unclear → create finding with `status: discovered`, note "scope unclear"
3. Never skip logging — false positives can be filtered, missed findings cannot

**Severity disagreement between tools:**
- Take the higher severity until confirmed otherwise
- Document the reasoning in `description`

---

## Multi-Agent Coordination

When multiple agents are working simultaneously (e.g. gemini-cli + claude-code):

- Each agent sets its own `agent` field — never overwrite another agent's finding
- If two agents find the same issue → the second calls `bb_update_finding`
  and appends "also confirmed by <agent>" rather than creating a duplicate
- `bb_get_stats` at session start reveals what other agents have been doing

---

## Skill Discovery

To know what specialist skills are available in this installation:

```bash
python scripts/bb-orchestrator-list-skills.py
```

This lists all skill folders under `~/.gemini/skills/`. Each folder is a
specialized capability the agent can load when needed.

---

## Session End Checklist

Before closing any session, run through:

- [ ] `bb_get_stats` — all findings accounted for?
- [ ] Any `debugging` findings have a progress note added?
- [ ] Any `confirmed` findings not yet `reported`?
- [ ] All evidence files attached?
- [ ] Next session can pick up cleanly?
