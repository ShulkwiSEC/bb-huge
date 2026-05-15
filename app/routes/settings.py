from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify, current_app)
from .. import db
from ..models import WebhookConfig, Note, Finding, WEBHOOK_EVENTS, AGENTS
from .auth import login_required
from ..utils import send_webhook

settings_bp = Blueprint("settings", __name__)


# ── Settings main page ────────────────────────────────────────────────────────

@settings_bp.route("/settings")
@login_required
def index():
    webhooks = WebhookConfig.query.order_by(WebhookConfig.created_at.desc()).all()
    return render_template("settings/index.html",
                           webhooks=webhooks,
                           webhook_events=WEBHOOK_EVENTS)


# ── Webhook: Add ──────────────────────────────────────────────────────────────

@settings_bp.route("/settings/webhooks/add", methods=["POST"])
@login_required
def add_webhook():
    events = request.form.getlist("events")
    w = WebhookConfig(
        name         = request.form["name"].strip(),
        wtype        = request.form["wtype"],
        url_or_token = request.form["url_or_token"].strip(),
        chat_id      = request.form.get("chat_id", "").strip() or None,
        active       = True,
    )
    w.events = events
    db.session.add(w)
    db.session.commit()
    flash("Webhook added ✓", "success")
    return redirect(url_for("settings.index"))


# ── Webhook: Edit ─────────────────────────────────────────────────────────────

@settings_bp.route("/settings/webhooks/<int:wid>/edit", methods=["GET", "POST"])
@login_required
def edit_webhook(wid):
    w = WebhookConfig.query.get_or_404(wid)
    if request.method == "POST":
        w.name         = request.form["name"].strip()
        w.wtype        = request.form["wtype"]
        w.url_or_token = request.form["url_or_token"].strip()
        w.chat_id      = request.form.get("chat_id", "").strip() or None
        w.active       = request.form.get("active") == "on"
        w.events       = request.form.getlist("events")
        db.session.commit()
        flash("Webhook updated ✓", "success")
        return redirect(url_for("settings.index"))
    return render_template("settings/webhook_form.html",
                           webhook=w, webhook_events=WEBHOOK_EVENTS)


# ── Webhook: Toggle active ────────────────────────────────────────────────────

@settings_bp.route("/settings/webhooks/<int:wid>/toggle", methods=["POST"])
@login_required
def toggle_webhook(wid):
    w = WebhookConfig.query.get_or_404(wid)
    w.active = not w.active
    db.session.commit()
    state = "enabled" if w.active else "disabled"
    flash(f"Webhook '{w.name}' {state}.", "info")
    return redirect(url_for("settings.index"))


# ── Webhook: Test ─────────────────────────────────────────────────────────────

@settings_bp.route("/settings/webhooks/<int:wid>/test", methods=["POST"])
@login_required
def test_webhook(wid):
    w = WebhookConfig.query.get_or_404(wid)
    ok, msg = send_webhook(w, event="test", payload={
        "message": "bb-huge test notification 🤗",
        "source":  "settings test button",
    })
    if ok:
        flash(f"Test sent successfully ✓", "success")
    else:
        flash(f"Test failed: {msg}", "error")
    return redirect(url_for("settings.index"))


# ── Webhook: Delete ───────────────────────────────────────────────────────────

@settings_bp.route("/settings/webhooks/<int:wid>/delete", methods=["POST"])
@login_required
def delete_webhook(wid):
    w = WebhookConfig.query.get_or_404(wid)
    db.session.delete(w)
    db.session.commit()
    flash("Webhook deleted.", "info")
    return redirect(url_for("settings.index"))


# ── Notes: Add (per-finding) ──────────────────────────────────────────────────

@settings_bp.route("/findings/<int:fid>/notes/add", methods=["POST"])
@login_required
def add_note(fid):
    Finding.query.get_or_404(fid)
    content = request.form.get("content", "").strip()
    if content:
        n = Note(
            finding_id = fid,
            content    = content,
            agent      = request.form.get("agent", "manual"),
        )
        db.session.add(n)
        db.session.commit()
        flash("Note added ✓", "success")
    return redirect(url_for("findings.detail", fid=fid) + "#notes")


# ── Notes: Delete ─────────────────────────────────────────────────────────────

@settings_bp.route("/notes/<int:nid>/delete", methods=["POST"])
@login_required
def delete_note(nid):
    n = Note.query.get_or_404(nid)
    fid = n.finding_id
    db.session.delete(n)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("findings.detail", fid=fid) + "#notes")
