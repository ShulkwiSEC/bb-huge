# Generic Bug Bounty — Report Writing Guide

> Platform-agnostic best practices applicable to any bug bounty platform
> (HackerOne, Bugcrowd, Intigriti, YesWeHack, Immunefi, etc.)

---

## The Universal Principle

> **"Can my report be printed on a sheet of paper and still be understood?"**

If the answer is no, rewrite it until the answer is yes.

Attachments (screenshots, videos, HAR files) are **supplemental evidence**, not the primary PoC. The report text must contain everything needed to understand and reproduce the finding.

---

## Universal Report Structure

Every platform expects some variation of these fields:

### 1. Title
```
<Vulnerability Type> in <Component> leads to <Specific Impact>
```
- Strong: "IDOR on `/api/orders/{id}` allows reading other users' order details including PII"
- Weak: "IDOR vulnerability"

### 2. Affected Asset / Endpoint
- Exact URL or component path
- Environment (production, staging, dev)
- Version/hash if applicable

### 3. Vulnerability Type
- CWE identifier if known (e.g., CWE-200, CWE-79, CWE-639)
- Platform-specific weakness type if required

### 4. Steps to Reproduce (The Core)

Numbered, complete, and reproducible by someone who has never seen your setup.

**Must include:**
- Prerequisites (account type, browser, tools)
- Exact URLs, parameters, HTTP methods
- Payloads in code blocks (curl commands are ideal)
- Every action from start to finish

```bash
# Example: curl-based PoC that triager can copy-paste
curl -s "https://api.example.com/v1/users/456/profile" \
  -H "Authorization: Bearer <attacker-token>"
```

### 5. Expected vs Actual Behavior
- **Expected**: What the secure behavior should be
- **Actual**: What happens instead — the security gap

### 6. Impact

Explain the **real** consequences:
- What data can be accessed/stolen?
- What actions can be performed?
- Who is affected? (users, admins, the company)
- Can this be chained with other issues?

**Never say "an attacker could" without showing the concrete outcome.**

✅ Good: "An unauthenticated visitor extracts valid Instana APM monitoring keys, Azure AD tenant IDs, and employee email addresses from the page HTML source. These credentials enable telemetry manipulation, targeted OAuth phishing, and infrastructure probing."

❌ Bad: "This could lead to information disclosure."

### 7. Remediation (Optional)
Constructive suggestions for fixing the issue. Not required but appreciated.

---

## Evidence Rules

| Do | Don't |
|----|-------|
| Include actual leaked data in the report text | Hide leaked data in attachments only |
| Paste HTTP requests as text (curl preferred) | Screenshot HTTP requests |
| Show payloads in code blocks | Write "a payload was sent" without showing it |
| Capture timestamps for time-sensitive findings | Claim a key changed without evidence |
| Use Markdown formatting for readability | Dump raw text without structure |

### The Three Layers of Evidence

```
Layer 1: Report text         ← Always required. Must be self-contained.
Layer 2: Code/curl snippets  ← Embedded in report text for reproduction.
Layer 3: Attachments         ← Supplemental only. Screenshots, videos, HAR files.
```

---

## Severity Scoring

**Always use the platform's CVSS calculator** if available. Never manually override unless you fully understand the CVSS 3.1 standard.

### Quick CVSS Reference

| Severity | CVSS Range | Examples |
|----------|-----------|----------|
| Critical | 9.0–10.0 | RCE, SQLi (full DB), ATO, auth bypass |
| High | 7.0–8.9 | Stored XSS, IDOR with PII, SSRF, privilege escalation |
| Medium | 4.0–6.9 | Reflected XSS, info disclosure, open redirect, CSRF |
| Low | 0.1–3.9 | Missing headers, verbose errors, non-sensitive leak |
| Informational | 0.0 | Best-practice gaps, recon notes |

### Common Severity Mistakes

| Mistake | Why It's Wrong |
|---------|---------------|
| Submitting Info Disclosure as Critical | Info disclosure with no demonstrated impact is Medium at best |
| Submitting Missing Headers as High | Missing CSP/X-Frame-Options headers are Low unless combined with working exploit |
| Using manual severity instead of CVSS | Manual selection is subjective — the calculator is objective |

---

## General Pre-Submit Checklist

- [ ] Program scope verified — asset IS in scope and bounty-eligible
- [ ] Vulnerability type accepted by program's weakness list
- [ ] No duplicate report found (search disclosed reports / Hacktivity)
- [ ] Title is descriptive: `[Type] in [Location] -> [Impact]`
- [ ] Steps to reproduce are complete and numbered
- [ ] HTTP requests/payloads included as TEXT (curl preferred)
- [ ] Impact describes real, specific consequences
- [ ] Report passes the "paper test" (understood without attachments)
- [ ] CVSS score computed, not guessed
- [ ] No hypothetical attack scenarios — only what's demonstrated
- [ ] AI assistance disclosed if applicable
- [ ] Source IP included if program recommends it

---

## Platform-Specific Differences

| Feature | HackerOne | Intigriti | Bugcrowd | YesWeHack |
|---------|-----------|-----------|----------|-----------|
| Form type | Template-based (Markdown) | Structured fields + CVSS | Structured form | Structured form |
| CVSS calculator | Yes (built-in) | Yes (Contextual CVSS) | Yes | Yes |
| Scope validator | Manual check | Automated assistant on draft | Manual check | Manual check |
| AI disclosure | Varies by program | Required | Recommended | Varies |
| Public disclosure | Optional, 30-day default | Depends on program | Via VRT | Depends on program |

**When in doubt, check the program's specific submission guidelines.** They override any generic guidance.
