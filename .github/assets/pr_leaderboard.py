#!/usr/bin/env python3
"""
bb-huge PR Leaderboard
- PR opened  → +1 point
- PR merged  → +1 point (total 2 for full cycle)
- Edits the same Discord message every time (PATCH via webhook)
- Stores state + message_id in .github/assets/pr-leaderboard.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests is required. pip install requests")

LEADERBOARD_PATH = Path(".github/assets/pr-leaderboard.json")
MEDALS = ["🥇", "🥈", "🥉"]
BAR_FILLED = "█"
BAR_EMPTY = "░"
BAR_LENGTH = 10


def load_leaderboard():
    if LEADERBOARD_PATH.exists():
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None, "scores": {}}


def save_leaderboard(data):
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_event(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_progress_bar(score, max_score):
    filled = round((score / max_score) * BAR_LENGTH) if max_score else 0
    return BAR_FILLED * filled + BAR_EMPTY * (BAR_LENGTH - filled)


def build_content(scores, event_action, contributor, pr_title, pr_url):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_score = sorted_scores[0][1] if sorted_scores else 1

    rows = []
    for i, (user, pts) in enumerate(sorted_scores[:10]):
        medal = MEDALS[i] if i < 3 else f"`#{i+1}`"
        bar = build_progress_bar(pts, max_score)
        rows.append(f"{medal} **{user}**\n`{bar}` {pts} pts")

    board_text = "\n".join(rows) if rows else "*No contributions yet.*"

    if event_action == "opened":
        action_line = f"📬 **{contributor}** opened a PR — +1 pt"
    else:
        action_line = f"🎉 **{contributor}** got a PR merged — +1 pt"

    pr_link = f"[{pr_title}]({pr_url})"

    return f"🏆 **bb-huge PR Warriors**\n\n{action_line}\n> {pr_link}\n\n{board_text}"


def parse_webhook_id_token(webhook_url):
    # https://discord.com/api/webhooks/{id}/{token}
    parts = webhook_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def send_or_edit(webhook_url, content, message_id=None):
    webhook_id, webhook_token = parse_webhook_id_token(webhook_url)

    if message_id:
        # PATCH — edit existing message
        url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}"
        r = requests.patch(url, json={"content": content}, timeout=30)
        if not r.ok:
            raise RuntimeError(f"PATCH failed {r.status_code}: {r.text.strip()}")
        return message_id
    else:
        # POST — first time, capture message_id
        url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}?wait=true"
        r = requests.post(url, json={"content": content}, timeout=30)
        if not r.ok:
            raise RuntimeError(f"POST failed {r.status_code}: {r.text.strip()}")
        return str(r.json()["id"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--event-action", required=True, choices=["opened", "merged"])
    parser.add_argument("--webhook", default=os.environ.get("DISCORD_PR_LEADERBOARD_WEBHOOK"))
    args = parser.parse_args()

    if not args.webhook:
        sys.exit("DISCORD_PR_LEADERBOARD_WEBHOOK is required.")

    event = load_event(args.event_path)
    pr = event.get("pull_request", {})
    contributor = pr.get("user", {}).get("login", "unknown")
    pr_title = pr.get("title", "No title")
    pr_url = pr.get("html_url", "")

    data = load_leaderboard()
    data["scores"][contributor] = data["scores"].get(contributor, 0) + 1

    content = build_content(data["scores"], args.event_action, contributor, pr_title, pr_url)
    message_id = send_or_edit(args.webhook, content, data.get("message_id"))

    data["message_id"] = message_id
    save_leaderboard(data)

    print(f"✅ Leaderboard updated — {contributor} now has {data['scores'][contributor]} pts")


if __name__ == "__main__":
    main()