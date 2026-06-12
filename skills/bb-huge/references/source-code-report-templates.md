# Source Code Audit Report Templates (White-Box)

This reference provides standardized templates for reporting vulnerabilities discovered via source code review.

## 1. Remote Code Execution via Insecure Deserialization (CWE-502)

### Title Formula
`Remote Code Execution via Insecure Deserialization in [FILE]:[LINE]`

### Impact Statement
The application deserializes untrusted data without sufficient validation, allowing an attacker to instantiate arbitrary objects and achieve full Remote Code Execution (RCE).

### Evidence Checklist
- [ ] Code snippet showing the vulnerable call (e.g., `pickle.load`, `unserialize`, `JSON.parse`)
- [ ] Data flow trace from user input to the deserialization sink
- [ ] PoC payload (e.g., base64 serialized object)

---

## 2. SQL Injection via String Concatenation (CWE-89)

### Title Formula
`SQL Injection in [FUNCTION] at [FILE]:[LINE] via [PARAMETER]`

### Impact Statement
Database queries are constructed using raw user input, allowing an attacker to manipulate the query logic, exfiltrate data, or bypass authentication.

### Evidence Checklist
- [ ] Code snippet showing the concatenated query string
- [ ] Name of the reachable endpoint that triggers this code
- [ ] PoC CURL command showing data exfiltration

---

## 3. Server-Side Template Injection (SSTI) (CWE-1336)

### Title Formula
`SSTI in [TEMPLATE_ENGINE] at [FILE]:[LINE]`

### Impact Statement
User input is embedded directly into a server-side template, allowing an attacker to execute arbitrary code within the template engine's context.

### Evidence Checklist
- [ ] Code snippet showing template rendering with user input
- [ ] Identification of the template engine (e.g., Jinja2, Twig, Mako)
- [ ] PoC payload: `{{7*7}}` or engine-specific RCE payload

---

## 4. Hardcoded Sensitive Information (CWE-798)

### Title Formula
`Hardcoded [SECRET_TYPE] in [FILE]:[LINE]`

### Impact Statement
Secrets (API keys, passwords, private keys) are hardcoded in the source code, allowing any user with access to the code or build artifacts to compromise the associated services.

### Evidence Checklist
- [ ] File path and line number
- [ ] The hardcoded string (redact slightly if needed, e.g., `sk_live_...ABCD`)
- [ ] Assessment of the secret's scope (e.g., "Full access to AWS S3 buckets")

---

## 5. Insecure Direct Object Reference (BOLA) in Code (CWE-639)

### Title Formula
`Missing Object-Level Authorization in [ENDPOINT] at [FILE]:[LINE]`

### Impact Statement
The application fails to verify if the authenticated user owns the requested resource before performing an action, leading to unauthorized data access or modification.

### Evidence Checklist
- [ ] Code snippet showing the lookup without an ownership check
- [ ] Comparison with a "Secure" implementation in the same codebase (if available)
- [ ] PoC demonstrating cross-user data access
