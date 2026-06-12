# bb-huge Curated Security Skills Manifest

This directory contains a collection of 350+ security skills curated for use with bb-huge and compatible AI agents (OpenCode, Claude Code, etc.).

## Source Credits

| Collection | Source | Count |
|------------|--------|-------|
| Hack Skills | [yaklang/hack-skills](https://github.com/yaklang/hack-skills) | 100 |
| Hacking Skills | [B-Step62/hacking-skills](https://github.com/B-Step62/hacking-skills) | 120 |
| Offensive Security Skills | [0x0pointer/awesome-offensive-security-skills](https://github.com/0x0pointer/awesome-offensive-security-skills) | 80 |
| Awesome Skills Security | [cloudevops33/awesome-skills-security](https://github.com/cloudevops33/awesome-skills-security) | 30 |
| bb-huge Internal | Built-in | 22 |

## Web Application Security

| Skill | Description |
|-------|-------------|
| `advanced-sql-injection-sqli` | > |
| `ai-data-extraction-via-ssrf` | > |
| `api-auth-and-jwt-abuse` | >- |
| `aws-imdsv2-ssrf-bypass` | > |
| `aws-metadata-ssrf` | > |
| `aws-metadata-ssrf-exploitation` | > |
| `csrf` | > |
| `csrf-cross-site-request-forgery` | >- |
| `csrf-token-bypass-techniques` | > |
| `dom-based-cross-site-scripting-xss` | > |
| `dom-based-xss` | > |
| `dom-xss` | > |
| `graphql-and-hidden-parameters` | >- |
| `graphql-batching-attacks` | > |
| `graphql-idor` | > |
| `graphql-idor-via-introspection-leak` | Covers object-level authorization bypass in GraphQL APIs where introspection reveals hidden fields or mutations that accept arbitrary user/resource IDs without ownership checks. Trigger on keywords like "GraphQL", "query", "mutation", "introspection", "resolver", "node ID", "relay", "object type", "schema", "batching", or "alias". Applies to dual-stack REST+GraphQL apps, Relay-style global IDs, and unauthenticated resolvers. |
| `graphql-injection-introspection` | > |
| `graphql-introspection-abuse` | > |
| `graphql-labs` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `http-request-smuggling` | > |
| `http-request-smuggling-desync` | > |
| `http-request-smuggling-te-te` | > |
| `javascript-prototype-pollution` | > |
| `jwt-algorithm-confusion` | > |
| `jwt-forgery-algorithm-confusion` | > |
| `jwt-labs` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `jwt-misconfig` | > |
| `jwt-null-signature` | > |
| `jwt-oauth-token-attacks` | >- |
| `nosql-injection` | >- |
| `open-redirect` | >- |
| `open-redirect-chaining-attacks` | > |
| `param-fuzz` | \| |
| `path-traversal` | > |
| `path-traversal-lfi` | >- |
| `prototype-pollution` | >- |
| `prototype-pollution-advanced` | >- |
| `prototype-pollution-rce` | > |
| `sqli-manual-and-automated` | > |
| `sqli-sql-injection` | >- |
| `ssrf` | > |
| `ssrf-aws-metadata-abuse` | > |
| `ssrf-nextjs-server-actions` | > |
| `ssrf-server-side-request-forgery` | >- |
| `ssti` | > |
| `ssti-server-side-template-injection` | >- |
| `web-application-recon-and-enumeration` | > |
| `web-cache-deception` | >- |
| `web-cache-poisoning` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `web-cache-poisoning-deception` | > |
| `web-exploit` | \| |
| `web-fingerprinting` | > |
| `websockets` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `xslt-injection` | >- |
| `xss` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `xss-cross-site-scripting` | >- |
| `xss-reflected` | > |
| `xss-reflected-stored-dom` | > |
| `xss-stored` | > |
| `xxe` | > |
| `xxe-xml-external-entity` | >- |
| `xxe-xml-external-entity-injection` | > |

## Authentication & Access Control

| Skill | Description |
|-------|-------------|
| `2fa-bypass` | > |
| `access-control` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `ai-agent-tool-abuse-and-privilege-escalation` | > |
| `api-authentication-bypass` | > |
| `api-authorization-and-bola` | >- |
| `auth-bypass` | > |
| `auth-sec` | >- |
| `authbypass-authentication-flaws` | >- |
| `authentication` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `authz-bypass` | > |
| `aws-iam-privilege-escalation` | > |
| `bola-idor` | > |
| `broken-object-level-authorization` | > |
| `idor-broken-object-authorization` | >- |
| `idor-vulnerability-hunting` | > |
| `insecure-direct-object-reference-idor` | > |
| `linux-privilege-escalation` | >- |
| `mobile-auth-bypass` | > |
| `oauth` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `oauth-flow-exploitation` | > |
| `oauth-oidc-misconfiguration` | >- |
| `oauth-security` | \| |
| `oauth-state-parameter-abuse` | > |
| `password-reset-flaws` | > |
| `saml-sso-assertion-attacks` | >- |
| `session-fixation` | > |
| `session-search-tool` | > |
| `unauthorized-access-common-services` | >- |
| `windows-privilege-escalation` | >- |
| `windows-token-impersonation` | > |

## Active Directory & Windows Security

| Skill | Description |
|-------|-------------|
| `active-directory-acl-abuse` | >- |
| `active-directory-asreproasting` | > |
| `active-directory-certificate-services` | >- |
| `active-directory-dcsync-attack` | > |
| `active-directory-full-attack-chain` | > |
| `active-directory-golden-ticket` | > |
| `active-directory-kerberoasting` | > |
| `active-directory-kerberos-attacks` | >- |
| `ad-asreproast-attack` | > |
| `ad-assessment` | \| |
| `ad-cs-esc1-abuse` | > |
| `ad-dcsync-attack` | > |
| `ad-pass-the-hash` | > |
| `azure-ad-illicit-consent-grant` | > |
| `azure-ad-lateral-movement` | > |
| `certutil-download-execution` | > |
| `kerberoasting-active-directory` | > |
| `ntlm-relay-coercion` | >- |
| `ntlm-relay-smb-signing-bypass` | > |
| `phishing-payload-generation` | > |
| `upload-insecure-files` | >- |
| `windows-av-evasion` | >- |
| `windows-event-logs-analysis` | > |
| `windows-lateral-movement` | >- |
| `windows-prefetch-analysis` | > |
| `windows-registry-autorun-forensics` | > |
| `windows-registry-forensics` | > |
| `wmi-event-subscription` | > |
| `wmi-event-subscription-persistence` | > |
| `wmi-event-subscriptions` | > |
| `wmi-execution` | > |
| `zero-logon-exploitation` | > |

## Cloud & Container Security

| Skill | Description |
|-------|-------------|
| `aws-cloud-penetration-testing` | > |
| `aws-cognito-abuse` | > |
| `azure-managed-identity-abuse` | > |
| `business-logic-flaws` | > |
| `cloud-security` | \| |
| `container-escape-techniques` | >- |
| `container-k8s-security` | \| |
| `docker-container-escape` | > |
| `docker-daemon-privesc` | > |
| `kubernetes-pentesting` | >- |
| `kubernetes-rbac-exploitation` | > |

## Mobile Security

| Skill | Description |
|-------|-------------|
| `android-apk-reverse-engineering` | > |
| `android-pentesting-tricks` | >- |
| `ios-application-hooking-frida` | > |
| `ios-pentesting-tricks` | >- |
| `mobile-code-quality` | > |
| `mobile-insecure-storage` | > |
| `mobile-network-security` | > |
| `mobile-platform-interaction` | > |
| `mobile-resilience` | > |
| `mobile-ssl-pinning-bypass` | >- |
| `mobile-weak-crypto` | > |

## Binary Exploitation & Reverse Engineering

| Skill | Description |
|-------|-------------|
| `binary-protection-bypass` | >- |
| `buffer-overflow-stack` | > |
| `code-obfuscation-deobfuscation` | >- |
| `format-string-exploitation` | >- |
| `heap-exploitation` | >- |
| `portable-executable-analysis` | > |
| `pwn-request` | > |
| `reverse-shell` | \| |
| `reverse-shell-techniques` | >- |
| `stack-overflow-and-rop` | >- |
| `vm-and-bytecode-reverse` | >- |

## OSINT & Reconnaissance

| Skill | Description |
|-------|-------------|
| `api-recon-and-docs` | >- |
| `domain-and-asn-enumeration` | > |
| `nmap-advanced-network-scanning` | > |
| `osint` | \| |
| `recon-and-methodology` | >- |
| `recon-for-sec` | >- |
| `shodan-dorking` | > |
| `subdomain-takeover` | >- |

## AI / LLM Security

| Skill | Description |
|-------|-------------|
| `ai-data-poisoning` | > |
| `ai-data-poisoning-model-skewing` | > |
| `ai-jailbreak-obfuscation-ciphers` | > |
| `ai-jailbreak-prompt-injection` | > |
| `ai-jailbreak-system-prompts` | > |
| `ai-ml-security` | >- |
| `ai-pair-hunting-with-claude` | > |
| `ai-prompt-leaking` | > |
| `ai-redteam` | \| |
| `ai-report-writing-guardrails` | > |
| `data-poisoning-and-backdoors` | > |
| `indirect-prompt-injection` | > |
| `llm-attacks` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `llm-direct-prompt-injection` | > |
| `llm-indirect-prompt-injection` | > |
| `llm-jailbreaking-personas` | > |
| `llm-jailbreaking-techniques` | > |
| `llm-overreliance-hallucination` | > |
| `llm-prompt-injection` | >- |
| `llm-prompt-injection-indirect` | > |
| `llm-supply-chain-poisoning` | > |
| `llm-testing` | Comprehensive LLM security testing prompts for bias detection, data leakage, alignment testing, and adversarial prompt resistance. |
| `llm-training-data-extraction` | > |
| `model-inversion-attacks` | > |
| `rag-poisoning-and-data-exfiltration` | > |

## CI/CD & Supply Chain

| Skill | Description |
|-------|-------------|
| `cicd-bot-command-injection` | > |
| `dependency-confusion` | >- |
| `github-actions-cache-poisoning` | > |
| `github-actions-script-injection` | > |
| `self-hosted-runner-poisoning` | > |

## Network & Infrastructure

| Skill | Description |
|-------|-------------|
| `bgp-hijacking-concepts` | > |
| `dns-rebinding-attacks` | >- |
| `ipv6-dns-takeover-mitm` | > |
| `ipv6-dns-takeover-mitm6` | > |
| `network-assess` | \| |
| `network-protocol-attacks` | >- |
| `smtp-open-relay-abuse` | > |
| `ssl-tls-audit` | \| |
| `traffic-analysis-pcap` | >- |
| `vlan-hopping-and-trunking` | > |
| `vlan-hopping-attacks` | > |
| `wifi-penetration-testing` | > |

## Red Team & Post-Exploitation

| Skill | Description |
|-------|-------------|
| `av-edr-evasion-techniques` | > |
| `cobalt-strike-beacon-operations` | > |
| `cobalt-strike-malleable-c2` | > |
| `lateral-movement` | \| |
| `linux-lateral-movement` | >- |
| `phishing-and-social-engineering-campaigns` | > |
| `post-exploit` | \| |
| `psexec-lateral-movement` | > |
| `tunneling-and-pivoting` | >- |

## Forensics & Malware Analysis

| Skill | Description |
|-------|-------------|
| `dynamic-malware-analysis` | > |
| `macos-unified-log-analysis` | > |
| `memory-forensics-volatility` | >- |
| `volatility-memory-forensics` | > |
| `yara-rule-development` | > |
| `yara-rule-writing-malware` | > |
| `zeek-conn-log-analysis` | > |

## Payloads & Wordlists

| Skill | Description |
|-------|-------------|
| `api-enumeration-fuzzing-discovery` | > |
| `defi-attack-patterns` | >- |
| `security-fuzzing` | Essential fuzzing payloads: SQL injection, command injection, special characters. Curated essentials for vulnerability testing. |
| `security-passwords` | Top password lists for authorized security testing: common passwords, darkweb leaks, worst passwords. Curated essentials (<10MB). |
| `security-patterns` | Sensitive data patterns for security testing: API keys, credit cards, emails, SSNs, phone numbers, IPs, and more. Use for data discovery and validation. |
| `security-payloads` | Essential exploitation payloads: anti-virus test files, file name exploits, malicious files. Curated for testing. |
| `security-usernames` | Top username lists for enumeration: common usernames, default credentials, names. Curated essentials for authorized testing. |
| `security-webshells` | Web shell samples for detection and analysis: PHP, ASP, ASPX, JSP, Python, Perl shells. Use for security research and detection system testing. |

## Methodology & Reporting

| Skill | Description |
|-------|-------------|
| `amend-skill` | > |
| `analyze-cve` | Analyzes CVE vulnerabilities in project dependencies with code path tracing and PoC generation for Burp Suite. Traces vulnerable code from user input to sink, assesses exploitability, and generates HTTP requests for testing. |
| `bug-bounty-report-writer` | Writes professional bug bounty reports for HackerOne, Bugcrowd, and Intigriti with CVSS 4.0 scoring, business impact, working exploits, and remediation. Runs 5-check Pre-Report Verification first: hallucination detection, AI writing patterns, PoC reproducibility, duplicate detection, and impact plausibility. Use when user describes a vulnerability, shares HTTP logs, HAR files, recon output, or screenshots; says 'write a bug report', 'format my finding', 'draft a vuln report', 'is this valid', 'rate my vulnerability', 'verify my report', or any variant. Trigger for partial or messy input — raw notes, one-liners, or full writeups all work. Do not wait for perfect input. |
| `burp-suite-advanced-methodology` | > |
| `compliance` | \| |
| `credential-audit` | \| |
| `cve-2023-36884-office-rce` | > |
| `distill-skill` | > |
| `observe-skill` | > |
| `report` | Generate a NullPointer Studio styled PDF penetration test report from findings.json. Produces a professional dark-themed PDF with executive summary, risk dashboard, per-finding cards with business risk, remediation summary, and clean controls section. |
| `request-cves` | \| |
| `threat-modeling` | \| |

## Other

| Skill | Description |
|-------|-------------|
| `401-403-bypass-techniques` | >- |
| `aikido-triage` | Triages an Aikido security findings CSV against a local codebase. For each finding, reads the flagged file, traces the code path, and verdicts it as KEEP OPEN or CLOSE with a specific reason. Outputs a reviewed CSV and a self-contained HTML evidence report. Run this at the end of a pentest when an Aikido CSV is available. |
| `amsi-bypass` | > |
| `anti-debugging-techniques` | >- |
| `api-mass-assignment-exploitation` | > |
| `api-rate-limit-bypass-techniques` | > |
| `api-sec` | >- |
| `api-security` | \| |
| `api-testing-labs` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `arbitrary-write-to-rce` | >- |
| `browser-exploitation-v8` | >- |
| `bug-bounty-workflow-funnel` | > |
| `business-logic` | \| |
| `business-logic-bypass` | > |
| `business-logic-vuln` | >- |
| `business-logic-vulnerabilities` | >- |
| `cache-deception` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `classical-cipher-analysis` | >- |
| `claude-skills-for-bug-bounty` | > |
| `clickjacking` | >- |
| `clickjacking-ui-redressing` | > |
| `cmd-injection` | > |
| `cmdi-command-injection` | >- |
| `codebase` | \| |
| `colang-gen` | Generates NeMo Guardrails Colang (.co) files and YAML config blocks from a plain-language description of a chatbot's purpose, allowed behaviors, and constraints. Use this skill whenever a user wants to build guardrails for a chatbot, define allowed intents for an LLM, create an AI firewall with NeMo Guardrails, generate Colang flow definitions, or configure a semantic allow-list for a bot. Trigger this skill even when the user just describes what their bot should and shouldn't do — generating the Colang and YAML is almost always what they need next. |
| `command-injection-os-level` | > |
| `cookie-attacks` | > |
| `cors` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `cors-cross-origin-misconfiguration` | >- |
| `cors-misconfig` | > |
| `cors-misconfiguration-exploitation` | > |
| `crlf-injection` | >- |
| `csp-bypass-advanced` | >- |
| `cspt` | > |
| `csv-formula-injection` | >- |
| `dangling-markup-injection` | >- |
| `data-exfiltration-techniques` | > |
| `data-extraction-training-data` | > |
| `deepfake-detection-and-analysis` | > |
| `default-credentials` | > |
| `deserialization-insecure` | >- |
| `django-sql-injection` | > |
| `dll-hijacking-privesc` | > |
| `dom-vulns` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `email-header-injection` | >- |
| `email-security` | \| |
| `essential-skills` | PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `expression-language-injection` | >- |
| `file-access-vuln` | >- |
| `file-upload` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `gh-export` | Formats all confirmed pentest findings from findings.json into copy-pasteable GitHub issue markdown blocks, following the AppSec reporting guide template. |
| `ghost-bits-cast-attack` | >- |
| `hack` | >- |
| `hackerone-brain-mcp` | > |
| `hash-attack-techniques` | >- |
| `host-header` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `host-header-injection-attacks` | > |
| `http-host-header-attacks` | >- |
| `http-parameter-pollution` | >- |
| `http2-specific-attacks` | >- |
| `info-disclosure` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `injection-checking` | >- |
| `insecure-deserialization` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `insecure-file-upload` | > |
| `insecure-source-code-management` | >- |
| `java-insecure-deserialization-ysoserial` | > |
| `jndi-injection` | >- |
| `kaido-proxy-integration` | > |
| `kerberoasting-attack` | > |
| `kernel-exploitation` | >- |
| `lattice-crypto-attacks` | >- |
| `linux-capabilities-privesc` | > |
| `linux-security-bypass` | >- |
| `macos-process-injection` | >- |
| `macos-security-bypass` | >- |
| `mass-assignment` | > |
| `mass-assignment-exploitation` | > |
| `mcp-protocol-exploitation` | > |
| `metasploit` | \| |
| `nodejs-deserialization-rce` | > |
| `os-command-injection` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `pass-the-hash-and-ticket` | > |
| `pentester-opencode` | Full penetration test using MCP tools — recon, scanning, exploitation, and reporting. Tailored for OpenCode (BYO LLM). Supports network/web targets and local codebases. Chains into analyze-cve, threat-modeling, and remediate skills automatically. |
| `php-deserialization-rce` | > |
| `process-hollowing` | > |
| `prompt-leaking-system-prompts` | > |
| `race-condition` | >- |
| `race-condition-toctou-exploitation` | > |
| `race-conditions-labs` | Complete PortSwigger deep-dive with exact payloads for every lab variant including zero-day techniques |
| `remediate` | \| |
| `remote-hunting-workflow` | > |
| `request-smuggling` | >- |
| `rogue-access-point-evil-twin` | > |
| `rsa-attack-techniques` | >- |
| `sandbox-escape-techniques` | >- |
| `semgrep-custom-rule-writing` | > |
| `server-side-template-injection` | > |
| `smart-contract-vulnerabilities` | >- |
| `spring-boot-actuator-abuse` | > |
| `sql-injection` | > |
| `steganography-techniques` | >- |
| `symbolic-execution-tools` | >- |
| `symmetric-cipher-attacks` | >- |
| `sysmon-process-creation-analysis` | > |
| `type-juggling` | >- |
| `waf-bypass-techniques` | >- |
| `websocket-hijacking-testing` | > |
| `websocket-security` | >- |
| `zero-day-research-skill` | > |

