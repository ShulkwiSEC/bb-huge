# bb-standards — Bug Bounty Standards, Scope & Rules

This file defines what counts as a valid finding, how to evaluate scope,
and what the universal rules are across all programs.

> Referenced by: `bb-orchestrator.md`
> Mentions: `bb-eligible-vulnerabilities.md`, `bb-operator.md`

---

## Universal Scope Rules (applies to ALL programs)

### Always OUT of scope — never test, never log as a finding:
- Denial of Service (DoS / DDoS) attacks
- Social engineering / phishing attacks against employees
- Physical security attacks
- Vulnerabilities in third-party services the company uses (unless explicitly in scope)
- Automated scanning that generates excessive load
- Accessing, modifying, or deleting other users' real data
- Testing on production systems in a way that impacts availability
- Any action that goes beyond reading data you shouldn't have access to

### Always requires explicit confirmation in program policy:
- Mobile apps (Android / iOS)
- APIs (REST, GraphQL, gRPC)
- Source code exposure
- Subdomain takeover on non-critical subdomains
- Self-XSS (usually not accepted)
- Rate limiting issues (usually accepted only if there's a real impact)

---

## Scope Evaluation Checklist

Before testing any target, answer all three:

**1. Is the domain/IP in scope?**
- Check the program's scope section explicitly
- Wildcards like `*.example.com` include all subdomains
- `example.com` without wildcard means only that domain
- When uncertain → note "scope unconfirmed" in finding, do NOT skip logging

**2. Is the vulnerability type accepted?**
- Load `bb-eligible-vulnerabilities.md` for the full eligible list
- Common rejections: self-XSS, missing security headers alone, clickjacking without PoC of harm
- Common acceptances: IDOR with PII access, stored XSS, auth bypass, SQLi, RCE

**3. Is the impact meaningful?**
- Theoretical vulnerabilities without demonstrated impact are usually rejected
- Always demonstrate: what data can be accessed? what action can be performed?
- A vulnerability with no real-world impact = informational at best

---

## CVSS Quick Reference

| Score | Rating | Action |
|-------|--------|--------|
| 9.0–10.0 | Critical | Log immediately, highest priority |
| 7.0–8.9  | High | Log immediately |
| 4.0–6.9  | Medium | Log and confirm before reporting |
| 0.1–3.9  | Low | Log, report only if program accepts low |
| 0.0      | Informational | Log for your own records, check if program accepts info |

---

## Platform-Specific Rules

### HackerOne
- Duplicate window: if same vuln reported in last 30 days → `status: duplicate`
- Reports need: Title, Severity, Description, Steps to Reproduce, Impact, PoC
- Markdown supported in all fields
- CVSS score is optional but improves triage speed

### Bugcrowd
- Uses Priority (P1–P4) not CVSS — map: critical=P1, high=P2, medium=P3, low=P4
- Requires: Target, Vulnerability Type (from their taxonomy), PoC
- Screenshots strongly preferred over text-only PoC

### Intigriti
- Strict scope enforcement — out-of-scope reports get automatic reject
- Requires business impact statement
- Prefers video PoC for complex chains

### Private Programs (direct contact)
- Always confirm responsible disclosure agreement before testing
- Default to 90-day disclosure timeline
- CC security@<company>.com on first contact

---

## Evidence Standards

What makes a finding report-ready:

| Field | Minimum Required | Ideal |
|-------|-----------------|-------|
| title | Clear, specific | Includes vuln type + endpoint |
| target | Domain/URL | Exact vulnerable URL |
| severity | Set | CVSS score also filled |
| description | What it is | How it was found, attack surface |
| poc | Steps to reproduce | Working payload + screenshot/recording |
| cwe | Optional | Always fill if known |
| attachments | At least one | Burp export + screenshot |
| evidence_records | None | Structured HTTP pairs via `bb_attach_http_pair()` |

### Structured Evidence

Prefer `bb_attach_http_pair()` over raw file attachments for HTTP-based
evidence. Structured evidence is:

- **Searchable** — future agents can read it without downloading files
- **Portable** — follows the record through promotion (observation→hypothesis→finding)
- **Self-documenting** — includes method, URL, headers, status code, and body

Use `bb_upload_attachment()` for visual/binaries: screenshots, Burp project
files, script outputs, or videos.

### Non-Finding Record Quality

Observations and hypotheses have lighter standards but still deserve care:

| Field | Observation | Hypothesis |
|-------|-------------|------------|
| title | Required — describe the odd behavior | Required — state the suspected vuln |
| summary | Required — what happened? | Use `attack_path` field instead |
| category | Required — which domain? | Use `weakness_hint` and `cwe` |
| confidence | Required — "low" if unsure | "medium" or "high" |

---

## Legal & Ethics

- Only test targets you have explicit permission to test
- If you accidentally access sensitive data: stop, document what you accessed, report immediately
- Do not store, share, or use any PII or credentials found during testing
- Responsible disclosure = notify first, wait for fix, then optionally publish
- Bug bounty programs have legal safe harbor — read it before testing
