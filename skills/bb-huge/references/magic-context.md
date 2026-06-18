# Magic Context — Agent Memory Reference

## What it is

Magic Context is an OpenCode plugin that gives the agent **unbounded, persistent
memory across sessions**. Instead of forgetting everything when the context
window fills or a session ends, Magic Context runs a background historian that
continuously compresses old history into structured compartments, extracts key
facts, and stores architectural decisions as searchable memories — so the next
session picks up exactly where the last one left off.

Think of it as the hippocampus for the agent: raw experience → compressed
memory → recalled on demand.

---

## How it works (the three loops)

### 1 — Historian (automatic, background)
Runs silently as a lightweight sub-agent. As the session grows it:
- Tags every turn with `§N§` markers for age tracking
- Compresses old messages into `<compartment>` blocks (tiered: full → lite → ultra-compressed)
- Extracts `<session-fact>` entries (decisions, constraints, findings)
- Never blocks the main agent — compression happens between turns

### 2 — Dreamer (optional, scheduled)
Runs overnight or on-demand via `/ctx-dream`. Maintains memory quality:
- Merges duplicate/similar memories into canonical facts
- Verifies memories against current codebase
- Archives stale memories (removed features, old paths)
- Rewrites verbose memories into terse operational form

### 3 — Sidekick (per-turn, automatic if enabled)
Before each user prompt, runs a background semantic search on the prompt.
If highly relevant content exists (score ≥ 0.55), appends a compressed
"vague recall" hint — the agent decides whether to call `ctx_search` for
the full content. Enable with `experimental.auto_search.enabled: true`.

---

## Tools the agent can call

| Tool | Purpose |
|------|---------|
| `ctx_memory` | **Write a memory** — store an architectural decision, constraint, credential pattern, finding pattern, or any fact that should survive session end |
| `ctx_search` | **Recall memories** — semantic + full-text search across all stored memories, compartments, and session facts |
| `ctx_reduce` | **Drop bulky content** — queue a large tool output or pasted block for removal from the live context (stays searchable) |
| `ctx_expand` | **Re-expand a compartment** — retrieve the full original content of a compressed block when needed |
| `ctx_note` | **Deferred intention** — write a note that fires at a future trigger (e.g. "remind me to recheck X after testing Y") |

---

## Slash commands (manual control)

| Command | What it does |
|---------|-------------|
| `/ctx-status` | Show current context usage, compartment count, memory count |
| `/ctx-dream` | Trigger the dreamer on-demand for immediate memory maintenance |
| `/ctx-recomp` | Rebuild compartments from raw history (use after upgrading historian rules) |
| `/ctx-flush` | Force-flush pending context reductions immediately |
| `/ctx-embed` | Show embedding status and control backfill |
| `/ctx-aug` | Run Sidekick on-demand for manual memory augmentation |

---

## Bug bounty hunting — what to memorize

For the bb-huge workflow, use `ctx_memory` aggressively. Everything worth
knowing across sessions belongs in memory, not just in bb-huge.

### Memorize immediately when discovered

```
Target recon facts
  ctx_memory({ category: "recon", content: "customer.bmwgroup.com runs nginx/1.18, WAF: Akamai, auth: ONEid SSO" })

Credential patterns
  ctx_memory({ category: "credentials", content: "Coolblue tester: shulkwisec@intigriti.me — valid across NL/BE/DE" })

Scope boundaries
  ctx_memory({ category: "scope", content: "BMW program: *.bmwgroup.com in scope, cdn.* and static.* excluded" })

Vuln patterns that work
  ctx_memory({ category: "technique", content: "BMW ONEid CORS: Origin header reflected with credentials on all /oauth/* routes" })

Vuln patterns that don't work (saves re-testing)
  ctx_memory({ category: "dead-end", content: "Coolblue /api/checkout: rate-limited at 10 req/s, blocks fuzzing" })

Platform quirks
  ctx_memory({ category: "platform", content: "Intigriti BMW program: CORS findings require authenticated exfil PoC to be triaged" })

Tool/endpoint discoveries
  ctx_memory({ category: "recon", content: "Coolblue admin panel at admin.coolblue.nl — 403, worth revisiting with different auth" })
```

### When to search before acting

Before starting any test on a known target, always run:
```
ctx_search("target-name credentials scope findings")
ctx_search("target-name dead ends rate limits WAF")
```
This prevents re-testing known dead ends and surfaces relevant prior work
that isn't in the current session's context window.

---

## Integration with bb-huge

Magic Context and bb-huge serve different but complementary roles:

| bb-huge | Magic Context |
|---------|--------------|
| Structured finding records (title, severity, PoC, CWE) | Free-form knowledge and observations |
| HTTP evidence pairs | Session facts and architectural constraints |
| Status workflow (discovered → rewarded) | Cross-session memory that survives compaction |
| Report generation | Contextual recall to inform decisions |

**Rule:** Log everything structured to bb-huge. Memorize everything contextual
to Magic Context. A CORS finding goes to bb-huge as a finding; the knowledge
that "ONEid reflects Origin on all routes" goes to Magic Context as a technique
memory so future sessions know this without re-testing.

### Combined workflow

```
1. Session start
   → ctx_search("program-name") to surface all prior memory
   → bb_get_program_brief(id) to get structured findings/recon
   Together they give full context: structured + free-form

2. During testing
   → Discoveries go to bb_log_observation / bb_log_hypothesis
   → Patterns, constraints, and facts go to ctx_memory

3. Session end
   → bb_get_stats() to confirm everything structured is logged
   → ctx_memory any conclusions not yet written (e.g. "tested all IDOR patterns on /api/user/*, no hit")
```

---

## What NOT to memorize

Magic Context memory is for durable, reusable knowledge. Do not memorize:

- Raw HTTP requests/responses (use `bb_attach_http_pair` instead)
- Screenshot paths (use `bb_upload_attachment`)
- Temporary test payloads (they belong in the finding PoC)
- Anything that will be stale after one session (use `ctx_note` with a trigger
  if you want a temporary reminder)

---

## Setup reminder

Magic Context requires OpenCode's built-in compaction to be **disabled**:

```json
{
  "plugin": ["@cortexkit/opencode-magic-context"],
  "compaction": {
    "auto": false,
    "prune": false
  }
}
```

Run `npx @cortexkit/magic-context@latest doctor` any time to verify config,
check for conflicts, and auto-fix issues.

Database lives at: `~/.local/share/cortexkit/magic-context/context.db`
Mount this path on a persistent volume in Docker/CI environments or memory
won't survive container restarts.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Memory not persisting between sessions | Check db path is not ephemeral; run `doctor` |
| Historian not compressing | Ensure compaction is disabled in `opencode.json` |
| `ctx_search` returns nothing | Run `/ctx-embed` to check embedding backfill status |
| Dreamer not running | Use `/ctx-dream` to trigger on-demand; check model config |
| Plugin disabled at startup | Another context-management plugin is active — Magic Context auto-disables to avoid conflict; remove the conflicting plugin |