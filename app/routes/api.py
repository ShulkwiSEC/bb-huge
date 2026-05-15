import json
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models import Finding, Attachment, SEVERITIES, STATUSES, AGENTS
from ..utils import allowed_file

api_bp = Blueprint("api", __name__)


def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-Dev-Key") or request.args.get("dev_key") or ""
        if key != current_app.config["DEV_KEY"]:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


def _parse_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ── Stats ─────────────────────────────────────────────────────────────────────


@api_bp.get("/stats")
@api_key_required
def get_stats():
    sev = {s: Finding.query.filter_by(severity=s).count() for s in SEVERITIES}
    sta = {s: Finding.query.filter_by(status=s).count() for s in STATUSES}
    agt = {a: Finding.query.filter_by(agent=a).count() for a in AGENTS}
    return jsonify(
        {
            "total": Finding.query.count(),
            "by_severity": sev,
            "by_status": sta,
            "by_agent": agt,
        }
    )


# ── List / Search ─────────────────────────────────────────────────────────────


@api_bp.get("/findings")
@api_key_required
def list_findings():
    q = request.args.get("q", "").strip()
    severity = request.args.get("severity", "")
    status = request.args.get("status", "")
    agent = request.args.get("agent", "")
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))

    query = Finding.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Finding.title.ilike(like),
                Finding.target.ilike(like),
                Finding.description.ilike(like),
            )
        )
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    if agent:
        query = query.filter_by(agent=agent)

    total = query.count()
    findings = (
        query.order_by(Finding.created_at.desc()).offset(offset).limit(limit).all()
    )

    return jsonify(
        {
            "total": total,
            "offset": offset,
            "limit": limit,
            "findings": [f.to_dict() for f in findings],
        }
    )


# ── Get one ───────────────────────────────────────────────────────────────────


@api_bp.get("/findings/<int:fid>")
@api_key_required
def get_finding(fid):
    f = Finding.query.get_or_404(fid)
    return jsonify(f.to_dict())


# ── Create ────────────────────────────────────────────────────────────────────


@api_bp.post("/findings")
@api_key_required
def create_finding():
    data = request.get_json(force=True) or {}

    if not data.get("title") or not data.get("target"):
        return jsonify({"error": "title and target are required"}), 400

    severity = data.get("severity", "medium")
    if severity not in SEVERITIES:
        return jsonify({"error": f"severity must be one of {SEVERITIES}"}), 400

    status = data.get("status", "discovered")
    if status not in STATUSES:
        return jsonify({"error": f"status must be one of {STATUSES}"}), 400

    f = Finding(
        title=data["title"].strip(),
        target=data["target"].strip(),
        platform=data.get("platform", "private"),
        severity=severity,
        status=status,
        agent=data.get("agent", "manual"),
        cwe=data.get("cwe") or None,
        cvss=_parse_float(data.get("cvss")),
        description=data.get("description", ""),
        poc=data.get("poc", ""),
        program_id=data.get("program_id") or None,
    )
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201


# ── Update ────────────────────────────────────────────────────────────────────


@api_bp.patch("/findings/<int:fid>")
@api_key_required
def update_finding(fid):
    f = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}

    for field in [
        "title",
        "target",
        "platform",
        "agent",
        "cwe",
        "description",
        "poc",
        "program_id",
    ]:
        if field in data:
            setattr(f, field, data[field])

    if "severity" in data:
        if data["severity"] not in SEVERITIES:
            return jsonify({"error": f"severity must be one of {SEVERITIES}"}), 400
        f.severity = data["severity"]

    if "status" in data:
        if data["status"] not in STATUSES:
            return jsonify({"error": f"status must be one of {STATUSES}"}), 400
        f.status = data["status"]

    if "cvss" in data:
        f.cvss = _parse_float(data["cvss"])

    f.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(f.to_dict())


# ── Update status only ────────────────────────────────────────────────────────


@api_bp.patch("/findings/<int:fid>/status")
@api_key_required
def update_status(fid):
    f = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}
    new = data.get("status")
    if new not in STATUSES:
        return jsonify({"error": f"status must be one of {STATUSES}"}), 400
    f.status = new
    f.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"id": f.id, "status": f.status})


# ── Delete ────────────────────────────────────────────────────────────────────


@api_bp.delete("/findings/<int:fid>")
@api_key_required
def delete_finding(fid):
    f = Finding.query.get_or_404(fid)
    db.session.delete(f)
    db.session.commit()
    return jsonify({"deleted": fid})


# ── Attachments ───────────────────────────────────────────────────────────────


@api_bp.post("/findings/<int:fid>/attachments")
@api_key_required
def upload_attachment(fid):
    f = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}

    filename = data.get("filename")
    content_b64 = data.get("content")

    if not filename or not content_b64:
        return jsonify({"error": "filename and content (base64) are required"}), 400

    if allowed_file(filename):
        import base64
        import uuid
        import os
        from werkzeug.utils import secure_filename

        try:
            content = base64.b64decode(content_b64)
        except:
            return jsonify({"error": "Invalid base64 content"}), 400

        original = secure_filename(filename)
        ext = original.rsplit(".", 1)[1].lower()
        stored = f"{uuid.uuid4().hex}.{ext}"
        dest = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)

        with open(dest, "wb") as f_out:
            f_out.write(content)

        att = Attachment(
            finding_id=fid,
            filename=stored,
            original_name=original,
            path=dest,
        )
        db.session.add(att)
        db.session.commit()
        return jsonify(att.to_dict()), 201

    return jsonify({"error": "File type not allowed"}), 400


# ── Enums ─────────────────────────────────────────────────────────────────────


@api_bp.get("/enums")
@api_key_required
def get_enums():
    from ..models import PLATFORMS, RECON_CATEGORIES, WEBHOOK_EVENTS

    return jsonify(
        {
            "severities": SEVERITIES,
            "statuses": STATUSES,
            "agents": AGENTS,
            "platforms": PLATFORMS,
            "recon_categories": RECON_CATEGORIES,
            "webhook_events": WEBHOOK_EVENTS,
        }
    )


# ── Programs ──────────────────────────────────────────────────────────────────


@api_bp.get("/programs")
@api_key_required
def list_programs():
    from ..models import Program

    programs = Program.query.order_by(Program.active.desc(), Program.name).all()
    return jsonify([p.to_dict() for p in programs])


@api_bp.get("/programs/<int:pid>")
@api_key_required
def get_program(pid):
    from ..models import Program

    p = Program.query.get_or_404(pid)
    return jsonify(p.to_dict())


@api_bp.post("/programs")
@api_key_required
def create_program():
    from ..models import Program

    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    p = Program(
        name=data["name"].strip(),
        platform=data.get("platform", "private"),
        program_url=data.get("program_url"),
        scope_in=data.get("scope_in", ""),
        scope_out=data.get("scope_out", ""),
        notes=data.get("notes", ""),
        active=data.get("active", True),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@api_bp.patch("/programs/<int:pid>")
@api_key_required
def update_program(pid):
    from ..models import Program
    from datetime import datetime, timezone

    p = Program.query.get_or_404(pid)
    data = request.get_json(force=True) or {}
    for field in ["name", "platform", "program_url", "scope_in", "scope_out", "notes"]:
        if field in data:
            setattr(p, field, data[field])
    if "active" in data:
        p.active = bool(data["active"])
    p.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(p.to_dict())


# ── Target Context (pre-hunt Q&A) ────────────────────────────────────────────


@api_bp.get("/programs/<int:pid>/context")
@api_key_required
def get_target_context(pid):
    from ..models import TargetContext

    ctx = TargetContext.query.filter_by(program_id=pid).first()
    if not ctx:
        return jsonify({"program_id": pid, "data": {}})
    return jsonify(ctx.to_dict())


@api_bp.put("/programs/<int:pid>/context")
@api_key_required
def save_target_context(pid):
    from ..models import TargetContext, Program

    Program.query.get_or_404(pid)
    data = request.get_json(force=True) or {}
    payload = data.get("data", data)

    ctx = TargetContext.query.filter_by(program_id=pid).first()
    if ctx:
        ctx.data = payload
    else:
        ctx = TargetContext(program_id=pid, _data=json.dumps(payload))
        db.session.add(ctx)
    db.session.commit()
    return jsonify(ctx.to_dict()), 201


# ── Recon ─────────────────────────────────────────────────────────────────────


@api_bp.get("/programs/<int:pid>/recon")
@api_key_required
def list_recon(pid):
    from ..models import ReconEntry

    category = request.args.get("category", "")
    query = ReconEntry.query.filter_by(program_id=pid)
    if category:
        query = query.filter_by(category=category)
    entries = query.order_by(ReconEntry.category, ReconEntry.created_at.desc()).all()
    return jsonify([e.to_dict() for e in entries])


@api_bp.post("/programs/<int:pid>/recon")
@api_key_required
def add_recon(pid):
    from ..models import ReconEntry, Program

    Program.query.get_or_404(pid)
    data = request.get_json(force=True) or {}
    if not data.get("value"):
        return jsonify({"error": "value is required"}), 400
    r = ReconEntry(
        program_id=pid,
        category=data.get("category", "subdomain"),
        value=data["value"].strip(),
        notes=data.get("notes", ""),
        source=data.get("source", ""),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@api_bp.delete("/recon/<int:rid>")
@api_key_required
def delete_recon(rid):
    from ..models import ReconEntry

    r = ReconEntry.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"deleted": rid})


# ── Notes ─────────────────────────────────────────────────────────────────────


@api_bp.post("/findings/<int:fid>/notes")
@api_key_required
def add_note(fid):
    from ..models import Note

    data = request.get_json(force=True) or {}
    if not data.get("content"):
        return jsonify({"error": "content is required"}), 400
    n = Note(
        finding_id=fid,
        content=data["content"],
        agent=data.get("agent", "manual"),
    )
    db.session.add(n)
    db.session.commit()
    return jsonify(n.to_dict()), 201


@api_bp.delete("/notes/<int:nid>")
@api_key_required
def delete_note(nid):
    from ..models import Note

    n = Note.query.get_or_404(nid)
    db.session.delete(n)
    db.session.commit()
    return jsonify({"deleted": nid})


# ── Search similar ────────────────────────────────────────────────────────────


@api_bp.get("/findings/similar")
@api_key_required
def search_similar():
    target = request.args.get("target", "").strip()
    cwe = request.args.get("cwe", "").strip()
    title = request.args.get("title", "").strip()

    if not (target or cwe or title):
        return jsonify({"error": "provide target, cwe, or title"}), 400

    query = Finding.query
    conditions = []
    if target:
        conditions.append(Finding.target.ilike(f"%{target}%"))
    if cwe:
        conditions.append(Finding.cwe.ilike(f"%{cwe}%"))
    if title:
        conditions.append(Finding.title.ilike(f"%{title}%"))
    query = query.filter(db.or_(*conditions))
    results = query.order_by(Finding.created_at.desc()).limit(10).all()

    return jsonify(
        {
            "count": len(results),
            "findings": [f.to_dict() for f in results],
        }
    )


# ── Bulk status update ────────────────────────────────────────────────────────


@api_bp.patch("/findings/bulk/status")
@api_key_required
def bulk_update_status():
    from datetime import datetime, timezone

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    status = data.get("status")
    if not ids or not status:
        return jsonify({"error": "ids (list) and status are required"}), 400
    if status not in STATUSES:
        return jsonify({"error": f"status must be one of {STATUSES}"}), 400
    updated = []
    for fid in ids:
        f = Finding.query.get(fid)
        if f:
            f.status = status
            f.updated_at = datetime.now(timezone.utc)
            updated.append(fid)
    db.session.commit()
    return jsonify({"updated": updated, "status": status})


# ── Notify ────────────────────────────────────────────────────────────────────


@api_bp.post("/notify")
@api_key_required
def notify():
    from ..utils import notify_event

    data = request.get_json(force=True) or {}
    event = data.get("event", "finding.created")
    payload = data.get("payload", {})
    if not payload:
        return jsonify({"error": "payload is required"}), 400
    notify_event(event, payload)
    return jsonify({"sent": True, "event": event})
