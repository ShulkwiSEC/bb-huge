"""
Import a HAR (HTTP Archive) export into bb-huge.

Two things happen in one pass:
  1. Every non-static request/response pair gets filed as an EvidenceRecord
     (evidence_type=http_exchange) — a real, already-fired endpoint map,
     no curl-and-regex guessing needed.
  2. The freshest authenticated request to the target host has its
     cookies/auth headers extracted and saved as a reusable AuthSession
     (bb_get_session) — so any other agent/subagent can attach real auth
     material to its own requests without ever handling login/MFA/CSRF.

Usage:
    python bb-import-har.py capture.har --program-id 3 --label user_a
    python bb-import-har.py capture.har --program-id 3 --label admin --base-url https://app.example.com

Env vars (same convention as bb-dump-attachments.py):
    BB_HUGE_URL   default http://127.0.0.1:5000
    DEV_KEY       required
"""

import argparse
import json
import os
from collections import Counter
from urllib.parse import urlparse

import requests

BASE_URL = os.environ.get("BB_HUGE_URL", "http://127.0.0.1:5000")
DEV_KEY = os.environ.get("DEV_KEY", "bb-huge-dev-key-change-me")
HEADERS = {"X-Dev-Key": DEV_KEY, "Content-Type": "application/json"}

STATIC_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".css", ".map",
}
STATIC_MIME_PREFIXES = ("image/", "font/", "text/css")

AUTH_HEADER_ALLOWLIST = {
    "authorization", "x-csrf-token", "x-xsrf-token", "csrf-token",
    "x-auth-token", "x-api-key", "x-session-token",
}


def _is_static(entry):
    url = entry.get("request", {}).get("url", "")
    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in STATIC_EXTENSIONS):
        return True
    mime = (entry.get("response", {}).get("content", {}) or {}).get("mimeType", "") or ""
    return mime.lower().startswith(STATIC_MIME_PREFIXES)


def _header_map(header_list):
    return {h["name"]: h["value"] for h in header_list or [] if "name" in h}


def _dominant_host(entries):
    hosts = Counter()
    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        parsed = urlparse(url)
        if parsed.netloc:
            hosts[f"{parsed.scheme}://{parsed.netloc}"] += 1
    if not hosts:
        return None
    return hosts.most_common(1)[0][0]


def _load_entries(har_path):
    with open(har_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("log", {}).get("entries", [])


def _dedupe(entries):
    """Keep the last (freshest) occurrence per (method, path)."""
    by_key = {}
    for entry in entries:
        req = entry.get("request", {})
        method = req.get("method", "GET")
        path = urlparse(req.get("url", "")).path
        by_key[(method, path)] = entry
    return list(by_key.values())


def _file_evidence(program_id, entry, account_label, auth_type, max_body=4000):
    req = entry.get("request", {})
    res = entry.get("response", {})
    method = req.get("method", "GET")
    url = req.get("url", "")

    post_data = (req.get("postData") or {}).get("text")
    content = (res.get("content") or {})
    response_body = content.get("text")
    if response_body and len(response_body) > max_body:
        response_body = response_body[:max_body] + "\n...[truncated]"

    payload = {
        "program_id": program_id,
        "evidence_type": "http_exchange",
        "title": f"{method} {urlparse(url).path or url}",
        "summary": "Imported from HAR capture.",
        "request_method": method,
        "request_url": url,
        "request_headers": _header_map(req.get("headers")),
        "request_body_text": post_data,
        "response_status": res.get("status"),
        "response_headers": _header_map(res.get("headers")),
        "response_body_text": response_body,
        "account_label": account_label,
        "auth_type": auth_type,
        "source_tool": "bb-import-har",
    }
    r = requests.post(f"{BASE_URL}/api/v1/evidence", headers=HEADERS, json=payload, timeout=15)
    return r.status_code == 201


def _extract_session(entries, target_host):
    """Freshest request to target_host carrying cookies or an auth header."""
    candidate = None
    for entry in entries:
        req = entry.get("request", {})
        url = req.get("url", "")
        parsed = urlparse(url)
        if f"{parsed.scheme}://{parsed.netloc}" != target_host:
            continue

        cookies = {c["name"]: c["value"] for c in req.get("cookies", []) if "name" in c}
        headers = _header_map(req.get("headers"))
        auth_headers = {k: v for k, v in headers.items() if k.lower() in AUTH_HEADER_ALLOWLIST}

        if cookies or auth_headers:
            candidate = (cookies, auth_headers)  # later entries overwrite -> freshest wins

    return candidate


def _infer_auth_type(cookies, auth_headers):
    has_bearer = any(
        k.lower() == "authorization" and v.lower().startswith("bearer ")
        for k, v in auth_headers.items()
    )
    if cookies and (auth_headers and not has_bearer):
        return "mixed"
    if has_bearer:
        return "bearer"
    if auth_headers:
        return "custom_header"
    return "cookie"


def import_har(har_path, program_id, label, base_url, account_label, max_evidence):
    entries = _load_entries(har_path)
    if not entries:
        print("[!] No entries found in HAR file.")
        return

    target_host = base_url.rstrip("/") if base_url else _dominant_host(entries)
    if not target_host:
        print("[!] Could not determine target host — pass --base-url explicitly.")
        return
    print(f"[*] Target host: {target_host}")

    non_static = [e for e in entries if not _is_static(e)]
    deduped = _dedupe(non_static)[:max_evidence]

    filed = 0
    for entry in deduped:
        if _file_evidence(program_id, entry, account_label or label, "cookie", max_body=4000):
            filed += 1
    print(f"[*] Filed {filed}/{len(deduped)} request/response pairs as evidence "
          f"(from {len(entries)} total, {len(entries) - len(non_static)} static skipped).")

    session = _extract_session(non_static, target_host)
    if session is None:
        print("[!] No cookies or auth headers found for target host — session not saved. "
              "Make sure you were logged in when the HAR was captured.")
        return

    cookies, auth_headers = session
    auth_type = _infer_auth_type(cookies, auth_headers)
    payload = {
        "label": label,
        "base_url": target_host,
        "auth_type": auth_type,
        "cookies": cookies,
        "headers": auth_headers,
        "captured_by": "bb-import-har",
        "source": "har_import",
        "notes": f"Imported from {os.path.basename(har_path)}",
    }
    r = requests.post(f"{BASE_URL}/api/v1/programs/{program_id}/sessions", headers=HEADERS, json=payload, timeout=15)
    if r.status_code == 201:
        print(f"[+] Session saved: label='{label}' auth_type={auth_type} "
              f"({len(cookies)} cookies, {len(auth_headers)} auth headers)")
    else:
        print(f"[!] Failed to save session (status {r.status_code}): {r.text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("har_file", help="Path to the HAR file (Chrome DevTools: Network tab -> Export HAR)")
    parser.add_argument("--program-id", type=int, required=True)
    parser.add_argument("--label", default="default", help="Identity label, e.g. user_a, admin (default: 'default')")
    parser.add_argument("--base-url", default=None, help="Target origin, e.g. https://app.example.com. Inferred from the HAR if omitted.")
    parser.add_argument("--account-label", default=None, help="account_label to stamp on filed evidence (defaults to --label)")
    parser.add_argument("--max-evidence", type=int, default=200, help="Cap on evidence records filed (default 200)")
    args = parser.parse_args()

    import_har(args.har_file, args.program_id, args.label, args.base_url, args.account_label, args.max_evidence)
