# Bug Bounty Bootcamp — Report Writing Reference
*Distilled from: "Bug Bounty Bootcamp" by Vickie Li (No Starch Press, 2021)*
*Read this before generating any report.*

---

## Core Philosophy

> "A bug bounty hunter's job isn't just finding vulnerabilities; it's also explaining them to the security team."

The faster a report is understood and reproduced, the faster it gets fixed and paid. Every minute you save the triager is a vote for your credibility.

---

## The 8-Step Report Framework (Vickie Li's Method)

### Step 1 — Descriptive Title
Answer in one line: **What** vulnerability? **Where** on the target? **What impact**?

❌ Weak: `IDOR on a Critical Endpoint`  
✅ Strong: `IDOR on https://example.com/api/users/{id}/account Exposes PII of All Users`

The title should let the security team know the vulnerability type, the affected endpoint, and potential severity before reading anything else.

### Step 2 — Severity Assessment
Use the standard scale. Accurate severity = faster triage + better relationship.

| Severity | Criteria | Example |
|---|---|---|
| **Low** | Doesn't cause much damage on its own | Open redirect usable only for phishing |
| **Medium** | Moderate user/org impact, or hard to exploit High | CSRF on password change |
| **High** | Large user impact, serious consequences | Open redirect stealing OAuth tokens |
| **Critical** | Majority of users or core infrastructure | SQLi → RCE on production server |

*"Providing an accurate assessment of severity will make everyone's lives easier and contribute to a positive relationship."*

### Step 3 — Proof of Concept (PoC)
Show the vulnerability, don't just describe it.
- **Web vulns**: screenshot, HTTP request/response pair, or crafted URL
- **CSRF**: embedded HTML file — triager opens it in browser, done
- **Complex multi-step bugs**: screen-capture video walkthrough
- Include crafted URLs, scripts, or upload files you used

The goal: triager shouldn't have to prepare anything themselves.

### Step 4 — Clear Steps to Reproduce
Write for someone with **zero knowledge** of the application. Be explicit.

❌ Weak:
```
1. Log in and visit /change_password
2. Click Change Password
3. Intercept and change user_id
```

✅ Strong:
```
1. Create two accounts: Account A (attacker) and Account B (victim)
2. Log in as Account A
3. Visit https://example.com/change_password
4. Fill in new password and click Submit
5. Intercept the POST /change_password request in Burp Suite
6. Change the user_id parameter from A's ID to B's ID
7. Forward the request
Result: Account B's password is now changed to attacker's chosen value
```

### Step 5 — PoC Files
Go beyond screenshots. Include:
- Ready-made HTML files with embedded payloads (CSRF, XSS)
- Crafted XML for XXE attacks
- Scripts that demonstrate the exploit end-to-end
- Video walkthroughs for complex multi-step chains

### Step 6 — Impact and Attack Scenario
**This section is not the same as severity.** Severity = how bad. Attack scenario = what it looks like when it's exploited.

Put yourself in the attacker's shoes:
- Could they take over user accounts?
- Could they steal user info and cause large-scale data leaks?
- **Escalate the impact** as much as possible — show the worst case

*"Give the client company a realistic sense of the risk."*

### Step 7 — Recommend Mitigations
Only recommend if you understand the root cause. Bad recommendations confuse readers and reduce credibility.

✅ Good: *"The application should validate the user's user_id parameter in the change password request to ensure the user is authorized. Unauthorized requests should be rejected and logged."*

❌ Don't just say: *"Sanitize input"* — too vague, shows you don't understand the root cause.

If you're unsure of the root cause: skip this section, or say "root cause analysis pending access to source code."

### Step 8 — Validate Before Submitting
- Follow your own Steps to Reproduce — do they work exactly?
- Test all PoC files and code
- Check for technical errors or ambiguity
- Read it as if you've never seen this bug before

---

## Report Writing Style (Li's Tips)

**Don't assume anything.** The engineer reading your report may not know how the application works at all. Spell out every assumption.

**Be clear and concise.** No wordy greetings, jokes, or memes. A security report is a business document. Make it as short as possible *without omitting key details.*

**Write what you want to read.** Conversational tone. No leetspeak, slang, or abbreviations — these add to reader frustration.

**Be professional.** Communicate with respect. Clarify patiently. This is a long-term relationship, not a one-time transaction.

---

## Why Reports Get Dismissed — Common Mistakes

### Out of Scope
Read the bounty policy carefully and repeatedly before submitting. Which vulnerabilities are explicitly out of scope? Common out-of-scope items:
- Self-XSS
- Clickjacking without meaningful impact
- Missing HTTP headers without direct security impact  
- DoS attacks
- Results of automated scanners **without proof of exploitability**

### Failing to Communicate Impact
*"Minor bugs get dismissed when you fail to communicate their impact."*

A bug that looks trivial can become critical when chained. Don't report the first minor bug you find — try to chain it into something bigger first. An open redirect alone might be low. An open redirect chaining into SSRF = High/Critical.

### Poor Steps to Reproduce
Security teams mark reports as "Need More Information" when they can't reproduce. If you included incorrect URLs in your PoC, the team may mark it as N/A even if the bug is real.

### Spamming / Automated Output
Don't submit automated scanner results without proof of exploitability. This is explicitly out of scope in almost all programs and kills your reputation.

---

## Vulnerability-Specific Escalation Guidance

### XSS — Escalation Path
Start with: *Can I run JavaScript in victim's browser?*
Then escalate to:
1. **Cookie/session theft** → account takeover (`document.cookie` exfil)
2. **Credential phishing** → fake login overlay injected into page
3. **Malware delivery** → redirect victim to exploit page
4. **Stored XSS** beats Reflected > DOM-based for severity (stored affects all users)

Prevention the target should implement: output encoding for all user-controlled data rendered in browser; `HttpOnly` flag on sensitive cookies; Content Security Policy (CSP).

### Open Redirect — Escalation Path
Alone = Low. Chained = High/Critical.
- Open Redirect + OAuth → **steal OAuth tokens** (Critical)
- Open Redirect + password reset → **token hijacking**
- Open Redirect + phishing → **credential theft at scale**

Always check: does the app use OAuth or SSO? If yes, open redirect jumps to High.

Prevention: allowlist-based URL validation (not blocklist). Avoid redirecting to user-supplied URLs entirely if possible.

### IDOR — Escalation Path
- Read-only PII exposure → High
- Account modification (change other user's password/email) → Critical
- Admin function IDOR → Critical

Check for: numerical IDs, GUIDs that are predictable, hashed IDs using weak algorithms, indirect references (filenames, order numbers).

Prevention: server-side ownership verification on every request. Never trust the client-supplied object ID alone.

### SSRF — Escalation Path
- Internal network enumeration → High
- Cloud metadata access (AWS IMDSv1) → **IAM credential exfil → full cloud takeover** → Critical
- Internal admin panel access → Critical

Always test: `http://169.254.169.254/latest/meta-data/iam/security-credentials/` — if this returns data, it's Critical.

Prevention: URL allowlist (not blocklist). Block cloud metadata endpoints explicitly. Enforce IMDSv2 (AWS).

### SQL Injection — Escalation Path
- Error-based data read → High
- UNION-based full DB dump → Critical
- `INTO OUTFILE` / `xp_cmdshell` → **OS-level RCE** → Critical

Prevention: parameterized queries / prepared statements (not input sanitization alone). Sanitization is brittle and easy to bypass.

### CSRF — Escalation Path
- On low-impact action → Medium
- On password/email change → High
- On admin action / financial action → Critical

Try bypass techniques before reporting: change request method (GET vs POST), remove CSRF token (does it still work?), use old/expired token.

Prevention: CSRF tokens (unique per session, sufficient entropy), SameSite cookie attribute.

---

## Bug Chaining Principle
*"Minor bugs classified as informative can become big issues if you learn to chain them."*

Examples:
- Open redirect → SSRF
- CSRF + XSS → full account takeover without interaction
- Info leak + IDOR → targeted data exfil
- Self-XSS + CSRF → stored XSS exploitable on other users

Before submitting a low-severity finding, ask: *Can I chain this into something worth reporting?*

---

## Platform Norms (from book)
- HackerOne and Bugcrowd are intermediaries — reports go to triagers first, not developers
- Triagers are often not deeply familiar with the product's security internals
- This is why reports must be self-contained and reproducible by someone with no context
- Programs with fast response times = better feedback loop for improving your report quality
