# bb-operator — Hunting Methodology & Strategy

Defines the end-to-end approach for a bug bounty engagement:
how to pick targets, structure a session, and maximize finding rate.

> Referenced by: `bb-orchestrator.md`
> Mentions: `bb-recon.md`, `bb-eligible-vulnerabilities.md`, `bb-standards.md`

---

## Field-Aware Target Selection

Before selecting targets, determine the **field discriminator** for the current engagement.
The field affects which targets are high-value and which methodology to use.

### Field Selection Guide

| Field | Best Targets | Starting Methodology |
|-------|-------------|---------------------|
| `web` | Web apps, APIs, GraphQL, SPAs | Recon → vuln testing |
| `mobile` | Android APK, iOS IPA, mobile APIs | Static analysis → runtime testing |
| `binary` | ELF/PE/Mach-O, firmware, malware samples | Strings → disassembly → dynamic analysis |
| `source_code` | GitHub repos, private source, npm packages | SAST → dep scanning → manual review |

When logging findings, always set `field` to match the current domain.
Filter stats with `bb_get_stats()` to see which field produces the best results.

---

## Target Selection Strategy

### High-value target indicators:
- **New features** — recently launched functionality has less hardening
- **Acquisition targets** — newly acquired companies often have lower security maturity
- **Mobile apps** — historically lower test coverage than web
- **API v2/v3** — new versions often reintroduce fixed bugs
- **Subdomains of large programs** — `staging.`, `dev.`, `api.`, `admin.`
- **Programs with high average bounty** — worth deeper investment

### Program health signals:
- Response time < 7 days → active triage team → worth investing
- Low duplicate rate → not oversaturated → higher chance of unique finds
- Has public disclosed reports → learn from what others found

---

## Session Structure

### Phase 1 — Reconnaissance (load `bb-recon.md`)
```
Goal: Build a complete map of the attack surface before testing anything.
Field-aware adjustments:

  web:    Subdomain enumeration → fingerprinting → JS analysis
  mobile: APK/IPA acquisition → decompile → manifest review
  binary: File identification → strings/imports → disassembly
 source_code: Clone repo → dependency analysis → SAST scanning
```

**Output**: A recon finding in bb-huge with `status: debugging`, all discovered
assets noted in description. Set `field` on the finding.

### Phase 2 — Vulnerability Hunting (load `bb-eligible-vulnerabilities.md`)
```
Goal: Systematically test high-value attack surfaces.

Priority order:
1. Authentication flows (highest impact if broken)
2. IDOR / authorization (easy wins, high frequency)
3. Input handling (XSS, SQLi, SSRF, SSTI)
4. Business logic (requires app understanding)
5. Information disclosure (sweep at the end)

During testing:
- Weak or partial signal → bb_log_observation() (cheap, easy to close)
- Stronger candidate with a testable theory → bb_log_hypothesis()
- Attach evidence with bb_attach_http_pair() at every stage
- Promote when confident: observation → hypothesis → finding
```

### Phase 3 — Confirmation
```
Goal: Turn suspicions into reproducible findings.

1. Reproduce the issue 3 times in a row
2. Test in different browsers/accounts if relevant
3. Assess real-world impact (what can an attacker actually do?)
4. Build minimal PoC (strip out noise)
5. Update bb-huge: status → confirmed
```

### Phase 4 — Documentation (load `bb-report-templates.md`)
```
Goal: Write a report that gets triaged correctly the first time.

1. Fill all fields in bb-huge
2. Attach all evidence
3. Generate report from template
4. Self-review: is the impact clear? are steps reproducible?
```

Note: Programs support an optional `logo_url` field. When creating or updating Program records, consider adding a public logo URL to improve dashboard and report readability. See `skills/bb-huge/SKILL.md` for example payloads and the `bb-skill-examples.py` script for a runnable demo.

---

## High-Frequency Finding Patterns

These are the most commonly found bugs in modern web apps — test these first:

### Pattern 1 — IDOR on numeric IDs
```
Profile: GET /api/user/1234
Test:    GET /api/user/1235 with your own auth token
Signal:  Returns another user's data
```

### Pattern 2 — Mass assignment via extra JSON fields
```
Profile: PUT /api/user {"name": "test"}
Test:    PUT /api/user {"name": "test", "role": "admin", "is_verified": true}
Signal:  Any of the extra fields reflected in response or change behavior
```

### Pattern 3 — JWT algorithm confusion
```
Profile: Decode JWT header → look for "alg": "RS256"
Test:    Re-sign with HS256 using the public key as the secret
Tool:    jwt_tool, portswigger JWT editor
```

### Pattern 4 — OAuth redirect_uri manipulation
```
Profile: Find OAuth flow, locate redirect_uri parameter
Test:    redirect_uri=https://attacker.com or use open redirect on same domain
Signal:  Auth code or token returned to attacker-controlled URL
```

### Pattern 5 — SSRF via URL parameters
```
Profile: Any parameter that takes a URL (webhooks, avatars, import, preview)
Test:    Burp Collaborator / interactsh URL as value
Signal:  DNS or HTTP callback received
```

### Pattern 6 — Stored XSS in user-controlled fields
```
Profile: Any field that renders back to other users (name, bio, comments, titles)
Test:    <img src=x onerror=alert(1)> or SVG payloads
Signal:  Executes in another session (use two accounts)
```

---

## Time Management

**Single-day session:**
- 60% recon + attack surface mapping
- 30% testing top 3 vulnerability patterns
- 10% documentation

**Multi-day engagement:**
- Day 1: Full recon, map everything, create recon finding in bb-huge
- Day 2–3: Deep testing on identified high-value surfaces
- Day 4: Confirmation + PoC building
- Day 5: Report writing

**When to move on:**
- No finding after 2 hours on a specific surface → move to next surface
- Stuck on a finding for 1 hour → note current state in bb-huge, come back later
- Found one critical → document it fully before continuing

---

## Field-Specific Evidence Preservation

Each field generates different types of evidence. Use the right evidence type when
calling `bb_attach_http_pair()`:

| Field | Primary Evidence | Tooling |
|-------|-----------------|---------|
| `web` | HTTP request/response pairs (`bb_attach_http_pair`) | Burp, nuclei, curl |
| `mobile` | Static analysis output (`mobile_static_analysis`) | JADX, MobSF, Frida |
| `binary` | Analysis output + IOCs (`binary_analysis_output`, `binary_ioc`) | Ghidra, IDA, strings |
| `source_code` | Vulnerable code snippets (`source_code_vulnerability`) | semgrep, codeql, grep |

**Binary evidence example:**
```json
bb_attach_http_pair({
  "program_id": 1,
  "finding_id": 5,
  "title": "Ghidra: RC4 key at offset 0x4A20",
  "summary": "Hardcoded RC4 symmetric key found in binary auth routine",
  "request_method": "internal",
  "request_url": "binary://malware-sample.exe/offset/0x4A20",
  "response_status": 200,
  "response_body_text": "Disassembly of decrypt routine confirms key usage at 0x48F0"
})
```

---

## Context Preservation Between Sessions

The bb-huge portal is your persistent memory. Use it aggressively:

- Every weak signal → `bb_log_observation()` (low confidence, easy to close if wrong)
- Every stronger candidate → `bb_log_hypothesis()` (testable theory with attack path)
- Every confirmed issue → `bb_create_finding()` (mature record)
- Every dead end → add a note explaining why, close the observation/hypothesis
- Every partial finding → update description with "Progress as of [date]: ..."
- Every HTTP exchange worth saving → `bb_attach_http_pair()`
- Session start → always run `bb_get_stats` + `bb_get_program_brief(id)` first

Promote records as confidence grows:
`bb_promote_observation()` → hypothesis → `bb_promote_hypothesis()` → finding.

This ensures a new session (or a new agent) can pick up exactly where you left off.

---

## Red Flags That Signal a Juicy Target

These patterns in an application suggest higher attack surface:

- Custom authentication system (not using standard libs)
- File upload functionality
- PDF/image generation or processing
- Import/export features (CSV, XML, JSON)
- URL preview / fetch-by-URL functionality
- User-generated HTML or Markdown that gets rendered
- Admin panel accessible from the internet
- GraphQL API (introspection often enabled)
- Swagger/OpenAPI docs publicly accessible
- `X-Forwarded-For` accepted and used for logic
- `debug=true` or `test=1` accepted parameters
