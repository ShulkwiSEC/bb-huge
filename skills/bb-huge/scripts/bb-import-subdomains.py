"""
Bulk-import a plain-text subdomain list (subfinder/amass/assetfinder-style
output, one hostname per line) into bb-huge.

Writes to both:
  - ReconEntry (category=subdomain) — the raw-discovery log, with provenance
  - Asset (kind=subdomain) — the tracked/testable inventory

Both are batch calls chunked to CHUNK_SIZE rows per request, so tens of
thousands of lines don't produce one oversized HTTP request.

Usage:
    python bb-import-subdomains.py subs.txt --program-id 3 --source subfinder

Env vars (same convention as bb-dump-attachments.py):
    BB_HUGE_URL   default http://127.0.0.1:5000
    DEV_KEY       required
"""

import argparse
import os

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


def import_subdomains(path, program_id, source):
    hosts = _read_lines(path)
    if not hosts:
        print("[!] No hostnames found in file.")
        return
    print(f"[*] {len(hosts)} hostnames read from {path}")

    recon_created = recon_skipped = 0
    for chunk in _chunks(hosts, CHUNK_SIZE):
        entries = [{"category": "subdomain", "value": h, "source": source} for h in chunk]
        r = requests.post(
            f"{BASE_URL}/api/v1/programs/{program_id}/recon/batch",
            headers=HEADERS, json={"entries": entries}, timeout=30,
        )
        if r.status_code in (201, 400):
            body = r.json()
            recon_created += body.get("total_created", 0)
            recon_skipped += body.get("total_skipped_duplicates", 0)
        else:
            print(f"[!] recon/batch chunk failed (status {r.status_code}): {r.text}")

    assets_created = assets_skipped = assets_errors = 0
    for chunk in _chunks(hosts, CHUNK_SIZE):
        assets = [{"kind": "subdomain", "identifier": h, "environment": "unknown"} for h in chunk]
        r = requests.post(
            f"{BASE_URL}/api/v1/programs/{program_id}/assets/batch",
            headers=HEADERS, json={"assets": assets}, timeout=30,
        )
        if r.status_code in (201, 400):
            body = r.json()
            assets_created += body.get("total_created", 0)
            assets_errors += body.get("total_errors", 0)
        else:
            print(f"[!] assets/batch chunk failed (status {r.status_code}): {r.text}")

    print(f"[+] Recon entries: {recon_created} created, {recon_skipped} already existed")
    print(f"[+] Assets: {assets_created} created"
          + (f", {assets_errors} errors" if assets_errors else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subdomains_file", help="Path to a plain-text file, one hostname per line")
    parser.add_argument("--program-id", type=int, required=True)
    parser.add_argument("--source", default="manual", help="Tool provenance, e.g. subfinder, amass (default: manual)")
    args = parser.parse_args()

    import_subdomains(args.subdomains_file, args.program_id, args.source)
