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
        key = (request.headers.get("X-Dev-Key") or
               request.args.get("dev_key") or "")
        if key != current_app.config["DEV_KEY"]:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def _parse_float(v):
    try: return float(v)
    except (TypeError, ValueError): return None


# ── Stats ─────────────────────────────────────────────────────────────────────

@api_bp.get("/stats")
@api_key_required
def get_stats():
    sev = {s: Finding.query.filter_by(severity=s).count() for s in SEVERITIES}
    sta = {s: Finding.query.filter_by(status=s).count()   for s in STATUSES}
    agt = {a: Finding.query.filter_by(agent=a).count()    for a in AGENTS}
    return jsonify({
        "total":          Finding.query.count(),
        "by_severity":    sev,
        "by_status":      sta,
        "by_agent":       agt,
    })


# ── List / Search ─────────────────────────────────────────────────────────────

@api_bp.get("/findings")
@api_key_required
def list_findings():
    q        = request.args.get("q", "").strip()
    severity = request.args.get("severity", "")
    status   = request.args.get("status", "")
    agent    = request.args.get("agent", "")
    limit    = min(int(request.args.get("limit", 50)), 200)
    offset   = int(request.args.get("offset", 0))

    query = Finding.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(
            Finding.title.ilike(like),
            Finding.target.ilike(like),
            Finding.description.ilike(like),
        ))
    if severity: query = query.filter_by(severity=severity)
    if status:   query = query.filter_by(status=status)
    if agent:    query = query.filter_by(agent=agent)

    total    = query.count()
    findings = query.order_by(Finding.created_at.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "total":    total,
        "offset":   offset,
        "limit":    limit,
        "findings": [f.to_dict() for f in findings],
    })


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
        title       = data["title"].strip(),
        target      = data["target"].strip(),
        platform    = data.get("platform", "private"),
        severity    = severity,
        status      = status,
        agent       = data.get("agent", "manual"),
        cwe         = data.get("cwe") or None,
        cvss        = _parse_float(data.get("cvss")),
        description = data.get("description", ""),
        poc         = data.get("poc", ""),
    )
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201


# ── Update ────────────────────────────────────────────────────────────────────

@api_bp.patch("/findings/<int:fid>")
@api_key_required
def update_finding(fid):
    f    = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}

    for field in ["title", "target", "platform", "agent", "cwe", "description", "poc"]:
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
    f    = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}
    new  = data.get("status")
    if new not in STATUSES:
        return jsonify({"error": f"status must be one of {STATUSES}"}), 400
    f.status     = new
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
    f    = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}
    
    filename    = data.get("filename")
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
        ext      = original.rsplit(".", 1)[1].lower()
        stored   = f"{uuid.uuid4().hex}.{ext}"
        dest     = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
        
        with open(dest, "wb") as f_out:
            f_out.write(content)
            
        att = Attachment(
            finding_id    = fid,
            filename      = stored,
            original_name = original,
            path          = dest,
        )
        db.session.add(att)
        db.session.commit()
        return jsonify(att.to_dict()), 201
        
    return jsonify({"error": "File type not allowed"}), 400


# ── Enums ─────────────────────────────────────────────────────────────────────

@api_bp.get("/enums")
@api_key_required
def get_enums():
    return jsonify({
        "severities": SEVERITIES,
        "statuses":   STATUSES,
        "agents":     AGENTS,
    })
