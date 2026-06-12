# CVSS 4.0 Reference Guide

## Vector Format
`CVSS:4.0/AV:_/AC:_/AT:_/PR:_/UI:_/VC:_/VI:_/VA:_/SC:_/SI:_/SA:_`

---

## Metric Quick Reference

| Metric | Code | Low/None | High |
|---|---|---|---|
| Attack Vector | AV | P=Physical, L=Local, A=Adjacent | N=Network |
| Attack Complexity | AC | H=High (race/config needed) | L=Low (works reliably) |
| Attack Requirements (NEW) | AT | P=Specific config needed | N=No prerequisites |
| Privileges Required | PR | H=Admin, L=Regular user | N=No auth |
| User Interaction | UI | A=Active click, P=Passive visit | N=None needed |
| Confidentiality (Vuln System) | VC | N=None, L=Partial | H=Full read |
| Integrity (Vuln System) | VI | N=None, L=Limited modify | H=Full control |
| Availability (Vuln System) | VA | N=None, L=Partial | H=Full DoS |
| Confidentiality (Subsequent) | SC | N=None, L=Partial | H=Other systems |
| Integrity (Subsequent) | SI | N=None, L=Limited | H=Other systems |
| Availability (Subsequent) | SA | N=None | H=Other systems |

Subsequent System (SC/SI/SA) = impact beyond the directly exploited component (e.g., SSRF reaching cloud metadata, XSS stealing session used on other services).

---

## Pre-Calculated Profiles for Common Bug Bounty Vulns

### RCE — Unauthenticated, Network
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H
Score: 10.0 — Critical
```

### SSRF — Unauthenticated, Internal Network/Cloud Metadata Access
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:H/SI:H/SA:H
Score: ~8.7 — High
```
*VC is Low (local system doesn't expose much), but SC/SI/SA are High because attacker reaches internal services.*

### Host Header Injection → Password Reset Poisoning
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:H/VI:H/VA:N/SC:H/SI:H/SA:N
Score: ~8.9 — High/Critical
```
*UI:A because victim must click poisoned reset link. SC:H because attacker gains access to victim's account (subsequent system).*

### Stored XSS — No Auth for Injection Point
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:P/VC:L/VI:L/VA:N/SC:H/SI:H/SA:N
Score: ~8.2 — High
```
*UI:P (Passive) because victim just needs to visit page. SC:H for session hijack enabling full account control.*

### Reflected XSS — Requires User Click
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:L/VI:L/VA:N/SC:H/SI:H/SA:N
Score: ~7.1 — High
```

### IDOR — Access Any User's Data (Low-Priv Auth)
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:L/VA:N/SC:N/SI:N/SA:N
Score: ~7.1 — High
```

### Unauthenticated API Endpoint — PII/Sensitive Data Exposure
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
Score: ~8.7 — High
```

### SQL Injection — Auth Required, MySQL
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:L/SC:L/SI:L/SA:N
Score: ~8.5 — High
```

### Open Redirect — Account Takeover via OAuth
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:H/VI:H/VA:N/SC:H/SI:H/SA:N
Score: ~8.7 — High
```

### Broken Auth / Password Reset Flaw
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N
Score: ~9.3 — Critical
```

### DoS — Unauthenticated, Resource Exhaustion
```
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:H
Score: ~8.7 — High
```

---

## Severity Thresholds (CVSS 4.0)
| Range | Severity |
|---|---|
| 9.0–10.0 | Critical |
| 7.0–8.9 | High |
| 4.0–6.9 | Medium |
| 0.1–3.9 | Low |

## Official Calculator
https://www.first.org/cvss/calculator/4.0
