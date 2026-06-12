# Business Impact Quantification Templates

Impact quantification is what separates a $500 bounty from a $50,000 one.
Triagers escalate reports that make the business case obvious. Use real numbers from
public data (Crunchbase, press releases, App Store, LinkedIn company page).

---

## Finding Target Size
Before quantifying, research:
- User count: company blog, press releases, App Store "X downloads", LinkedIn employees as proxy
- Revenue: Crunchbase, SEC filings (public companies), funding rounds
- Industry: determines applicable regulations (GDPR, HIPAA, PCI-DSS)

---

## Templates by Vulnerability Type

### Data Breach / PII Exposure
```
This endpoint exposes [data types: emails, passwords, PII] without authentication.
With [Company]'s estimated [X million] user base:
- Records at risk: up to [X]M user records
- GDPR/CCPA maximum fine: €20M or 4% of annual global revenue (whichever higher)
- Average breach cost per record (IBM 2024): $165 → estimated total exposure: $[X × 165]
- Class-action and regulatory investigation risk
```

### Account Takeover
```
This vulnerability enables full account takeover without requiring any user interaction.
At scale:
- [Company] has [X]M registered accounts — all are at risk
- Compromised accounts can be used for: fraud, data theft, privilege escalation to admin
- Dark web market rate for accounts with linked payment methods: $10–$50/account
- Reputational: mass ATO events routinely result in news coverage and user churn
```

### SSRF → Cloud Metadata / Internal Access
```
Successful exploitation reaches [Company]'s internal infrastructure from the internet:
- AWS IMDSv1/GCP/Azure metadata accessible → IAM credentials extractable → full cloud takeover
- Internal service enumeration enables lateral movement to databases, caches, admin panels
- Blast radius: all internal services reachable from the vulnerable application server
- AWS account compromise average cost (IBM 2024): $1.2M–$4.8M
- If cloud credentials obtained: complete infrastructure takeover is possible
```

### Host Header Injection / Password Reset Poisoning
```
An attacker can intercept password reset tokens for any account — including admins and executives:
- Targeted account takeover of high-value users (executives, paying customers, admins)
- No user interaction required beyond clicking a normal-looking reset email
- With admin account access: full application compromise
- At scale: sending poisoned resets to [X]% of [Y]M users = [Z] accounts at risk
```

### Stored XSS
```
Persistent XSS executes in victims' browsers on every page visit. Consequences:
- Session token theft → mass account takeover
- Credential harvesting via DOM overlay phishing
- Malware distribution to [X] daily active users visiting [affected page]
- One injected payload affects all users — no per-victim interaction required
```

### SQL Injection
```
Attacker can extract the full application database:
- Tables at risk: [list key tables — users, payments, sessions]
- Records: [X]M rows
- Sensitive columns: [passwords, PII, payment methods, API keys]
- If MSSQL xp_cmdshell or MySQL FILE privilege enabled: escalates to OS-level RCE
- PCI-DSS scope: if payment data present, mandatory breach notification + fines apply
```

### IDOR (Broken Object Level Authorization)
```
Any authenticated user can access any other user's [resource type]:
- [X]M users' [data type] accessible with a single token change
- Horizontal privilege escalation — no admin access required
- Automated enumeration can drain entire dataset in minutes
- SOC 2 / ISO 27001 access control violation
```

### Authentication Bypass
```
Attacker gains [admin/user] access without valid credentials:
- [X]M accounts accessible
- [Admin bypass]: complete application compromise — all user data, config, secrets
- Regulatory: authentication failure is a critical finding under SOC 2 CC6.1, ISO 27001 A.9
```

### DoS / Resource Exhaustion
```
Single unauthenticated request can take down [service/endpoint]:
- [Company] revenue per hour downtime: est. $[X] (based on $[ARR]/8760 hours)
- SLA violation risk for enterprise customers
- Automated attacks can keep service offline indefinitely
- Requires zero authentication — anyone on the internet can trigger this
```
