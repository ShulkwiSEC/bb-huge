# HackerOne — Report Writing Guide

> Based on HackerOne Help Center: Quality Reports, Report Components, Report Templates
> Sources:
> - https://docs.hackerone.com/en/articles/8475116-quality-reports
> - https://docs.hackerone.com/en/articles/8475055-report-components
> - https://docs.hackerone.com/en/articles/8496338-report-templates

---

## Before You Write

**Verify three things:**
1. The program's scope — is this asset eligible for a bounty?
2. The program's accepted weakness types — does your vuln type match?
3. Has this issue already been reported? (Check for duplicates in the program's Hacktivity.)

---

## What HackerOne Looks For in a Quality Report

A quality report provides **clear, detailed, and actionable information**. It should include:

- **Clear and concise title** — Summarizes the vulnerability in one line
- **Detailed steps to reproduce** — Numbered, copy-pasteable, includes URLs and parameters
- **Impact assessment** — What an attacker can achieve and why it matters
- **Supporting material** — Screenshots, recordings, code snippets (text preferred)
- **Remediation suggestions** (optional but appreciated)

---

## Report Structure

### 1. Title

Format: `<Vulnerability Type> in <Location> allows <Impact>`

**Weak:** XSS in web app
**Better:** Stored XSS in user profile field allows script execution on profile view
**Good:** Stored XSS in `/settings/profile` "About Me" field — script executes when other users view the profile, enabling session hijacking

### 2. Summary (Optional)

The HackerOne report form has an optional **Summary** section that sets the context. Use it when:
- The vulnerability chain is complex and needs a high-level overview
- You want to frame the impact upfront
- The report is long and triagers need TL;DR first

### 3. Steps to Reproduce

Numbered, clear, and complete. Include:
- URLs with exact paths and parameters
- HTTP methods (GET, POST, PUT, etc.)
- Authentication requirements (logged-in user role)
- Payloads in code blocks

**Example:**

```
1. Log in as a regular user at https://example.com/login
2. Navigate to profile settings at https://example.com/settings/profile
3. Insert `<script>alert(document.cookie)</script>` into the "About Me" field
4. Click Save
5. Log out and view the profile as another user at https://example.com/user/test123
6. Observe the script executes on page load — alert box shows the victim's cookies
```

**Curl commands are preferred** for API-level findings — triagers can copy-paste directly:

```bash
curl -X POST "https://api.example.com/v1/user/profile" \
  -H "Content-Type: application/json" \
  -d '{"bio": "<script>alert(1)</script>"}'
```

### 4. Expected vs Actual Behavior

Clearly state the security boundary.

- **Expected:** The profile field should sanitize HTML/JavaScript input to prevent script execution
- **Actual:** The `<script>` tag is stored and executed when any user views the profile

### 5. Impact

Explain the security implications in specific terms.

**Weak:** This is a security issue.
**Good:** An attacker can store persistent JavaScript in their profile that executes in the browser of every user who visits it. This enables session cookie theft, CSRF token exfiltration, and redirection to phishing pages — without any user interaction beyond viewing a profile.

### 6. Supporting Material

- **Screenshots**: Visual proof, but NOT as the primary PoC
- **Video recordings**: For complex multi-step exploits
- **Code snippets**: Payloads, proof-of-concept scripts
- **HTTP request/response pairs**: Include headers and body

The report must be understandable **without** the supporting material. Attachments supplement the text, not replace it.

### 7. Remediation (Optional)

Constructive suggestions for fixing the issue.

---

## Common Mistakes That Get Reports Rejected

| Mistake | Why It's Bad |
|---------|-------------|
| Vague reports ("There's an XSS") | Triager can't reproduce without guessing |
| Screenshots instead of text for requests | Triager has to manually type the payload — wastes time |
| No impact explanation | Triager doesn't know why this matters |
| Poor formatting | Hard to read = hard to triage |
| Unnecessary detail overload | Buries the actual finding in noise |
| Out of scope | Instant N/A — wastes everyone's time |
| Duplicate of existing report | Check before submitting |

---

## HackerOne-Specific: Report Components

When your report is submitted, these components appear:

| Component | Description |
|-----------|-------------|
| Report ID | Unique identifier (e.g., `#123456`) |
| Report Title | Your title — becomes the public name if disclosed |
| Severity | CVSS score + rating (Critical/High/Medium/Low/None) |
| Weakness | CWE type selected during submission |
| Asset | The in-scope asset you selected |
| State | New → Triaged → Resolved (or N/A/Informative/Duplicate) |
| Timeline | All comments, state changes, bounty actions |
| Bounty | Only shown if awarded |

The metadata sidebar shows your hacker profile (reputation, signal, impact) — high-signal researchers get faster triage.

---

## HackerOne Report Templates

Some programs use **report templates** — a Markdown-powered form that pre-fills the submission form with required sections. When a template is active, you'll see structured fields instead of an empty text box.

If a template is present, **fill every section it provides.** Programs use templates because they need specific information to triage efficiently.

---

## Pre-Submit Checklist

- [ ] Program scope checked — asset is bounty-eligible
- [ ] Weakness type accepted by the program
- [ ] Checked for duplicates (Hacktivity, disclosed reports)
- [ ] Title is descriptive, includes vuln type + location + impact
- [ ] Steps to reproduce are numbered and complete
- [ ] HTTP requests included as text (curl commands preferred)
- [ ] Expected vs Actual behavior stated
- [ ] Impact describes real, specific consequences
- [ ] Supporting material attached (text preferred over screenshots)
- [ ] Report readable without attachments
- [ ] No overclaiming — severity matches CVSS score
