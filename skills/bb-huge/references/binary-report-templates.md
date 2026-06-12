# Binary Bug Bounty Report Templates

This reference provides standardized templates for reporting binary-level vulnerabilities.

## 1. Stack-Based Buffer Overflow (CWE-120)

### Title Formula
`Stack-based Buffer Overflow in [FUNCTION] of [BINARY] via [PARAMETER]`

### Impact Statement
An attacker can overwrite the return address on the stack, leading to control of the instruction pointer (EIP/RIP) and potential Remote Code Execution (RCE).

### Evidence Checklist
- [ ] Vulnerable code snippet (disassembly/pseudocode)
- [ ] Offset to the return address
- [ ] Crash dump (GDB/x64dbg output showing EIP control)
- [ ] Payload used to trigger the crash

---

## 2. Use-After-Free (CWE-416)

### Title Formula
`Use-After-Free in [MODULE] allows [IMPACT]`

### Impact Statement
Accessing memory after it has been freed can lead to memory corruption, information leakage, or arbitrary code execution by hijacking the freed object.

### Evidence Checklist
- [ ] Free() call location and subsequent Use location
- [ ] Logic trace showing how the free'd memory is reachable
- [ ] Debugger output showing heap state
- [ ] PoC triggering the crash or corruption

---

## 3. Integer Overflow (CWE-190)

### Title Formula
`Integer Overflow in [CALCULATION] leads to [BUFFER_OVERFLOW/LOGIC_BYPASS]`

### Impact Statement
Improper arithmetic handling allows large values to wrap around, resulting in smaller-than-expected buffer allocations or bypassed security checks.

### Evidence Checklist
- [ ] Disassembly showing the vulnerable arithmetic operation
- [ ] Values used to trigger the overflow
- [ ] Downstream impact (e.g., small malloc call followed by large memcpy)

---

## 4. DLL/Shared Library Hijacking (CWE-427)

### Title Formula
`DLL Hijacking in [BINARY] allows Local Privilege Escalation`

### Impact Statement
An attacker can place a malicious library in a high-priority search path, causing the binary to execute attacker-controlled code with its own privileges.

### Evidence Checklist
- [ ] Process Monitor (ProcMon) log showing "NAME NOT FOUND" for the DLL
- [ ] The search path order used by the application
- [ ] PoC DLL and confirmation of execution

---

## 5. Insecure Privileged Service (CWE-732)

### Title Formula
`Insecure Permissions on [SERVICE/BINARY] allow [PRIVILEGE_ESCALATION]`

### Impact Statement
Weak filesystem or service permissions allow unprivileged users to modify executable code or service configurations, leading to full system compromise.

### Evidence Checklist
- [ ] Output of `icacls` (Windows) or `ls -l` (Linux)
- [ ] Verification of the service user context (e.g., SYSTEM or root)
- [ ] PoC showing modification and escalation
