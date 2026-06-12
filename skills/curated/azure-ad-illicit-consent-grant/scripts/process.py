#!/usr/bin/env python3
"""
CI/CD Execution Harness for azure-ad-illicit-consent-grant
Validates skill documentation quality, technique accuracy, and completeness.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

SKILL_NAME = "azure-ad-illicit-consent-grant"
SKILL_CATEGORY = "penetration-testing/cloud-security"
MITRE_TECHNIQUES = ['T1528']
MITRE_TACTICS = ['TA0001', 'TA0005', 'TA0009']


def validate_skill_structure() -> Dict:
    """Validate SKILL.md has all required sections with substantive content."""
    result = {"test": "skill_structure", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    if not skill_md.exists():
        result["details"] = "SKILL.md not found"
        return result
    
    content = skill_md.read_text(encoding="utf-8")
    
    required_sections = [
        "## When to Use",
        "## Workflow",
        "### Phase 1:",
        "## Key Concepts",
        "## References",
    ]
    
    recommended_sections = [
        "## Prerequisites",
        "Blue Team",
        "## Output Format",
        "Decision Point",
    ]
    
    missing_required = [s for s in required_sections if s not in content]
    missing_recommended = [s for s in recommended_sections if s not in content]
    
    if missing_required:
        result["details"] = f"Missing required sections: {', '.join(missing_required)}"
        return result
    
    # Check for empty tables or placeholder content
    placeholder_patterns = ["| AMSI | |", "| Fileless Malware | |", "# Placeholder", 
                           "TODO:", "# Concept: 1."]
    found_placeholders = [p for p in placeholder_patterns if p in content]
    
    if found_placeholders:
        result["details"] = f"Contains placeholder content: {found_placeholders}"
        return result
    
    # Check minimum content length (quality gate)
    if len(content) < 2000:
        result["details"] = f"Content too thin: {len(content)} chars (minimum 2000)"
        return result
    
    warnings = []
    if missing_recommended:
        warnings.append(f"Missing recommended: {', '.join(missing_recommended)}")
    
    result["passed"] = True
    result["details"] = f"All {len(required_sections)} required sections present" + (f" (warnings: {'; '.join(warnings)})" if warnings else "")
    return result


def validate_frontmatter() -> Dict:
    """Validate YAML frontmatter has required metadata fields."""
    result = {"test": "frontmatter", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    # Extract frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        result["details"] = "No YAML frontmatter found"
        return result
    
    frontmatter = fm_match.group(1)
    
    required_fields = ["name:", "description:", "domain:", "category:", 
                       "difficulty:", "platforms:", "tags:", "tools:"]
    
    missing = [f for f in required_fields if f not in frontmatter]
    
    if missing:
        result["details"] = f"Missing frontmatter fields: {', '.join(missing)}"
    else:
        # Verify description is not empty
        desc_match = re.search(r'description:\s*>?\s*\n?\s*(.+)', frontmatter)
        if not desc_match or len(desc_match.group(1).strip()) < 20:
            result["details"] = "Description field is empty or too short"
        else:
            result["passed"] = True
            result["details"] = f"All {len(required_fields)} frontmatter fields present"
    
    return result


def validate_mitre_mapping() -> Dict:
    """Validate MITRE ATT&CK technique and tactic mappings."""
    result = {"test": "mitre_mapping", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    missing_techniques = [t for t in MITRE_TECHNIQUES if t and t not in content]
    missing_tactics = [t for t in MITRE_TACTICS if t and t not in content]
    
    if not MITRE_TECHNIQUES and not MITRE_TACTICS:
        result["passed"] = True
        result["details"] = "No MITRE mapping required for this skill type"
        return result
    
    if missing_techniques or missing_tactics:
        issues = []
        if missing_techniques:
            issues.append(f"techniques: {missing_techniques}")
        if missing_tactics:
            issues.append(f"tactics: {missing_tactics}")
        result["details"] = f"Missing MITRE references — {', '.join(issues)}"
    else:
        result["passed"] = True
        result["details"] = f"All MITRE mappings verified"
    
    return result


def validate_code_blocks() -> Dict:
    """Validate that code blocks contain real content, not placeholders."""
    result = {"test": "code_quality", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
    
    if not code_blocks:
        result["details"] = "No code blocks found in skill"
        return result
    
    empty_count = 0
    for block in code_blocks:
        executable_lines = [ln.strip() for ln in block.strip().split('\n') 
                          if ln.strip() and not ln.strip().startswith('#') 
                          and not ln.strip().startswith('//')]
        if len(executable_lines) < 1:
            empty_count += 1
    
    if empty_count > len(code_blocks) // 2:
        result["details"] = f"{empty_count}/{len(code_blocks)} code blocks are mostly comments/empty"
    else:
        result["passed"] = True
        result["details"] = f"{len(code_blocks)} code blocks with substantive content"
    
    return result


def validate_references() -> Dict:
    """Validate reference links exist."""
    result = {"test": "references", "passed": False, "details": ""}
    
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    
    urls = re.findall(r'https?://[^\s\)>]+', content)
    
    if len(urls) < 1:
        result["details"] = "No reference URLs found"
    else:
        result["passed"] = True
        result["details"] = f"{len(urls)} reference URLs included"
    
    return result


def main() -> None:
    print(f"[*] Running validation harness for: {SKILL_NAME}")
    print(f"[*] Category: {SKILL_CATEGORY}")
    print(f"[*] Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    tests = [
        validate_skill_structure,
        validate_frontmatter,
        validate_mitre_mapping,
        validate_code_blocks,
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
