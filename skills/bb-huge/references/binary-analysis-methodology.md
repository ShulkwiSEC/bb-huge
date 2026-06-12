# Binary Analysis & Reverse Engineering Methodology

This reference defines the methodology for analyzing executable binaries (Windows/Linux/Linux) for security flaws.

## 🔍 Static Analysis

### 1. Triage
- **Identification**: Use `file`, `strings`, and `checksec`.
- **Packing**: Check for UPX or custom packers via entropy analysis.
- **Imports/Exports**: Analyze linked libraries and functions (CWE-427).

### 2. Disassembly & Decompilation
- **Tooling**: Use `Ghidra`, `IDA Pro`, or `Binary Ninja`.
- **Logic Flow**: Trace function calls and control flow graphs.
- **Constants**: Search for hardcoded keys, IPs, or magic numbers (CWE-321).

---

## 🛠️ Dynamic Analysis

### 1. Debugging
- **Tooling**: Use `GDB` (Linux) or `x64dbg` (Windows).
- **Tracing**: Monitor syscalls via `strace` or API calls via `API Monitor`.
- **Fuzzing**: Identify crash-inducing inputs (CWE-120).

### 2. Environment Simulation
- **Sandbox**: Run suspicious binaries in isolated VMs (CWE-497).
- **Network**: Monitor C2 traffic via Wireshark or FakeNet.

---

## 🐛 Common Binary Vulnerabilities

| Vuln Type | CWE | Description |
|---|---|---|
| Buffer Overflow | CWE-120 | Unbounded copy into stack/heap buffers. |
| Use-After-Free | CWE-416 | Accessing memory after it has been freed. |
| Integer Overflow | CWE-190 | Arithmetic overflow causing logic bypass. |
| Format String | CWE-134 | Unsanitized user input in printf-like functions. |
| DLL Hijacking | CWE-427 | Insecure loading of dynamic libraries. |

---

## 📁 Evidence Requirements

- **Disassembly**: Annotated assembly snippets from Ghidra/IDA.
- **Debug Output**: Stack traces or register dumps during a crash.
- **IOCs**: List of hashes, C2 addresses, or mutexes.
- **PoC**: Step-by-step instructions or Python exploit script.
