# Mobile Bug Bounty Report Templates

This reference provides standardized templates for reporting mobile vulnerabilities.

## 1. Insecure Data Storage (CWE-312)

### Title Formula
`Insecure storage of [DATA_TYPE] in [STORAGE_TYPE] (Android/iOS)`

### Impact Statement
Sensitive information is stored in plaintext on the device, allowing an attacker with physical access or a secondary malware app to steal [DATA_TYPE].

### Evidence Checklist
- [ ] Path to the file (e.g., `/data/data/[PACKAGE]/shared_prefs/prefs.xml`)
- [ ] Code snippet showing the insecure write
- [ ] Screenshot of the plaintext data in a file explorer

---

## 2. Unvalidated Deep Link Handling (CWE-939)

### Title Formula
`Deep Link vulnerability on [SCHEME]://[HOST] allows [ACTION]`

### Impact Statement
An attacker can trigger unauthorized actions (e.g., password change, fund transfer) by tricking a user into clicking a malicious link.

### Evidence Checklist
- [ ] Vulnerable intent filter in `AndroidManifest.xml`
- [ ] Vulnerable code in `onNewIntent` or similar
- [ ] PoC ADB command: `adb shell am start -W -a android.intent.action.VIEW -d "[MALICIOUS_LINK]"`

---

## 3. WebView JavascriptInterface Exposure (CWE-749)

### Title Formula
`Insecure JavascriptInterface in WebView allows [RCE/XSS]`

### Impact Statement
A malicious website loaded in the app's WebView can execute arbitrary Java code on the device via the exposed bridge.

### Evidence Checklist
- [ ] Code snippet showing `addJavascriptInterface`
- [ ] Proof that `setJavaScriptEnabled(true)` is active
- [ ] HTML payload used to trigger the bridge

---

## 4. SSL Pinning Bypass (CWE-295)

### Title Formula
`SSL Pinning Bypass allows MiTM on [ENVIRONMENT]`

### Impact Statement
An attacker on the same network can intercept and modify encrypted traffic, stealing session tokens or user data.

### Evidence Checklist
- [ ] Frida script used for bypass
- [ ] Burp Suite logs showing decrypted traffic
- [ ] Evidence that pinning was expected but failed

---

## 5. Exported Activity without Authorization (CWE-926)

### Title Formula
`Exported [ACTIVITY_NAME] allows unauthorized access to [FEATURE]`

### Impact Statement
Other apps on the device can launch internal activities to bypass authentication or access restricted data.

### Evidence Checklist
- [ ] Manifest snippet showing `exported="true"`
- [ ] PoC ADB command: `adb shell am start -n [PACKAGE]/[ACTIVITY]`
- [ ] Screenshot of the launched activity bypassing a gate
