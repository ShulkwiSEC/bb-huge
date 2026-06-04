#!/usr/bin/env python3
"""
bb-huge PR Leaderboard
- PR opened  → +1 point
- PR merged  → +1 point (total 2 for full cycle)
Stores state in .github/assets/pr-leaderboard.json
Sends leaderboard embed to Discord on every event
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
    return {}


def save_leaderboard(data):
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_event(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_progress_bar(score, max_score):
    if max_score == 0:
        filled = 0
    else:
        filled = round((score / max_score) * BAR_LENGTH)
    return BAR_FILLED * filled + BAR_EMPTY * (BAR_LENGTH - filled)


def build_leaderboard_embed(scores, event_action, contributor, pr_title, pr_url):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_score = sorted_scores[0][1] if sorted_scores else 1

    rows = []
    for i, (user, pts) in enumerate(sorted_scores[:10]):
        medal = MEDALS[i] if i < 3 else f"`#{i+1}`"
        bar = build_progress_bar(pts, max_score)
        rows.append(f"{medal} **{user}**\n`{bar}` {pts} pts")

    board_text = "\n".join(rows) if rows else "No contributions yet."

    if event_action == "opened":
        action_line = f"📬 **{contributor}** opened a PR — +1 pt"
        color = 3447003  # blue
    else:
        action_line = f"🎉 **{contributor}** got a PR merged — +1 pt"
        color = 5763719  # green

    return {
        "embeds": [
            {
                "title": "🏆 bb-huge PR Warriors",
                "description": f"{action_line}\n> [{pr_title}]({pr_url})\n\n{board_text}",
                "color": color,
                "footer": {"text": "bb-huge / pr-warriors"},
            }
        ]
    }


def send_webhook(url, payload):
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
    if not r.ok:
        raise RuntimeError(f"Webhook failed {r.status_code}: {r.text.strip()}")


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

    scores = load_leaderboard()
    scores[contributor] = scores.get(contributor, 0) + 1
    save_leaderboard(scores)

    payload = build_leaderboard_embed(scores, args.event_action, contributor, pr_title, pr_url)
    send_webhook(args.webhook, payload)
    print(f"✅ Leaderboard updated — {contributor} now has {scores[contributor]} pts")


if __name__ == "__main__":
    main()