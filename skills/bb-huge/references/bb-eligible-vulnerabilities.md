# bb-eligible-vulnerabilities — Vulnerability Taxonomy & Triage Guide

Full reference of vulnerability classes accepted in bug bounty programs,
with CWE mappings, typical severity, impact description, and quick triage notes.

> Referenced by: `bb-orchestrator.md`, `bb-standards.md`
> Mentions: `bb-recon.md` (for discovery vectors), `bb-report-templates.md` (for writing up)

---

## Injection

### SQL Injection — CWE-89
- **Severity**: Critical (blind/error-based with data access) → High (login bypass)
- **CVSS range**: 7.5–10.0
- **Accepted**: Almost universally
- **Triage signal**: Can you dump data? Can you bypass authentication? Can you write files?
- **PoC minimum**: Working payload + evidence of data returned or auth bypassed
- **Common endpoints**: Login forms, search, filters, order/sort params, REST IDs

### Command Injection — CWE-78
- **Severity**: Critical
- **CVSS**: 9.0–10.0
- **Triage signal**: OS command execution confirmed (`id`, `whoami`, `ping` callbacks)
- **PoC minimum**: Out-of-band confirmation (DNS callback via Burp Collaborator / interactsh)

### SSTI (Server-Side Template Injection) — CWE-94
- **Severity**: Critical if RCE achievable, High otherwise
- **CVSS**: 8.0–10.0
- **Triage signal**: `{{7*7}}` → `49` in response
- **Common engines**: Jinja2, Twig, Freemarker, Smarty, Pebble

### XXE (XML External Entity) — CWE-611
- **Severity**: High–Critical depending on data accessible
- **Triage signal**: Can read `/etc/passwd` or make outbound HTTP requests

---

## Cross-Site Scripting (XSS)

### Stored XSS — CWE-79
- **Severity**: High (affects other users) → Critical (admin panel or auth context)
- **CVSS**: 7.0–9.0
- **Accepted**: Yes, high priority
- **PoC minimum**: Payload that executes in another user's session, screenshot/recording

### Reflected XSS — CWE-79
- **Severity**: Medium–High
- **CVSS**: 6.1–7.5
- **Accepted**: Yes, but requires social engineering vector
- **Note**: Must bypass CSP if present — show CSP bypass in PoC

### DOM XSS — CWE-79
- **Severity**: Medium–High
- **Triage signal**: User input flows to `innerHTML`, `eval`, `document.write`, `location.href`
- **Tools**: DOM Invader (Burp), manual source-to-sink tracing

### Self-XSS
- **Severity**: Informational
- **Accepted**: Usually NOT — only accepted if there's a known escalation path (e.g. CSRF to trigger it)

---

## Authentication & Authorization

### IDOR (Insecure Direct Object Reference) — CWE-639
- **Severity**: Medium–Critical depending on data exposed
- **CVSS**: 5.0–9.0
- **Triage signal**: Change numeric/UUID ID in request → access another user's data
- **PoC minimum**: Two accounts, Account A accessing Account B's resource
- **Impact escalation**: PII access = High, account takeover = Critical

### Authentication Bypass — CWE-287
- **Severity**: Critical
- **Types**: JWT manipulation, password reset flaws, OAuth misconfiguration, MFA bypass

### JWT Vulnerabilities — CWE-347
- **Severity**: High–Critical
- **Common issues**:
  - `alg: none` accepted
  - Algorithm confusion (RS256 → HS256 with public key)
  - Weak secret (brute-forceable with hashcat/jwt-cracker)
  - Missing expiry validation

### OAuth Misconfiguration — CWE-601
- **Severity**: High–Critical
- **Common issues**:
  - Open redirect in `redirect_uri` → token theft
  - `state` parameter not validated → CSRF on auth flow
  - Account linking without email verification

### Privilege Escalation — CWE-269
- **Severity**: High–Critical
- **Types**: Horizontal (user → user), Vertical (user → admin)

### CSRF (Cross-Site Request Forgery) — CWE-352
- **Severity**: Medium
- **Accepted**: Yes, if state-changing action without CSRF token
- **Not accepted**: GET requests, actions requiring re-authentication

---

## Server-Side Vulnerabilities

### SSRF (Server-Side Request Forgery) — CWE-918
- **Severity**: High–Critical
- **CVSS**: 7.0–9.0
- **Triage signal**: Server makes requests to attacker-controlled host (DNS/HTTP callback)
- **Escalation path**: Internal network access, cloud metadata (169.254.169.254), RCE via internal services
- **Tools**: Burp Collaborator, interactsh, ssrf.ing

### Path Traversal — CWE-22
- **Severity**: High (if reading sensitive files like `/etc/passwd`, `.env`, source code)
- **Payloads**: `../../../etc/passwd`, `..%2F..%2F`, `....//....//`

### Unrestricted File Upload — CWE-434
- **Severity**: Critical (if executable), High (if stored XSS via SVG/HTML)
- **Test**: Upload `.php`, `.jsp`, `.html`, `.svg` — can you execute or trigger XSS?

### Remote Code Execution — CWE-94/78
- **Severity**: Critical
- **Always**: Maximum priority, report immediately

### Insecure Deserialization — CWE-502
- **Severity**: Critical–High
- **Targets**: Java (ysoserial), PHP (unserialize), Python (pickle), Node.js

---

## Information Disclosure

### Sensitive Data Exposure — CWE-200
- **Severity**: Depends on data type
  - API keys, credentials, tokens → High–Critical
  - PII (names, emails, addresses) → Medium–High
  - Internal paths, stack traces → Low–Medium

### Directory Listing — CWE-548
- **Severity**: Low–Medium
- **Accepted**: If sensitive files are exposed

### Source Code Disclosure — CWE-540
- **Severity**: Medium–High (depends on what's in the code)

---

## Business Logic Vulnerabilities

### Price Manipulation
- **Severity**: High–Critical
- **Test**: Modify price/quantity in request, negative values, race conditions on payments

### Race Conditions — CWE-362
- **Severity**: Medium–High
- **Test**: Parallel requests on single-use tokens, coupons, limited resources

### Mass Assignment — CWE-915
- **Severity**: Medium–High
- **Test**: Send extra fields in JSON body that map to privileged model attributes

---

## Infrastructure & Configuration

### Subdomain Takeover — CWE-840
- **Severity**: High (if on main domain), Medium (on minor subdomain)
- **Test**: CNAME points to unclaimed resource (GitHub Pages, Heroku, S3, Azure)
- **Tools**: subjack, nuclei subdomain-takeover templates

### Open Redirect — CWE-601
- **Severity**: Medium
- **Accepted**: Yes, especially if it can be used in phishing or OAuth token theft

### Exposed Admin Panels
- **Severity**: High–Critical
- **Types**: Exposed without auth, weak credentials, default credentials

### CORS Misconfiguration — CWE-942
- **Severity**: Medium–High
- **Triage signal**: `Access-Control-Allow-Origin: <attacker-origin>` with `Access-Control-Allow-Credentials: true`
- **PoC minimum**: JavaScript that reads sensitive data cross-origin

---

## 📱 Mobile Vulnerabilities

### Insecure Data Storage — CWE-312
- **Severity**: Medium–High
- **Targets**: `shared_prefs`, `databases`, `plist`, external storage.

### Unvalidated Deep Link — CWE-939
- **Severity**: Medium–High
- **Impact**: Triggering sensitive actions or RCE in WebView.

### Exported Android Components — CWE-926
- **Severity**: Medium–High
- **Impact**: Unauthorized access to app features by other apps.

---

## ⚙️ Binary Vulnerabilities

### Buffer Overflow — CWE-120
- **Severity**: Critical (RCE) → High (DoS)
- **Triage**: Control over instruction pointer (EIP/RIP).

### Use-After-Free — CWE-416
- **Severity**: Critical–High
- **Impact**: Memory corruption leading to code execution.

### Hardcoded Constants — CWE-321
- **Severity**: High–Critical
- **Targets**: Hardcoded crypto keys, C2 IPs, or admin credentials.

---

## 📄 Source Code / SAST Findings

### Reachable Vulnerabilities
- **SQLi/RCE in Code**: MUST be reachable via a public interface.
- **Severity**: Same as web equivalents.

### Hardcoded Secrets in Repo — CWE-798
- **Severity**: High–Critical
- **Targets**: AWS keys, DB credentials, SSH private keys.

---

## What Programs Usually DON'T Accept

| Issue | Reason |
|-------|--------|
| Self-XSS | No real-world attack vector without CSRF |
| Missing security headers alone | Informational at best |
| SPF/DMARC missing | Low impact without phishing PoC |
| Clickjacking without sensitive action | No impact |
| Brute force without rate limiting alone | Needs PoC of actual impact |
| CSV injection | Rarely accepted, needs PoC of exploitation |
| Banner grabbing / version disclosure | Informational |
| SSL/TLS issues on non-critical hosts | Usually out of scope |
