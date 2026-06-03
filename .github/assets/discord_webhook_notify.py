#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys

try:
    import requests
except ImportError:
    sys.exit("The 'requests' package is required. Install dependencies from .github/assets/requirements.txt")

MAX_TITLE = 256
MAX_DESCRIPTION = 4096
MAX_FIELD = 1024
COMMIT_HASH_LENGTH = 7


def normalize_text(value):
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\x00", "", text)
    return text


def truncate(text, limit):
    if limit is None:
        return text
    return text[:limit]


def load_event(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def send_webhook(url, payload):
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Webhook request failed with status {response.status_code}: {response.text.strip()}"
        )


def build_issue_payload(event, title_prefix, footer_text, color):
    issue = event.get("issue", {})
    title_text = truncate(normalize_text(issue.get("title")), MAX_TITLE)
    body_text = truncate(normalize_text(issue.get("body")), MAX_DESCRIPTION)
    action = normalize_text(event.get("action", "unknown"))
    url = normalize_text(issue.get("html_url"))
    user = normalize_text(issue.get("user", {}).get("login"))
    number = issue.get("number")

    return {
        "embeds": [
            {
                "title": f"{title_prefix} [#{number}] {title_text}",
                "description": body_text,
                "url": url,
                "color": color,
                "fields": [
                    {"name": "Status", "value": action, "inline": True},
                    {"name": "Opened by", "value": user, "inline": True},
                ],
                "footer": {"text": footer_text},
            }
        ]
    }


def build_release_payload(event):
    release = event.get("release", {})
    tag = normalize_text(release.get("tag_name"))
    name = truncate(normalize_text(release.get("name")) or tag, MAX_TITLE)
    body_text = truncate(normalize_text(release.get("body")), MAX_DESCRIPTION)
    url = normalize_text(release.get("html_url"))
    author = normalize_text(release.get("author", {}).get("login"))
    prerelease = release.get("prerelease", False)

    label = "Pre-release" if prerelease else "Release"
    color = 16776960 if prerelease else 1752220

    return {
        "content": f"@everyone 🚀 **bb-huge {tag}** is out!",
        "embeds": [
            {
                "title": f"🚀 {name} ({tag})",
                "description": body_text,
                "url": url,
                "color": color,
                "fields": [
                    {"name": "Type", "value": label, "inline": True},
                    {"name": "Released by", "value": author, "inline": True},
                ],
                "footer": {"text": "bb-huge / releases"},
            }
        ],
    }


def build_commit_payload(commit):
    message = normalize_text(commit.get("message", ""))
    lines = message.split("\n")
    subject = truncate(lines[0] if lines else "No commit message", MAX_TITLE)
    body = normalize_text("\n".join(lines[1:])).strip()
    if not body:
        body = "No additional details provided."
    url = normalize_text(commit.get("url"))
    author = normalize_text(
        commit.get("author", {}).get("username")
        or commit.get("author", {}).get("name")
        or commit.get("author", {}).get("email")
        or "unknown"
    )
    sha = normalize_text(commit.get("id", ""))[:COMMIT_HASH_LENGTH]

    return {
        "embeds": [
            {
                "title": f"🔨 Commit: {subject}",
                "description": truncate(body, MAX_DESCRIPTION),
                "url": url,
                "color": 3447003,
                "fields": [
                    {"name": "Author", "value": author, "inline": True},
                    {"name": "Hash", "value": f"`{sha}`", "inline": True},
                ],
                "footer": {"text": "bb-huge / source-code"},
            }
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Send GitHub event notifications to Discord via webhook.")
    parser.add_argument("--event-path", required=True, help="Path to the GitHub event JSON file.")
    parser.add_argument("--event-type", required=True, choices=["bug", "feature", "release", "commits"], help="Type of notification to send.")
    parser.add_argument("--webhook", default=os.environ.get("DISCORD_WEBHOOK"), help="Discord webhook URL.")
    args = parser.parse_args()

    if not args.webhook:
        parser.error("Discord webhook URL is required via --webhook or DISCORD_WEBHOOK environment variable.")

    event = load_event(args.event_path)

    if args.event_type == "bug":
        payload = build_issue_payload(event, "🐛", "bb-huge / bug-report", 15158332)
        send_webhook(args.webhook, payload)
        return

    if args.event_type == "feature":
        payload = build_issue_payload(event, "💡", "bb-huge / feature-request", 7419530)
        send_webhook(args.webhook, payload)
        return

    if args.event_type == "release":
        payload = build_release_payload(event)
        send_webhook(args.webhook, payload)
        return

    if args.event_type == "commits":
        commits = event.get("commits", [])
        for commit in commits:
            payload = build_commit_payload(commit)
            send_webhook(args.webhook, payload)
        return

    raise ValueError(f"Unsupported event type: {args.event_type}")


if __name__ == "__main__":
    main()
