from flask import current_app
import json
import urllib.request
import urllib.error


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# ── Webhook helpers ───────────────────────────────────────────────────────────

def send_webhook(webhook, event: str, payload: dict) -> tuple[bool, str]:
    """
    Send a notification to a single WebhookConfig.
    Returns (success: bool, message: str).
    """
    try:
        if webhook.wtype == "discord":
            return _send_discord(webhook.url_or_token, event, payload)
        elif webhook.wtype == "telegram":
            return _send_telegram(webhook.url_or_token, webhook.chat_id, event, payload)
        else:
            return False, f"Unknown webhook type: {webhook.wtype}"
    except Exception as e:
        return False, str(e)


def notify_event(event: str, payload: dict):
    """
    Fire all active webhooks that subscribe to this event.
    Called from routes after significant state changes.
    """
    # Import here to avoid circular imports
    from .models import WebhookConfig
    webhooks = WebhookConfig.query.filter_by(active=True).all()
    for w in webhooks:
        if event in w.events or "test" == event:
            send_webhook(w, event, payload)


def _send_discord(webhook_url: str, event: str, payload: dict) -> tuple[bool, str]:
    title   = payload.get("title", event)
    message = payload.get("message", "")
    color   = _event_color(event)

    body = {
        "embeds": [{
            "title":       f"bb-huge · {event}",
            "description": f"**{title}**\n{message}",
            "color":       color,
            "fields":      [
                {"name": k, "value": str(v), "inline": True}
                for k, v in payload.items()
                if k not in ("title", "message") and v
            ],
            "footer": {"text": "bb-huge 🤗"},
        }]
    }
    return _post_json(webhook_url, body)


def _send_telegram(token: str, chat_id: str, event: str, payload: dict) -> tuple[bool, str]:
    if not chat_id:
        return False, "chat_id is required for Telegram"

    title   = payload.get("title", event)
    message = payload.get("message", "")
    lines   = [f"🔔 *bb-huge · {event}*", f"*{title}*"]
    if message:
        lines.append(message)
    for k, v in payload.items():
        if k not in ("title", "message") and v:
            lines.append(f"• *{k}*: {v}")

    body = {
        "chat_id":    chat_id,
        "text":       "\n".join(lines),
        "parse_mode": "Markdown",
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    return _post_json(url, body)


def _post_json(url: str, body: dict) -> tuple[bool, str]:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (compatible; bb-huge/2.0)"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return True, r.read().decode()
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()}"
    except Exception as e:
        return False, str(e)


def _event_color(event: str) -> int:
    colors = {
        "finding.created":       0x7c6aff,
        "finding.confirmed":     0x06d6a0,
        "finding.reported":      0xa78bfa,
        "finding.rewarded":      0x00ffb3,
        "finding.denied":        0xff4d6d,
        "finding.status_changed":0xff9a3c,
        "recon.added":           0x6bbcff,
        "test":                  0x888888,
    }
    return colors.get(event, 0x7c6aff)

