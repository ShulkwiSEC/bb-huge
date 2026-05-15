# bb-huge Theory Quiz

Test whether your AI agent fully loaded and understood the bb-huge skill.
Use these prompts after `/bb-huge` loads. Compare the agent's responses to the
expected answers below.

If any response is **wrong, incomplete, or confused** → [open an issue](https://github.com/ShulkwiSEC/bb-huge/issues/new)
and paste the agent's output + which question failed.

---

## How To Use

1. Start a **fresh session** with your agent (gemini-cli, claude-code, etc.)
2. Type **`/bb-huge`** — let the skill load completely
3. Ask each question **one at a time** from the list below
4. Compare the agent's answer to the **expected response**
5. Mark PASS / FAIL for each question

**Pass threshold:** 9/10 correct = agent is ready for production use.

---

## Quiz Questions

### Q1 — Architecture Understanding

**Prompt:**
```
What is bb-huge and how does it work at the architectural level?
```

**Expected response:**
bb-huge is a Context Engineering Architecture with two layers:
- **Skill layer** (SKILL.md + references/): injects Senior Bug Hunter persona,
  SOPs, severity/status definitions, and methodology into the agent's context.
- **Portal layer** (Flask app + SQLite + MCP server): persistent storage for
  findings, programs, attachments, notes, and recon data.

They communicate through **MCP** (Model Context Protocol) via stdio. The agent
never touches the database directly — it calls MCP tools (`bb_create_finding`,
`bb_list_programs`, etc.) which hit the REST API.

The `/bb-huge` command triggers the skill which loads ~1,300 lines of bug bounty
knowledge into the agent's working context.

---

### Q2 — Loading Behavior

**Prompt:**
```
What happens when I type /bb-huge? Walk through the full sequence.
```

**Expected response:**
1. The skill file (`SKILL.md`) loads into the agent's context
2. The agent's persona is set to **Senior Bug Hunter** with capture-first discipline
3. The Session Initialization Protocol runs:
   - `bb_get_stats()` — gets portal state
   - `bb_list_programs()` — checks existing programs
   - `bb_get_context(program_id)` — checks for pre-hunt Q&A data
   - `bb_list_findings(q=<target>)` — checks prior work if a target is known
4. The agent reports a one-paragraph status summary
5. The agent asks: what target should we work on? (or proceeds if target known)

At this point the agent has full SOP knowledge, all MCP tools wired, and knows
the current portal state.

---

### Q3 — Capture-First Discipline

**Prompt:**
```
I just found a potential IDOR on /api/users/profile. What do you do?
```

**Expected response:**
Immediately call `bb_list_programs()` to find the target's program ID, then
`bb_create_finding()` with `status: discovered` and the program_id. Fill in
title, target, severity, and agent — even if the description is thin.

Never wait for a fully verified PoC. A thin entry now is better than a perfect
entry that never gets written.

Then attach any evidence files, continue testing, and enrich the finding as
more information becomes available.

---

### Q4 — SOP Listing

**Prompt:**
```
List all 5 Standard Operating Procedures and briefly explain each.
```

**Expected response:**

| SOP | Name | Purpose |
|-----|------|---------|
| SOP-1 | New Target Assigned | Recon setup, skill roster check, anchor finding |
| SOP-2 | Vulnerability Found | Capture-first protocol with program linking |
| SOP-3 | Resume a Previous Finding | Restore full context via get + dump attachments |
| SOP-4 | End of Session | Closeout checklist, stats check, progress notes |
| SOP-5 | Pre-Hunt Questioning Layer ⭐ | Collect target context from user once, persist forever |

---

### Q5 — Status Workflow

**Prompt:**
```
What do discovered, confirmed, and reported mean? When do you move between them?
```

**Expected response:**

| Status | Meaning | When to move to it |
|--------|---------|-------------------|
| `discovered` | Suspected but not verified | Immediately on suspicion |
| `debugging` | Actively testing/reproducing | When you start investigating |
| `confirmed` | Verified and reproducible | When you can reliably reproduce |
| `reported` | Submitted to bug bounty platform | After writing and submitting the report |
| `rewarded` | Bounty received | When payout comes in |
| `denied` | Rejected — out of scope or won't fix | After platform response |
| `duplicate` | Already reported by someone else | After platform confirmation |
| `n/a` | False positive | After determining it's not valid |

Never skip statuses. Move through the chain as evidence accumulates.

---

### Q6 — Program Linking

**Prompt:**
```
I want to log a finding for "Example Corp" on HackerOne. Walk me through it.
```

**Expected response:**
1. Call `bb_list_programs()` to check if "Example Corp" already exists
2. If not found, call `bb_create_program(name="Example Corp", platform="HackerOne")`
   which returns an id
3. Call `bb_list_programs()` again to find the id (or use the returned id)
4. Call `bb_get_context(program_id=N)` to check if pre-hunt Q&A exists
5. If context is empty, run the SOP-5 questioning phase to gather info from the
   user before proceeding
6. Call `bb_create_finding()` with `program_id: N` to link the finding to the
   program

---

### Q7 — Questioning Layer Purpose

**Prompt:**
```
What is SOP-5 and why is it the most important step?
```

**Expected response:**
SOP-5 is the **Pre-Hunt Questioning Layer**. Before any work starts on a new
target, the agent must collect structured context from the user across 5
categories:

1. **Target basics** — domains, business context, program type
2. **Access & credentials** — tester accounts, cookies, tokens, API keys
3. **Attack surface** — source code, tech stack, API docs, WAF
4. **Priorities & focus** — bug types to focus on, suspicious areas, past bugs
5. **Environment** — staging URLs, VPN, running tools

This data is saved via `bb_save_context(program_id, data)` and never re-asked.
Every subsequent session starts with `bb_get_context()` to check if data exists.

It's the most important step because testing blind is wasted effort. Knowing
the credentials, tech stack, and focus areas transforms random poking into
targeted hunting.

---

### Q8 — Session Resume

**Prompt:**
```
I was working on finding #17 last week. How do you pick up where I left off?
```

**Expected response:**
Follow SOP-3:
1. `bb_get_finding(17)` — read the current state, existing notes, attachments
2. `python scripts/bb-dump-attachments.py 17` — download all evidence to local
   disk
3. Read every attachment to fully restore context
4. Give a one-paragraph summary of where things stand:
   - What the finding is
   - What's been tested so far
   - What the current status is
   - What the next step should be

---

### Q9 — Multi-Agent Coordination

**Prompt:**
```
gemini-cli found an XSS and logged it. Now I (claude-code) found the same XSS.
What do I do?
```

**Expected response:**
Do NOT create a duplicate finding. Instead:
1. `bb_list_findings(q="xss", target=<target>)` — find the existing entry
2. `bb_update_finding(id=N)` — append "also confirmed by claude-code" to the
   description or add a note
3. If the finding is still in `discovered` or `debugging`, consider calling
   `bb_update_status(id=N, status="confirmed")` since a second agent confirmed it

Each agent always sets its own `agent` field. Never overwrite another agent's
finding.

---

### Q10 — End of Session

**Prompt:**
```
I'm wrapping up this research session. What should we do before I go?
```

**Expected response:**
Follow SOP-4:
1. `bb_get_stats()` — confirm everything found is logged
2. For any finding still in `debugging`, add a progress note via
   `bb_update_finding()` so the next session picks up cleanly
3. Flag any `confirmed` findings that haven't been `reported` yet
4. Summarize the session: what was tested, what was found, what's pending

---

## Scoring Sheet

| # | Question | PASS | FAIL |
|---|----------|------|------|
| 1 | Architecture Understanding | ☐ | ☐ |
| 2 | Loading Behavior | ☐ | ☐ |
| 3 | Capture-First Discipline | ☐ | ☐ |
| 4 | SOP Listing | ☐ | ☐ |
| 5 | Status Workflow | ☐ | ☐ |
| 6 | Program Linking | ☐ | ☐ |
| 7 | Questioning Layer Purpose | ☐ | ☐ |
| 8 | Session Resume | ☐ | ☐ |
| 9 | Multi-Agent Coordination | ☐ | ☐ |
| 10 | End of Session | ☐ | ☐ |

**Total: ** / 10 — **PASS if ≥ 9**, otherwise FAIL

---

## Reporting Issues

If the agent fails any question, [open an issue](https://github.com/ShulkwiSEC/bb-huge/issues/new)
with:

```
**Agent:** [gemini-cli / claude-code / codex / other]
**bb-huge version:** [commit hash or version]
**Failed question:** Q#
**Agent's answer:** <paste the agent's raw output>
**Expected answer:** <from this doc>
**Notes:** <any additional context>
```

This helps the community improve the skill files for everyone.
