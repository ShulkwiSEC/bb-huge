# Mobile Bug Bounty Methodology

This reference defines the structured approach for hunting vulnerabilities in mobile applications (Android/iOS).

## 📱 Android Analysis (APK)

### 1. Static Analysis
- **Decompilation**: Use `JADX-GUI` or `apktool`.
- **Manifest Review**: Check `AndroidManifest.xml` for:
  - `exported="true"` activities, services, or receivers (CWE-926).
  - Weak permissions or custom permissions.
  - Hardcoded API keys or secrets in strings.xml or code.
- **Library Audit**: Check for vulnerable third-party SDKs.

### 2. Dynamic Analysis
- **Interception**: Configure Burp Suite proxy for mobile traffic.
- **SSL Pinning Bypass**: Use `Frida` with universal bypass scripts.
- **Hooking**: Use `objection` or custom Frida scripts to monitor method calls.
- **Logcat**: Monitor system logs for sensitive data leakage (CWE-532).

---

## 🍎 iOS Analysis (IPA)

### 1. Static Analysis
- **Dump Decrypted IPA**: Use `frida-ios-dump`.
- **Class Analysis**: Use `class-dump` or `Hopper/Ghidra` to inspect methods.
- **Binary Protections**: Verify PIE, Stack Canary, and ARC are enabled.

### 2. Dynamic Analysis
- **Proxy**: Set up Burp Suite with iOS CA certificate.
- **Keychain Analysis**: Inspect stored secrets via `objection`.
- **Runtime Hooking**: Frida scripts to bypass jailbreak detection and pinning.

---

## 🐛 Common Mobile Vulnerabilities

| Vuln Type | CWE | Description |
|---|---|---|
| Insecure Data Storage | CWE-312 | Sensitive data in SharedPreferences, Plist, or Local DB. |
| Insecure Auth | CWE-287 | Biometric bypass or weak session handling. |
| Improper Deep Link | CWE-939 | Unvalidated deep link parameters causing RCE or XSS. |
| Insecure WebView | CWE-749 | JavascriptInterface exposure or file:// access. |
| Tapjacking | CWE-1021 | Malicious overlay stealing user clicks. |

---

## 📁 Evidence Requirements

- **Static**: Code snippet from JADX/Hopper + file path.
- **Dynamic**: Frida console output or Burp HTTP pair.
- **Visual**: Screenshot showing the vulnerability in action.
- **PoC**: ADB command or Frida script to reproduce.
