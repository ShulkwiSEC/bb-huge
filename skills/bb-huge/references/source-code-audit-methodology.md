# Source Code Audit Methodology (White-Box Review)

This reference defines the methodology for performing security audits on source code repositories.

## 🔎 Audit Process

### 1. Discovery
- **Tech Stack**: Identify languages, frameworks, and database types.
- **Entry Points**: Map controllers, API routes, and public interfaces.
- **Dependencies**: Check `package.json`, `Cargo.toml`, or `requirements.txt` for vulnerable versions (CWE-1104).

### 2. Automated Scanning (SAST)
- **Tooling**: Use `Semgrep`, `Snyk`, `CodeQL`, or `SonarQube`.
- **Triage**: Filter out false positives and prioritize reachable sinks.

### 3. Manual Review
- **Data Flow**: Trace user input from source to dangerous sinks (e.g., DB queries, shell execution).
- **Logic Check**: Audit authentication and authorization checks (BOLA/BFLA).
- **Secret Scan**: Use `Trufflehog` or `Gitleaks` to find hardcoded credentials.

---

## 🐛 Language-Specific Patterns

| Language | Common Flaws |
|---|---|
| **Python** | `pickle.load` (RCE), `eval`, `os.system` (Cmd Injection), `Jinja2` (SSTI). |
| **JS/TS** | Prototype Pollution, `eval`, `dangerouslySetInnerHTML` (XSS), `vm.runInNewContext`. |
| **Go** | `template.HTML` (XSS), Unsafe Pointers, Race Conditions, `exec.Command`. |
| **C/C++** | `strcpy` (Overflow), Format Strings, Use-After-Free, Integer Overflows. |
| **PHP** | Type Juggling (`==`), `unserialize` (RCE), LFI/RFI, `exec`. |

---

## 📁 Evidence Requirements

- **File Reference**: Path to the vulnerable file and line number(s).
- **Code Snippet**: The specific block of code containing the flaw.
- **Trace**: Documentation of the input-to-sink data flow path.
- **Fix**: Suggested code remediation with a "Before vs After" example.
- **PoC**: CURL command or script demonstrating the vulnerability reachability.
