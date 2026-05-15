#!/usr/bin/env python3
"""
bb-huge CLI helper script.
Used by the Gemini CLI skill to interact with bb-huge portal.

Usage:
    python bb.py stats
    python bb.py list [--severity critical] [--status confirmed] [--q "xss"]
    python bb.py get <id>
    python bb.py create --title "..." --target "..." --severity high
    python bb.py status <id> <new_status>
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import argparse

BASE_URL = os.environ.get("BB_HUGE_URL", "http://127.0.0.1:5000")
DEV_KEY = os.environ.get("DEV_KEY", "bb-huge-dev-key-change-me")
HEADERS = {"Content-Type": "application/json", "X-Dev-Key": DEV_KEY}


def req(method, path, body=None):
    url = f"{BASE_URL}/api/v1{path}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read())


def pretty(data):
    print(json.dumps(data, indent=2, default=str))


def cmd_stats(_):
    pretty(req("GET", "/stats"))


def cmd_list(args):
    params = {}
    if args.q:
        params["q"] = args.q
    if args.severity:
        params["severity"] = args.severity
    if args.status:
        params["status"] = args.status
    if args.agent:
        params["agent"] = args.agent
    qs = urllib.parse.urlencode(params)
    pretty(req("GET", f"/findings{'?' + qs if qs else ''}"))


def cmd_get(args):
    pretty(req("GET", f"/findings/{args.id}"))


def cmd_create(args):
    body = {k: v for k, v in vars(args).items() if v and k != "cmd"}
    pretty(req("POST", "/findings", body))


def cmd_status(args):
    pretty(req("PATCH", f"/findings/{args.id}/status", {"status": args.status}))


def main():
    p = argparse.ArgumentParser(description="bb-huge CLI helper")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("stats")

    pl = sub.add_parser("list")
    pl.add_argument("--q")
    pl.add_argument("--severity")
    pl.add_argument("--status")
    pl.add_argument("--agent")

    pg = sub.add_parser("get")
    pg.add_argument("id", type=int)

    pc = sub.add_parser("create")
    pc.add_argument("--title", required=True)
    pc.add_argument("--target", required=True)
    pc.add_argument("--severity", default="medium")
    pc.add_argument("--status", default="discovered")
    pc.add_argument("--agent", default="gemini-cli")
    pc.add_argument("--platform", default="private")
    pc.add_argument("--program_id", type=int, default=None)
    pc.add_argument("--cwe")
    pc.add_argument("--cvss", type=float)
    pc.add_argument("--description", default="")
    pc.add_argument("--poc", default="")

    ps = sub.add_parser("status")
    ps.add_argument("id", type=int)
    ps.add_argument("status")

    args = p.parse_args()
    dispatch = {
        "stats": cmd_stats,
        "list": cmd_list,
        "get": cmd_get,
        "create": cmd_create,
        "status": cmd_status,
    }
    fn = dispatch.get(args.cmd)
    if fn:
        fn(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
