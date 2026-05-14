import os
import uuid
from datetime import datetime, timezone
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, send_from_directory, abort)
from werkzeug.utils import secure_filename
from .. import db
from ..models import Finding, Attachment, SEVERITIES, STATUSES, AGENTS
from .auth import login_required
from ..utils import allowed_file

findings_bp = Blueprint("findings", __name__)


# ── Dashboard ────────────────────────────────────────────────────────────────

@findings_bp.route("/")
@login_required
def dashboard():
    total     = Finding.query.count()
    critical  = Finding.query.filter_by(severity="critical").count()
    high      = Finding.query.filter_by(severity="high").count()
    rewarded  = Finding.query.filter_by(status="rewarded").count()
    confirmed = Finding.query.filter_by(status="confirmed").count()

    # Counts per severity and status for mini-charts
    sev_counts = {s: Finding.query.filter_by(severity=s).count() for s in SEVERITIES}
    sta_counts = {s: Finding.query.filter_by(status=s).count()   for s in STATUSES}

    # Agent breakdown
    agent_counts = {a: Finding.query.filter_by(agent=a).count() for a in AGENTS}

    recent = (Finding.query
              .order_by(Finding.created_at.desc())
              .limit(10).all())

    return render_template(
        "dashboard.html",
        total=total, critical=critical, high=high,
        rewarded=rewarded, confirmed=confirmed,
        sev_counts=sev_counts, sta_counts=sta_counts,
        agent_counts=agent_counts, recent=recent,
    )


# ── List ─────────────────────────────────────────────────────────────────────

@findings_bp.route("/findings")
@login_required
def list_findings():
    q        = request.args.get("q", "").strip()
    severity = request.args.get("severity", "")
    status   = request.args.get("status", "")
    agent    = request.args.get("agent", "")
    platform = request.args.get("platform", "")
    sort     = request.args.get("sort", "newest")

    query = Finding.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Finding.title.ilike(like),
                   Finding.target.ilike(like),
                   Finding.description.ilike(like),
                   Finding.cwe.ilike(like))
        )
    if severity: query = query.filter_by(severity=severity)
    if status:   query = query.filter_by(status=status)
    if agent:    query = query.filter_by(agent=agent)
    if platform: query = query.filter(Finding.platform.ilike(f"%{platform}%"))

    if sort == "newest":
        query = query.order_by(Finding.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Finding.created_at.asc())
    elif sort == "severity":
        order = db.case(
            {s: i for i, s in enumerate(SEVERITIES)},
            value=Finding.severity
        )
        query = query.order_by(order)
    elif sort == "cvss":
        query = query.order_by(Finding.cvss.desc().nullslast())

    findings = query.all()

    # CSV export
    if request.args.get("export") == "csv":
        import csv, io
        from flask import Response
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id","title","target","platform","severity","status",
            "agent","cwe","cvss","created_at"
        ])
        writer.writeheader()
        for f in findings:
            writer.writerow({
                "id": f.id, "title": f.title, "target": f.target,
                "platform": f.platform, "severity": f.severity,
                "status": f.status, "agent": f.agent,
                "cwe": f.cwe or "", "cvss": f.cvss or "",
                "created_at": f.created_at.strftime("%Y-%m-%d") if f.created_at else "",
            })
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=bb-huge-export.csv"}
        )

    platforms = [r[0] for r in db.session.query(Finding.platform).distinct().all()]

    return render_template(
        "findings/list.html",
        findings=findings,
        severities=SEVERITIES, statuses=STATUSES, agents=AGENTS,
        platforms=platforms,
        q=q, severity=severity, status=status,
        agent=agent, platform=platform, sort=sort,
    )


# ── Detail ────────────────────────────────────────────────────────────────────

@findings_bp.route("/findings/<int:fid>")
@login_required
def detail(fid):
    finding = Finding.query.get_or_404(fid)
    return render_template("findings/detail.html",
                           finding=finding, statuses=STATUSES)


# ── Add ───────────────────────────────────────────────────────────────────────

@findings_bp.route("/findings/add", methods=["GET", "POST"])
@login_required
def add_finding():
    if request.method == "POST":
        finding = Finding(
            title       = request.form["title"].strip(),
            target      = request.form["target"].strip(),
            platform    = request.form.get("platform", "private").strip(),
            severity    = request.form["severity"],
            status      = request.form.get("status", "discovered"),
            agent       = request.form.get("agent", "manual"),
            cwe         = request.form.get("cwe", "").strip() or None,
            cvss        = _parse_float(request.form.get("cvss")),
            description = request.form.get("description", ""),
            poc         = request.form.get("poc", ""),
        )
        db.session.add(finding)
        db.session.flush()  # get id before attachments

        _handle_uploads(finding.id)

        db.session.commit()
        flash("Finding added ✓", "success")
        return redirect(url_for("findings.detail", fid=finding.id))

    return render_template("findings/form.html",
                           finding=None,
                           severities=SEVERITIES,
                           statuses=STATUSES,
                           agents=AGENTS)


# ── Edit ──────────────────────────────────────────────────────────────────────

@findings_bp.route("/findings/<int:fid>/edit", methods=["GET", "POST"])
@login_required
def edit_finding(fid):
    finding = Finding.query.get_or_404(fid)

    if request.method == "POST":
        finding.title       = request.form["title"].strip()
        finding.target      = request.form["target"].strip()
        finding.platform    = request.form.get("platform", "private").strip()
        finding.severity    = request.form["severity"]
        finding.status      = request.form.get("status", finding.status)
        finding.agent       = request.form.get("agent", finding.agent)
        finding.cwe         = request.form.get("cwe", "").strip() or None
        finding.cvss        = _parse_float(request.form.get("cvss"))
        finding.description = request.form.get("description", "")
        finding.poc         = request.form.get("poc", "")
        finding.updated_at  = datetime.now(timezone.utc)

        _handle_uploads(finding.id)

        db.session.commit()
        flash("Finding updated ✓", "success")
        return redirect(url_for("findings.detail", fid=finding.id))

    return render_template("findings/form.html",
                           finding=finding,
                           severities=SEVERITIES,
                           statuses=STATUSES,
                           agents=AGENTS)


# ── Quick status update ───────────────────────────────────────────────────────

@findings_bp.route("/findings/<int:fid>/status", methods=["POST"])
@login_required
def update_status(fid):
    finding = Finding.query.get_or_404(fid)
    new_status = request.form.get("status")
    if new_status in STATUSES:
        finding.status = new_status
        finding.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash(f"Status updated to '{new_status}' ✓", "success")
    return redirect(url_for("findings.detail", fid=fid))


# ── Delete ────────────────────────────────────────────────────────────────────

@findings_bp.route("/findings/<int:fid>/delete", methods=["POST"])
@login_required
def delete_finding(fid):
    finding = Finding.query.get_or_404(fid)
    db.session.delete(finding)
    db.session.commit()
    flash("Finding deleted.", "info")
    return redirect(url_for("findings.list_findings"))


# ── Delete attachment ─────────────────────────────────────────────────────────

@findings_bp.route("/attachments/<int:aid>/delete", methods=["POST"])
@login_required
def delete_attachment(aid):
    att = Attachment.query.get_or_404(aid)
    fid = att.finding_id
    try:
        os.remove(att.path)
    except OSError:
        pass
    db.session.delete(att)
    db.session.commit()
    flash("Attachment deleted.", "info")
    return redirect(url_for("findings.detail", fid=fid))


# ── Serve uploads ─────────────────────────────────────────────────────────────

@findings_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _handle_uploads(finding_id):
    files = request.files.getlist("attachments")
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            original = secure_filename(f.filename)
            ext      = original.rsplit(".", 1)[1].lower()
            stored   = f"{uuid.uuid4().hex}.{ext}"
            dest     = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
            f.save(dest)
            att = Attachment(
                finding_id    = finding_id,
                filename      = stored,
                original_name = original,
                path          = dest,
            )
            db.session.add(att)
