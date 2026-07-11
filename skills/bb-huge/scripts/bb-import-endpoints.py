"""
Bulk-import a plain-text URL list (katana/gau/waybackurls-style output, one
full URL per line) into bb-huge as Endpoints.

Parses host + path from each URL and posts to the endpoints/batch endpoint,
which auto-creates the parent Asset (by hostname) if it isn't already
tracked. Chunked to CHUNK_SIZE rows per request.

Usage:
    python bb-import-endpoints.py urls.txt --program-id 3 --discovered-by katana

Env vars (same convention as bb-dump-attachments.py):
    BB_HUGE_URL   default http://127.0.0.1:5000
    DEV_KEY       required
"""

import argparse
import os
from urllib.parse import urlparse

import requests

BASE_URL = os.environ.get("BB_HUGE_URL", "http://127.0.0.1:5000")
DEV_KEY = os.environ.get("DEV_KEY", "bb-huge-dev-key-change-me")
HEADERS = {"X-Dev-Key": DEV_KEY, "Content-Type": "application/json"}
CHUNK_SIZE = 500


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _parse_url(url):
    parsed = urlparse(url)
    if not parsed.netloc or not parsed.scheme:
        return None
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return {
        "identifier": parsed.hostname,
        "path": path,
        "protocol": parsed.scheme if parsed.scheme in ("http", "https") else "https",
    }


def import_endpoints(path, program_id, discovered_by, default_asset_kind):
    urls = _read_lines(path)
    if not urls:
        print("[!] No URLs found in file.")
        return
    print(f"[*] {len(urls)} URLs read from {path}")

    parsed = [p for p in (_parse_url(u) for u in urls) if p]
    skipped_unparseable = len(urls) - len(parsed)
    if skipped_unparseable:
        print(f"[!] {skipped_unparseable} lines could not be parsed as URLs, skipped.")

    for p in parsed:
        p["discovered_by"] = discovered_by

    total_created = total_skipped = total_errors = 0
    for chunk in _chunks(parsed, CHUNK_SIZE):
        r = requests.post(
            f"{BASE_URL}/api/v1/programs/{program_id}/endpoints/batch",
            headers=HEADERS,
            json={"endpoints": chunk, "default_asset_kind": default_asset_kind},
            timeout=30,
        )
        if r.status_code in (201, 400):
            body = r.json()
            total_created += body.get("total_created", 0)
            total_skipped += body.get("total_skipped_duplicates", 0)
            total_errors += body.get("total_errors", 0)
        else:
            print(f"[!] endpoints/batch chunk failed (status {r.status_code}): {r.text}")

    print(f"[+] Endpoints: {total_created} created, {total_skipped} already existed"
          + (f", {total_errors} errors" if total_errors else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls_file", help="Path to a plain-text file, one full URL per line")
    parser.add_argument("--program-id", type=int, required=True)
    parser.add_argument("--discovered-by", default="manual", help="Tool provenance, e.g. katana, gau, waybackurls")
    parser.add_argument("--default-asset-kind", default="subdomain",
                         choices=["domain", "subdomain", "api_host", "mobile_app", "binary", "source_repo", "repo", "other"],
                         help="Kind to use for any auto-created Asset (default: subdomain)")
    args = parser.parse_args()

    import_endpoints(args.urls_file, args.program_id, args.discovered_by, args.default_asset_kind)
