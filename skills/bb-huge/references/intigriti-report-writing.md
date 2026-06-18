# Intigriti — Report Writing Guide

> Based on Intigriti KB: "How to write and submit a good report"
> Source: https://kb.intigriti.com/en/articles/5379086-how-to-write-and-submit-a-good-report

---

## Before You Write

**Read the scope. Read it again. Then read it once more.**
- Understand what's in scope and what's explicitly excluded
- Know the bounty tiers (Tier 1 = No Bounty, Tier 3 = Bounty-eligible)
- Respect program rules — no automated scanners, no DoS, no social engineering

The scope validation assistant runs automatically when you review your draft. If it flags a potential issue, read the specific reasoning, cross-check against program scope, and decide whether to proceed.

---

## Intigriti Submission Form Fields

When submitting via the Intigriti web UI, you fill out a structured form — not a free-text box. Here's what each field expects:

### 1. Submission Title
Concise, descriptive. Format: `<Vulnerability Type> in <Component> leads to <Impact>`

Good: "Stored XSS in user profile bio field allows session hijacking on profile view"
Bad: "XSS vulnerability" (too vague)

### 2. Asset
Select the relevant asset from the program's in-scope list. If the asset isn't listed, you may not be able to submit — check scope again.

Example: `developer.sbb.ch` under `*.sbb.ch`

### 3. Endpoint / Vulnerable Component (Optional but Recommended)
The exact URL or component path where the vulnerability manifests.

Example: `https://developer.sbb.ch/env-config.js` or `POST /api/user/profile`

### 4. Type of Vulnerability
Select from the provided dropdown. If your vuln type isn't listed, pick the closest match.

Common types: XSS, SQL Injection, IDOR, SSRF, Information Disclosure, Authentication Bypass, Business Logic Flaw, etc.

### 5. Severity (CVSS Calculator)

**Use Intigriti's CVSS calculator** — available in the submission form. Do NOT pick a manual severity unless you fully understand the CVSS standard.

> Wrong severity is a common reason for initial downgrade. If you submit as "Critical" but it's Medium, the triager adjusts it and may distrust your judgment going forward.

Intigriti uses a **Contextual CVSS** standard:
- Be conservative with Confidentiality/Integrity/Availability metrics
- If you're unsure, use the calculator and let it compute the score
- Document your CVSS vector string and rationale

### 6. Proof of Concept / Description (The Main Body)

This is where the report content goes. The golden test:

> **"Can my report be printed on a sheet of paper and still be understood?"**

**Required elements:**
- **Summary**: 2-3 sentences explaining what the vulnerability is and why it matters
- **Steps to Reproduce**: Numbered, clear, reproducible by someone who has never seen your setup
- **Expected vs Actual Behavior**: What should happen vs what actually happens
- **Payload / Request**: Include actual HTTP requests (raw curl commands are best — triagers can copy-paste them), parameters, or payloads

**Formatting rules:**
- Use Markdown for structure (headings, code blocks, bullet points)
- Use code blocks for requests, payloads, and commands
- Put the actual exposed/leaked data in the report text, not just in attachments
- Screenshots are supplementary — the report must be understandable WITHOUT them

**Do NOT:**
- Add screenshots of raw HTTP requests (paste the text instead)
- Write "an attacker could" without showing *how*
- Omit the actual leaked data (in info disclosure reports, the leaked data IS the evidence)

### 7. Impact
Explain the real-world consequences. Be specific about what an attacker can achieve.

Good: "An unauthenticated attacker extracts Instana APM monitoring keys, Azure AD tenant IDs, and internal infrastructure routes from the client-side HTML. This enables telemetry manipulation, targeted OAuth phishing, and infrastructure probing."

Bad: "This could lead to information disclosure."

### 8. Recommended Solution (Optional)
How the issue should be fixed. Be constructive, not demanding.

Examples:
- "Remove sensitive env vars from client-side HTML — inject them server-side only"
- "Implement proper access control on the endpoint"
- "Sanitize user input before rendering"

### 9. IP Address Used During Testing (Optional but Recommended)

Providing your source IP helps the customer validate the finding against their logs. This is **standard** in bug bounty — including it will NOT get you in trouble.

---

## Platform-Specific Rules

| Rule | Details |
|------|---------|
| Language | English unless program specifies otherwise |
| Attachments | Screenshots as supplement only — report must be readable without them |
| File size limits | PNG/JPG/GIF: 10MB, all others: 1GB |
| Evidence | Include actual data/code/requests in the report text |
| AI disclosure | Required if AI tools assisted with discovery or drafting — disclose transparently, but verify every claim manually |
| Scope validation | Automated assistant runs on draft review — if it flags scope, read the reasoning and decide |

---

## The Triage Lifecycle

```
Submitted → In Queue → Under Review → Triaged (Needs More Info / Validated)
                                                            ↘ Fixed / Bounty Paid
                                                            ↘ Informative / N/A
```

- **Initial response**: Within days typically. Severity may be adjusted.
- **Needs More Info**: Respond quickly and thoroughly with additional evidence.
- **Validated**: Moved to customer for the final decision.
- **Disclosure**: Policies vary by program.

---

## Common Mistakes That Get Reports Downgraded or Rejected

1. **Submitting out of scope** — Always verify scope first. Use the scope validation assistant.
2. **Wrong severity** — Using the manual severity slider instead of the CVSS calculator.
3. **Missing evidence** — Not including the actual leaked data or payload in the report text.
4. **Screenshot-only PoC** — Triagers can't copy-paste from images. Always include text.
5. **Hypothetical impact** — "An attacker could" without demonstrating how.
6. **Not including source IP** — Makes it harder for the customer to validate.
7. **Overclaiming** — Saying "Critical" when it's Medium damages your credibility.

---

## Pre-Submit Checklist

- [ ] Program scope read and understood — asset IS in scope
- [ ] Vulnerability type matches program's accepted weakness list
- [ ] Title is descriptive and specific
- [ ] Asset selected correctly
- [ ] CVSS score computed, not guessed
- [ ] Steps to reproduce are numbered and copy-pasteable
- [ ] Actual leaked data / payload is IN the report text
- [ ] Impact describes real consequences, not hypotheticals
- [ ] Report passes the "paper test" — can it be printed and still understood?
- [ ] AI assistance disclosed (if applicable)
- [ ] Source IP included
