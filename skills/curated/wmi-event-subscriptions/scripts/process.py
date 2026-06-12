#!/usr/bin/env python3
"""
CI/CD Execution Harness for wmi-event-subscriptions
Validates WMI persistence technique documentation, detection coverage,
and attack methodology completeness.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

SKILL_NAME = "wmi-event-subscriptions"
SKILL_CATEGORY = "red-teaming/persistence"
MITRE_TECHNIQUES = ["T1546.003", "T1047"]
MITRE_TACTICS = ["TA0003", "TA0002"]


def validate_skill_structure() -> Dict:
    """Validate SKILL.md has all required sections with substantive content."""
    result = {"test": "skill_structure", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    if not skill_md.exists():
        result["details"] = "SKILL.md not found"
        return result
    
    content = skill_md.read_text(encoding="utf-8")
    
    required_sections = [
        ("## When to Use", 50),
        ("## Prerequisites", 30),
        ("## Workflow", 100),
        ("### Phase 1:", 50),
        ("### Phase 2:", 50),
        ("## 🔵 Blue Team", 100),
        ("## Key Concepts", 50),
        ("## References", 30),
        ("Decision Point", 20),
        ("## Output Format", 50),
    ]
    
    issues: List[str] = []
    for section_header, min_chars in required_sections:
        if section_header not in content:
            issues.append(f"Missing: {section_header}")
        else:
            idx = content.index(section_header)
            section_content = content[idx:idx + min_chars + 200]
            if len(section_content.strip()) < min_chars:
                issues.append(f"Thin content: {section_header} (<{min_chars} chars)")
    
    # Check for empty/placeholder content
    placeholder_patterns = ["# Placeholder", "TODO", "# Concept: 1.", 
                           "| AMSI | |", "| Fileless Malware | |"]
    for pattern in placeholder_patterns:
        if pattern in content:
            issues.append(f"Contains placeholder: '{pattern}'")
    
    if issues:
        result["details"] = f"{len(issues)} issues: {'; '.join(issues[:5])}"
    else:
        result["passed"] = True
        result["details"] = f"All {len(required_sections)} sections present with substantive content"
    
    return result


def validate_mitre_mapping() -> Dict:
    """Validate MITRE ATT&CK technique and tactic mappings."""
    result = {"test": "mitre_mapping", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    missing_techniques = [t for t in MITRE_TECHNIQUES if t not in content]
    missing_tactics = [t for t in MITRE_TACTICS if t not in content]
    
    if missing_techniques or missing_tactics:
        result["details"] = f"Missing techniques: {missing_techniques}, tactics: {missing_tactics}"
    else:
        result["passed"] = True
        result["details"] = f"All {len(MITRE_TECHNIQUES)} techniques and {len(MITRE_TACTICS)} tactics mapped"
    
    return result


def validate_detection_coverage() -> Dict:
    """Ensure blue team detection references are comprehensive."""
    result = {"test": "detection_coverage", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    required_detections = [
        "Sysmon Event ID 19",
        "Sysmon Event ID 20", 
        "Sysmon Event ID 21",
        "Script Block Logging",
        "Autoruns",
    ]
    
    missing = [d for d in required_detections if d not in content]
    
    if missing:
        result["details"] = f"Missing detection references: {', '.join(missing)}"
    else:
        result["passed"] = True
        result["details"] = f"All {len(required_detections)} detection methods documented"
    
    return result


def validate_code_blocks() -> Dict:
    """Validate that code blocks contain real, executable content."""
    result = {"test": "code_quality", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    code_block_pattern = r'```(?:powershell|bash|python|text|csharp)\n(.*?)```'
    code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
    
    if len(code_blocks) < 3:
        result["details"] = f"Only {len(code_blocks)} code blocks found (minimum 3)"
        return result
    
    empty_blocks = 0
    for block in code_blocks:
        lines = [ln.strip() for ln in block.strip().split('\n') if ln.strip() and not ln.strip().startswith('#')]
        if len(lines) < 2:
            empty_blocks += 1
    
    if empty_blocks > 1:
        result["details"] = f"{empty_blocks} code blocks have insufficient executable content"
    else:
        result["passed"] = True
        result["details"] = f"{len(code_blocks)} code blocks validated with substantive content"
    
    return result


def validate_mermaid_diagram() -> Dict:
    """Ensure mermaid decision diagram has labeled nodes."""
    result = {"test": "mermaid_diagram", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    mermaid_match = re.search(r'```mermaid\n(.*?)```', content, re.DOTALL)
    if not mermaid_match:
        result["details"] = "No mermaid diagram found"
        return result
    
    diagram = mermaid_match.group(1)
    
    # Check for empty node labels like "A[...]" with no real text
    empty_nodes = re.findall(r'\w+\[\s*\]', diagram)
    short_labels = re.findall(r'\w+\[.{1,3}\]', diagram)
    
    if empty_nodes:
        result["details"] = f"Found {len(empty_nodes)} empty diagram nodes"
    elif len(short_labels) > 2:
        result["details"] = f"Found {len(short_labels)} nodes with very short labels"
    else:
        node_count = len(re.findall(r'\w+\[', diagram))
        result["passed"] = True
        result["details"] = f"Mermaid diagram valid with {node_count} labeled nodes"
    
    return result


def validate_references() -> Dict:
    """Validate that references contain real URLs."""
    result = {"test": "references", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    url_pattern = r'https?://[^\s\)>]+'
    urls = re.findall(url_pattern, content)
    
    if len(urls) < 2:
        result["details"] = f"Only {len(urls)} reference URLs found (minimum 2)"
    else:
        result["passed"] = True
        result["details"] = f"{len(urls)} reference URLs included"
    
    return result


def main() -> None:
    print(f"[*] Running validation harness for: {SKILL_NAME}")
    print(f"[*] Category: {SKILL_CATEGORY}")
    print(f"[*] MITRE: {', '.join(MITRE_TECHNIQUES)}")
    print(f"[*] Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    tests = [
        validate_skill_structure,
        validate_mitre_mapping,
        validate_detection_coverage,
        validate_code_blocks,
        validate_mermaid_diagram,
        validate_references,
    ]
    
    results = []
    for test_fn in tests:
        try:
            test_result = test_fn()
        except Exception as exc:
            test_result = {"test": test_fn.__name__, "passed": False, "details": f"Error: {exc}"}
        results.append(test_result)
        status = "✅ PASS" if test_result["passed"] else "❌ FAIL"
        print(f"  {status} | {test_result['test']}: {test_result['details']}")
    
    print("=" * 60)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"[{'+'if passed == total else '!'}] Results: {passed}/{total} tests passed")
    
    output_path = Path(__file__).parent / "validation_results.json"
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump({
            "skill": SKILL_NAME,
            "category": SKILL_CATEGORY,
            "mitre_techniques": MITRE_TECHNIQUES,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "total": total,
            "results": results,
        }, output_file, indent=2)
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
