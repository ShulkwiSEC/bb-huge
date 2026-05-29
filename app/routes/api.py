import json
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, current_app, jsonify, request

from .. import db
from ..models import (
    AGENTS,
    ASSET_ENVIRONMENTS,
    ASSET_KINDS,
    CONFIDENCE_LEVELS,
    ENDPOINT_PROTOCOLS,
    EVIDENCE_TYPES,
    HYPOTHESIS_STATUSES,
    OBSERVATION_CATEGORIES,
    OBSERVATION_STATUSES,
    PLATFORMS,
    RECON_CATEGORIES,
    SEVERITIES,
    STATUSES,
    WEBHOOK_EVENTS,
    Asset,
    Attachment,
    Endpoint,
    EvidenceRecord,
    Finding,
    Hypothesis,
    Note,
    Observation,
    Program,
    ReconEntry,
    TargetContext,
)
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


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _json_text(value):
    if value is None or value == "":
        return None
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except Exception:
            return json.dumps({"raw": value})
    return json.dumps(value)


def _limit_arg(default=50, max_limit=200):
    return min(int(request.args.get("limit", default)), max_limit)


def _validate_choice(value, allowed, field_name):
    if value not in allowed:
        return jsonify({"error": f"{field_name} must be one of {allowed}"}), 400
    return None


def _validate_from_data(data, field, allowed, name=None):
    value = data.get(field) if isinstance(data, dict) else data
    if value is not None and value not in allowed:
        return jsonify({"error": f"{name or field} must be one of {allowed}"}), 400
    return None


def _apply_fields(obj, data, fields):
    for field in fields:
        if field in data:
            setattr(obj, field, data[field])


def _require_fields(data, *fields):
    for field in fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400
    return None


def _check_ownership(item, program_id, label):
    if item.program_id and item.program_id != program_id:
        return jsonify({"error": f"{label} does not belong to this program"}), 400
    return None


def _touch(obj):
    obj.updated_at = datetime.now(timezone.utc)


def _save(obj=None):
    if obj is not None:
        db.session.add(obj)
    db.session.commit()


def _require_program(pid):
    Program.query.get_or_404(pid)


def _finding_summary(finding):
    return {
        "id": finding.id,
        "title": finding.title,
        "target": finding.target,
        "severity": finding.severity,
        "status": finding.status,
        "agent": finding.agent,
        "cwe": finding.cwe,
        "confidence": finding.confidence,
        "created_at": finding.created_at.isoformat() if finding.created_at else None,
        "updated_at": finding.updated_at.isoformat() if finding.updated_at else None,
    }


def _observation_summary(observation):
    return {
        "id": observation.id,
        "title": observation.title,
        "category": observation.category,
        "status": observation.status,
        "agent": observation.agent,
        "confidence": observation.confidence,
        "source_tool": observation.source_tool,
        "created_at": observation.created_at.isoformat()
        if observation.created_at
        else None,
        "updated_at": observation.updated_at.isoformat()
        if observation.updated_at
        else None,
    }


def _hypothesis_summary(hypothesis):
    return {
        "id": hypothesis.id,
        "title": hypothesis.title,
        "weakness_hint": hypothesis.weakness_hint,
        "cwe": hypothesis.cwe,
        "severity_hint": hypothesis.severity_hint,
        "status": hypothesis.status,
        "agent": hypothesis.agent,
        "confidence": hypothesis.confidence,
        "created_at": hypothesis.created_at.isoformat()
        if hypothesis.created_at
        else None,
        "updated_at": hypothesis.updated_at.isoformat()
        if hypothesis.updated_at
        else None,
    }


def _tokenize(value):
    if not value:
        return set()
    tokens = []
    current = []
    for char in value.lower():
        if char.isalnum():
            current.append(char)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return {token for token in tokens if len(token) >= 3}


def _derive_target_from_hypothesis(hypothesis):
    evidence = (
        EvidenceRecord.query.filter_by(hypothesis_id=hypothesis.id)
        .order_by(EvidenceRecord.created_at.desc())
        .first()
    )
    if evidence and evidence.request_url:
        parsed = urlparse(evidence.request_url)
        if parsed.netloc:
            return parsed.netloc
    if hypothesis.observation_id:
        evidence = (
            EvidenceRecord.query.filter_by(observation_id=hypothesis.observation_id)
            .order_by(EvidenceRecord.created_at.desc())
            .first()
        )
        if evidence and evidence.request_url:
            parsed = urlparse(evidence.request_url)
            if parsed.netloc:
                return parsed.netloc
    return hypothesis.program.name


def _build_report_pack(finding):
    linked_hypothesis = finding.hypothesis
    related_evidence = finding.evidence_records
    if linked_hypothesis:
        hypothesis_evidence = [
            evidence.to_dict()
            for evidence in linked_hypothesis.evidence_records
            if evidence.finding_id is None
        ]
    else:
        hypothesis_evidence = []

    unresolved_gaps = []
    if not finding.cwe and not (linked_hypothesis and linked_hypothesis.cwe):
        unresolved_gaps.append("Missing CWE classification")
    if not finding.cvss:
        unresolved_gaps.append("Missing CVSS score")
    if not finding.poc.strip():
        unresolved_gaps.append("PoC / reproduction steps are incomplete")
    if not related_evidence and not hypothesis_evidence:
        unresolved_gaps.append("No structured evidence records attached")

    return {
        "finding": finding.to_dict(),
        "program": finding.program.to_dict() if finding.program else None,
        "linked_hypothesis": linked_hypothesis.to_dict() if linked_hypothesis else None,
        "summary": {
            "title": finding.title,
            "target": finding.target,
            "severity": finding.severity,
            "status": finding.status,
            "confidence": finding.confidence,
            "cwe": finding.cwe or (linked_hypothesis.cwe if linked_hypothesis else None),
            "weakness_hint": linked_hypothesis.weakness_hint if linked_hypothesis else None,
        },
        "report_inputs": {
            "description": finding.description,
            "attack_path": linked_hypothesis.attack_path if linked_hypothesis else "",
            "impact": linked_hypothesis.impact_hypothesis if linked_hypothesis else "",
            "repro_steps": finding.poc,
            "notes": [note.to_dict() for note in finding.notes],
            "attachments": [attachment.to_dict() for attachment in finding.attachments],
        },
        "evidence_summary": {
            "finding_evidence": [evidence.to_dict() for evidence in related_evidence],
            "linked_hypothesis_evidence": hypothesis_evidence,
        },
        "unresolved_gaps": unresolved_gaps,
    }


def _similarity_score(candidate, query):
    score = 0
    reasons = []

    title_tokens = _tokenize(query.get("title"))
    candidate_title_tokens = _tokenize(candidate.get("title"))
    if title_tokens and candidate_title_tokens:
        overlap = len(title_tokens & candidate_title_tokens)
        if overlap:
            score += min(overlap * 12, 36)
            reasons.append(f"title token overlap={overlap}")

    query_cwe = (query.get("cwe") or "").strip().lower()
    candidate_cwe = (candidate.get("cwe") or "").strip().lower()
    if query_cwe and candidate_cwe and query_cwe == candidate_cwe:
        score += 35
        reasons.append("same cwe")

    query_target = (query.get("target") or "").strip().lower()
    candidate_target = (candidate.get("target") or candidate.get("program_name") or "").strip().lower()
    if query_target and candidate_target:
        if query_target == candidate_target:
            score += 30
            reasons.append("same target")
        elif query_target in candidate_target or candidate_target in query_target:
            score += 18
            reasons.append("target partial match")

    query_desc_tokens = _tokenize(query.get("description"))
    candidate_desc_tokens = _tokenize(candidate.get("description") or candidate.get("summary"))
    if query_desc_tokens and candidate_desc_tokens:
        overlap = len(query_desc_tokens & candidate_desc_tokens)
        if overlap:
            score += min(overlap * 5, 20)
            reasons.append(f"description token overlap={overlap}")

    return score, reasons


def _top_duplicate_hotspots(program_id):
    by_cwe = (
        db.session.query(Finding.cwe, db.func.count(Finding.id))
        .filter(Finding.program_id == program_id, Finding.cwe.isnot(None))
        .group_by(Finding.cwe)
        .order_by(db.func.count(Finding.id).desc())
        .limit(5)
        .all()
    )
    by_target = (
        db.session.query(Finding.target, db.func.count(Finding.id))
        .filter(Finding.program_id == program_id)
        .group_by(Finding.target)
        .order_by(db.func.count(Finding.id).desc())
        .limit(5)
        .all()
    )
    return {
        "by_cwe": [{"cwe": cwe, "count": count} for cwe, count in by_cwe if cwe],
        "by_target": [
            {"target": target, "count": count} for target, count in by_target if target
        ],
    }


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


@api_bp.get("/findings")
@api_key_required
def list_findings():
    q = request.args.get("q", "").strip()
    severity = request.args.get("severity", "")
    status = request.args.get("status", "")
    agent = request.args.get("agent", "")
    limit = _limit_arg()
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
            "findings": [finding.to_dict() for finding in findings],
        }
    )


@api_bp.get("/findings/<int:fid>")
@api_key_required
def get_finding(fid):
    return jsonify(Finding.query.get_or_404(fid).to_dict())


@api_bp.get("/findings/<int:fid>/report-pack")
@api_key_required
def get_report_pack(fid):
    finding = Finding.query.get_or_404(fid)
    return jsonify(_build_report_pack(finding))


@api_bp.post("/findings")
@api_key_required
def create_finding():
    data = request.get_json(force=True) or {}

    err = _require_fields(data, "title", "target")
    if err:
        return err

    severity = data.get("severity", "medium")
    err = _validate_from_data(severity, "severity", SEVERITIES)
    if err:
        return err

    status = data.get("status", "discovered")
    err = _validate_from_data(status, "status", STATUSES)
    if err:
        return err

    confidence = data.get("confidence", "high")
    err = _validate_from_data(confidence, "confidence", CONFIDENCE_LEVELS)
    if err:
        return err

    hypothesis_id = data.get("hypothesis_id")
    if hypothesis_id:
        Hypothesis.query.get_or_404(hypothesis_id)

    finding = Finding(
        title=data["title"].strip(),
        target=data["target"].strip(),
        platform=data.get("platform", "private"),
        severity=severity,
        status=status,
        agent=data.get("agent", "manual"),
        cwe=data.get("cwe") or None,
        cvss=_parse_float(data.get("cvss")),
        confidence=confidence,
        description=data.get("description", ""),
        poc=data.get("poc", ""),
        program_id=data.get("program_id") or None,
        hypothesis_id=hypothesis_id or None,
    )
    _save(finding)
    return jsonify(finding.to_dict()), 201


@api_bp.patch("/findings/<int:fid>")
@api_key_required
def update_finding(fid):
    finding = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}

    _apply_fields(finding, data, [
        "title", "target", "platform", "agent", "cwe",
        "description", "poc", "program_id",
    ])

    if "hypothesis_id" in data:
        hypothesis_id = data["hypothesis_id"]
        if hypothesis_id:
            Hypothesis.query.get_or_404(hypothesis_id)
        finding.hypothesis_id = hypothesis_id or None

    for field, allowed in [
        ("severity", SEVERITIES),
        ("status", STATUSES),
        ("confidence", CONFIDENCE_LEVELS),
    ]:
        if field in data:
            err = _validate_from_data(data, field, allowed)
            if err:
                return err
            setattr(finding, field, data[field])

    if "cvss" in data:
        finding.cvss = _parse_float(data["cvss"])

    _touch(finding)
    _save()
    return jsonify(finding.to_dict())


@api_bp.patch("/findings/<int:fid>/status")
@api_key_required
def update_status(fid):
    finding = Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}
    new_status = data.get("status")
    err = _validate_from_data(new_status, "status", STATUSES)
    if err:
        return err
    finding.status = new_status
    _touch(finding)
    _save()
    return jsonify({"id": finding.id, "status": finding.status})


@api_bp.delete("/findings/<int:fid>")
@api_key_required
def delete_finding(fid):
    finding = Finding.query.get_or_404(fid)
    db.session.delete(finding)
    _save()
    return jsonify({"deleted": fid})


@api_bp.post("/findings/<int:fid>/attachments")
@api_key_required
def upload_attachment(fid):
    Finding.query.get_or_404(fid)
    data = request.get_json(force=True) or {}

    filename = data.get("filename")
    content_b64 = data.get("content")
    if not filename or not content_b64:
        return jsonify({"error": "filename and content (base64) are required"}), 400

    if not allowed_file(filename):
        return jsonify({"error": "File type not allowed"}), 400

    import base64
    import os
    import uuid
    from werkzeug.utils import secure_filename

    try:
        content = base64.b64decode(content_b64)
    except Exception:
        return jsonify({"error": "Invalid base64 content"}), 400

    original = secure_filename(filename)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)

    with open(dest, "wb") as file_out:
        file_out.write(content)

    attachment = Attachment(
        finding_id=fid,
        filename=stored,
        original_name=original,
        path=dest,
    )
    _save(attachment)
    return jsonify(attachment.to_dict()), 201


@api_bp.get("/enums")
@api_key_required
def get_enums():
    return jsonify(
        {
            "severities": SEVERITIES,
            "statuses": STATUSES,
            "agents": AGENTS,
            "platforms": PLATFORMS,
            "recon_categories": RECON_CATEGORIES,
            "webhook_events": WEBHOOK_EVENTS,
            "confidence_levels": CONFIDENCE_LEVELS,
            "observation_categories": OBSERVATION_CATEGORIES,
            "observation_statuses": OBSERVATION_STATUSES,
            "hypothesis_statuses": HYPOTHESIS_STATUSES,
            "evidence_types": EVIDENCE_TYPES,
            "asset_kinds": ASSET_KINDS,
            "asset_environments": ASSET_ENVIRONMENTS,
            "endpoint_protocols": ENDPOINT_PROTOCOLS,
        }
    )


@api_bp.get("/programs")
@api_key_required
def list_programs():
    programs = Program.query.order_by(Program.active.desc(), Program.name).all()
    return jsonify([program.to_dict() for program in programs])


@api_bp.get("/programs/<int:pid>")
@api_key_required
def get_program(pid):
    return jsonify(Program.query.get_or_404(pid).to_dict())


@api_bp.post("/programs")
@api_key_required
def create_program():
    data = request.get_json(force=True) or {}
    err = _require_fields(data, "name")
    if err:
        return err
    program = Program(
        name=data["name"].strip(),
        platform=data.get("platform", "private"),
        program_url=data.get("program_url"),
        logo_url=data.get("logo_url"),
        scope_in=data.get("scope_in", ""),
        scope_out=data.get("scope_out", ""),
        notes=data.get("notes", ""),
        active=data.get("active", True),
    )
    _save(program)
    return jsonify(program.to_dict()), 201


@api_bp.patch("/programs/<int:pid>")
@api_key_required
def update_program(pid):
    program = Program.query.get_or_404(pid)
    data = request.get_json(force=True) or {}
    _apply_fields(program, data, [
        "name", "platform", "program_url", "scope_in", "scope_out", "notes",
    ])
    if "logo_url" in data:
        program.logo_url = data.get("logo_url")
    if "active" in data:
        program.active = bool(data["active"])
    _touch(program)
    _save()
    return jsonify(program.to_dict())


@api_bp.delete("/programs/<int:pid>")
@api_key_required
def delete_program(pid):
    program = Program.query.get_or_404(pid)
    db.session.delete(program)
    _save()
    return jsonify({"deleted": pid})


@api_bp.get("/programs/<int:pid>/context")
@api_key_required
def get_target_context(pid):
    ctx = TargetContext.query.filter_by(program_id=pid).first()
    if not ctx:
        return jsonify({"program_id": pid, "data": {}})
    return jsonify(ctx.to_dict())


@api_bp.put("/programs/<int:pid>/context")
@api_key_required
def save_target_context(pid):
    _require_program(pid)
    data = request.get_json(force=True) or {}
    payload = data.get("data", data)

    ctx = TargetContext.query.filter_by(program_id=pid).first()
    if ctx:
        ctx.data = payload
    else:
        ctx = TargetContext(program_id=pid, _data=json.dumps(payload))
        db.session.add(ctx)
    _save()
    return jsonify(ctx.to_dict()), 201


@api_bp.get("/programs/<int:pid>/brief")
@api_key_required
def get_program_brief(pid):
    program = Program.query.get_or_404(pid)
    context = TargetContext.query.filter_by(program_id=pid).first()
    recent_findings = (
        Finding.query.filter_by(program_id=pid)
        .order_by(Finding.updated_at.desc())
        .limit(10)
        .all()
    )
    recent_recon = (
        ReconEntry.query.filter_by(program_id=pid)
        .order_by(ReconEntry.created_at.desc())
        .limit(15)
        .all()
    )
    open_observations = (
        Observation.query.filter(
            Observation.program_id == pid,
            Observation.status.in_(["open", "testing"]),
        )
        .order_by(Observation.updated_at.desc())
        .limit(10)
        .all()
    )
    open_hypotheses = (
        Hypothesis.query.filter(
            Hypothesis.program_id == pid,
            Hypothesis.status.in_(["open", "testing", "confirmed"]),
        )
        .order_by(Hypothesis.updated_at.desc())
        .limit(10)
        .all()
    )

    return jsonify(
        {
            "program": program.to_dict(),
            "target_context": context.to_dict() if context else {"program_id": pid, "data": {}},
            "counts": {
                "findings": Finding.query.filter_by(program_id=pid).count(),
                "recon_entries": ReconEntry.query.filter_by(program_id=pid).count(),
                "open_observations": Observation.query.filter(
                    Observation.program_id == pid,
                    Observation.status.in_(["open", "testing"]),
                ).count(),
                "open_hypotheses": Hypothesis.query.filter(
                    Hypothesis.program_id == pid,
                    Hypothesis.status.in_(["open", "testing", "confirmed"]),
                ).count(),
                "evidence_records": EvidenceRecord.query.filter_by(program_id=pid).count(),
            },
            "recent_findings": [_finding_summary(finding) for finding in recent_findings],
            "recent_recon": [entry.to_dict() for entry in recent_recon],
            "open_observations": [
                _observation_summary(observation) for observation in open_observations
            ],
            "open_hypotheses": [
                _hypothesis_summary(hypothesis) for hypothesis in open_hypotheses
            ],
            "duplicate_hotspots": _top_duplicate_hotspots(pid),
        }
    )


@api_bp.get("/programs/<int:pid>/recon")
@api_key_required
def list_recon(pid):
    category = request.args.get("category", "")
    query = ReconEntry.query.filter_by(program_id=pid)
    if category:
        query = query.filter_by(category=category)
    entries = query.order_by(ReconEntry.category, ReconEntry.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])


@api_bp.post("/programs/<int:pid>/recon")
@api_key_required
def add_recon(pid):
    _require_program(pid)
    data = request.get_json(force=True) or {}
    err = _require_fields(data, "value")
    if err:
        return err
    recon_entry = ReconEntry(
        program_id=pid,
        category=data.get("category", "subdomain"),
        value=data["value"].strip(),
        notes=data.get("notes", ""),
        source=data.get("source", ""),
    )
    _save(recon_entry)
    return jsonify(recon_entry.to_dict()), 201


@api_bp.delete("/recon/<int:rid>")
@api_key_required
def delete_recon(rid):
    recon_entry = ReconEntry.query.get_or_404(rid)
    db.session.delete(recon_entry)
    _save()
    return jsonify({"deleted": rid})


@api_bp.get("/programs/<int:pid>/observations")
@api_key_required
def list_observations(pid):
    _require_program(pid)
    status = request.args.get("status", "").strip()
    category = request.args.get("category", "").strip()
    query = Observation.query.filter_by(program_id=pid)
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    observations = query.order_by(Observation.updated_at.desc()).limit(_limit_arg()).all()
    return jsonify([observation.to_dict() for observation in observations])


@api_bp.post("/programs/<int:pid>/observations")
@api_key_required
def create_observation(pid):
    _require_program(pid)
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    category = data.get("category", "other")
    err = _validate_from_data(category, "category", OBSERVATION_CATEGORIES)
    if err:
        return err

    status = data.get("status", "open")
    err = _validate_from_data(status, "status", OBSERVATION_STATUSES)
    if err:
        return err

    confidence = data.get("confidence", "medium")
    err = _validate_from_data(confidence, "confidence", CONFIDENCE_LEVELS)
    if err:
        return err

    observation = Observation(
        program_id=pid,
        title=title,
        summary=data.get("summary", ""),
        category=category,
        status=status,
        agent=data.get("agent", "manual"),
        source_tool=data.get("source_tool"),
        confidence=confidence,
    )
    _save(observation)
    return jsonify(observation.to_dict()), 201


@api_bp.get("/observations/<int:oid>")
@api_key_required
def get_observation(oid):
    return jsonify(Observation.query.get_or_404(oid).to_dict())


@api_bp.patch("/observations/<int:oid>")
@api_key_required
def update_observation(oid):
    observation = Observation.query.get_or_404(oid)
    data = request.get_json(force=True) or {}

    _apply_fields(observation, data, ["title", "summary", "agent", "source_tool"])

    for field, allowed in [
        ("category", OBSERVATION_CATEGORIES),
        ("status", OBSERVATION_STATUSES),
        ("confidence", CONFIDENCE_LEVELS),
    ]:
        if field in data:
            err = _validate_from_data(data, field, allowed)
            if err:
                return err
            setattr(observation, field, data[field])

    _touch(observation)
    _save()
    return jsonify(observation.to_dict())


@api_bp.delete("/observations/<int:oid>")
@api_key_required
def delete_observation(oid):
    observation = Observation.query.get_or_404(oid)
    db.session.delete(observation)
    _save()
    return jsonify({"deleted": oid})


@api_bp.post("/observations/<int:oid>/promote")
@api_key_required
def promote_observation(oid):
    observation = Observation.query.get_or_404(oid)
    data = request.get_json(force=True) or {}

    title = (data.get("title") or observation.title).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    severity_hint = data.get("severity_hint")
    if severity_hint:
        err = _validate_from_data(severity_hint, "severity_hint", SEVERITIES)
        if err:
            return err

    status = data.get("status", "open")
    err = _validate_from_data(status, "status", HYPOTHESIS_STATUSES)
    if err:
        return err

    confidence = data.get("confidence", observation.confidence)
    err = _validate_from_data(confidence, "confidence", CONFIDENCE_LEVELS)
    if err:
        return err

    hypothesis = Hypothesis(
        program_id=observation.program_id,
        observation_id=observation.id,
        title=title,
        weakness_hint=data.get("weakness_hint"),
        cwe=data.get("cwe"),
        severity_hint=severity_hint,
        attack_path=data.get("attack_path", observation.summary),
        impact_hypothesis=data.get("impact_hypothesis", ""),
        status=status,
        agent=data.get("agent", observation.agent),
        confidence=confidence,
    )
    observation.status = "promoted"
    _touch(observation)

    _save(hypothesis)
    return jsonify({"observation": observation.to_dict(), "hypothesis": hypothesis.to_dict()}), 201


@api_bp.get("/programs/<int:pid>/hypotheses")
@api_key_required
def list_hypotheses(pid):
    _require_program(pid)
    status = request.args.get("status", "").strip()
    query = Hypothesis.query.filter_by(program_id=pid)
    if status:
        query = query.filter_by(status=status)
    hypotheses = query.order_by(Hypothesis.updated_at.desc()).limit(_limit_arg()).all()
    return jsonify([hypothesis.to_dict() for hypothesis in hypotheses])


@api_bp.post("/programs/<int:pid>/hypotheses")
@api_key_required
def create_hypothesis(pid):
    _require_program(pid)
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    status = data.get("status", "open")
    err = _validate_from_data(status, "status", HYPOTHESIS_STATUSES)
    if err:
        return err

    confidence = data.get("confidence", "medium")
    err = _validate_from_data(confidence, "confidence", CONFIDENCE_LEVELS)
    if err:
        return err

    severity_hint = data.get("severity_hint")
    if severity_hint:
        err = _validate_from_data(severity_hint, "severity_hint", SEVERITIES)
        if err:
            return err

    observation_id = data.get("observation_id")
    if observation_id:
        observation = Observation.query.get_or_404(observation_id)
        err = _check_ownership(observation, pid, "observation_id")
        if err:
            return err

    hypothesis = Hypothesis(
        program_id=pid,
        observation_id=observation_id or None,
        title=title,
        weakness_hint=data.get("weakness_hint"),
        cwe=data.get("cwe"),
        severity_hint=severity_hint,
        attack_path=data.get("attack_path", ""),
        impact_hypothesis=data.get("impact_hypothesis", ""),
        status=status,
        agent=data.get("agent", "manual"),
        confidence=confidence,
    )
    _save(hypothesis)
    return jsonify(hypothesis.to_dict()), 201


@api_bp.get("/hypotheses/<int:hid>")
@api_key_required
def get_hypothesis(hid):
    return jsonify(Hypothesis.query.get_or_404(hid).to_dict())


@api_bp.patch("/hypotheses/<int:hid>")
@api_key_required
def update_hypothesis(hid):
    hypothesis = Hypothesis.query.get_or_404(hid)
    data = request.get_json(force=True) or {}

    _apply_fields(hypothesis, data, [
        "title", "weakness_hint", "cwe", "attack_path", "impact_hypothesis", "agent",
    ])

    if "severity_hint" in data:
        severity_hint = data["severity_hint"]
        if severity_hint:
            err = _validate_from_data(severity_hint, "severity_hint", SEVERITIES)
            if err:
                return err
        hypothesis.severity_hint = severity_hint

    for field, allowed in [
        ("status", HYPOTHESIS_STATUSES),
        ("confidence", CONFIDENCE_LEVELS),
    ]:
        if field in data:
            err = _validate_from_data(data, field, allowed)
            if err:
                return err
            setattr(hypothesis, field, data[field])

    if "observation_id" in data:
        observation_id = data["observation_id"]
        if observation_id:
            observation = Observation.query.get_or_404(observation_id)
            err = _check_ownership(observation, hypothesis.program_id, "observation_id")
            if err:
                return err
        hypothesis.observation_id = observation_id or None

    _touch(hypothesis)
    _save()
    return jsonify(hypothesis.to_dict())


@api_bp.delete("/hypotheses/<int:hid>")
@api_key_required
def delete_hypothesis(hid):
    hypothesis = Hypothesis.query.get_or_404(hid)
    db.session.delete(hypothesis)
    _save()
    return jsonify({"deleted": hid})


@api_bp.post("/hypotheses/<int:hid>/promote")
@api_key_required
def promote_hypothesis(hid):
    hypothesis = Hypothesis.query.get_or_404(hid)
    data = request.get_json(force=True) or {}

    title = (data.get("title") or hypothesis.title).strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    severity = data.get("severity") or hypothesis.severity_hint or "medium"
    err = _validate_from_data(severity, "severity", SEVERITIES)
    if err:
        return err

    status = data.get("status", "discovered")
    err = _validate_from_data(status, "status", STATUSES)
    if err:
        return err

    confidence = data.get("confidence", "high")
    err = _validate_from_data(confidence, "confidence", CONFIDENCE_LEVELS)
    if err:
        return err

    finding = Finding(
        program_id=hypothesis.program_id,
        hypothesis_id=hypothesis.id,
        title=title,
        target=(data.get("target") or _derive_target_from_hypothesis(hypothesis)).strip(),
        platform=data.get("platform", hypothesis.program.platform),
        severity=severity,
        status=status,
        agent=data.get("agent", hypothesis.agent),
        cwe=data.get("cwe") or hypothesis.cwe,
        cvss=_parse_float(data.get("cvss")),
        confidence=confidence,
        description=data.get("description", ""),
        poc=data.get("poc", ""),
    )
    hypothesis.status = "promoted"
    _touch(hypothesis)

    _save(finding)
    return jsonify({"hypothesis": hypothesis.to_dict(), "finding": finding.to_dict()}), 201


@api_bp.get("/programs/<int:pid>/evidence")
@api_key_required
def list_evidence(pid):
    Program.query.get_or_404(pid)
    query = EvidenceRecord.query.filter_by(program_id=pid)

    finding_id = request.args.get("finding_id", type=int)
    hypothesis_id = request.args.get("hypothesis_id", type=int)
    observation_id = request.args.get("observation_id", type=int)
    evidence_type = request.args.get("evidence_type", "").strip()

    if finding_id:
        query = query.filter_by(finding_id=finding_id)
    if hypothesis_id:
        query = query.filter_by(hypothesis_id=hypothesis_id)
    if observation_id:
        query = query.filter_by(observation_id=observation_id)
    if evidence_type:
        query = query.filter_by(evidence_type=evidence_type)

    evidence = query.order_by(EvidenceRecord.created_at.desc()).limit(_limit_arg()).all()
    return jsonify([record.to_dict() for record in evidence])


@api_bp.post("/evidence")
@api_key_required
def create_evidence():
    data = request.get_json(force=True) or {}

    program_id = data.get("program_id")
    if not program_id:
        return jsonify({"error": "program_id is required"}), 400
    _require_program(program_id)

    title = (data.get("title") or "").strip()
    if not title:
        request_method = data.get("request_method")
        request_url = data.get("request_url")
        if request_method and request_url:
            title = f"{request_method} {request_url}"
        else:
            return jsonify({"error": "title is required"}), 400

    evidence_type = data.get("evidence_type", "other")
    err = _validate_from_data(evidence_type, "evidence_type", EVIDENCE_TYPES)
    if err:
        return err

    finding_id = data.get("finding_id") or None
    hypothesis_id = data.get("hypothesis_id") or None
    observation_id = data.get("observation_id") or None

    if finding_id:
        finding = Finding.query.get_or_404(finding_id)
        err = _check_ownership(finding, program_id, "finding_id")
        if err:
            return err
    if hypothesis_id:
        hypothesis = Hypothesis.query.get_or_404(hypothesis_id)
        err = _check_ownership(hypothesis, program_id, "hypothesis_id")
        if err:
            return err
    if observation_id:
        observation = Observation.query.get_or_404(observation_id)
        err = _check_ownership(observation, program_id, "observation_id")
        if err:
            return err

    evidence = EvidenceRecord(
        program_id=program_id,
        finding_id=finding_id,
        hypothesis_id=hypothesis_id,
        observation_id=observation_id,
        evidence_type=evidence_type,
        title=title,
        summary=data.get("summary", ""),
        request_method=data.get("request_method"),
        request_url=data.get("request_url"),
        request_headers_json=_json_text(data.get("request_headers")),
        request_body_text=data.get("request_body_text"),
        response_status=_parse_int(data.get("response_status")),
        response_headers_json=_json_text(data.get("response_headers")),
        response_body_text=data.get("response_body_text"),
        account_label=data.get("account_label"),
        auth_type=data.get("auth_type"),
        source_tool=data.get("source_tool"),
        occurred_at=_parse_datetime(data.get("occurred_at")),
    )
    _save(evidence)
    return jsonify(evidence.to_dict()), 201


@api_bp.get("/evidence/<int:eid>")
@api_key_required
def get_evidence(eid):
    return jsonify(EvidenceRecord.query.get_or_404(eid).to_dict())


@api_bp.patch("/evidence/<int:eid>")
@api_key_required
def update_evidence(eid):
    evidence = EvidenceRecord.query.get_or_404(eid)
    data = request.get_json(force=True) or {}

    _apply_fields(evidence, data, [
        "title", "summary", "request_method", "request_url",
        "request_body_text", "response_body_text", "account_label",
        "auth_type", "source_tool",
    ])

    if "evidence_type" in data:
        err = _validate_from_data(data, "evidence_type", EVIDENCE_TYPES)
        if err:
            return err
        evidence.evidence_type = data["evidence_type"]

    if "response_status" in data:
        evidence.response_status = _parse_int(data["response_status"])

    if "request_headers" in data:
        evidence.request_headers_json = _json_text(data["request_headers"])
    if "response_headers" in data:
        evidence.response_headers_json = _json_text(data["response_headers"])
    if "occurred_at" in data:
        evidence.occurred_at = _parse_datetime(data["occurred_at"])

    _save()
    return jsonify(evidence.to_dict())


# ── Assets ─────────────────────────────────────────────────────────────────


@api_bp.get("/programs/<int:pid>/assets")
@api_key_required
def list_assets(pid):
    _require_program(pid)
    kind = request.args.get("kind", "").strip()
    query = Asset.query.filter_by(program_id=pid)
    if kind:
        query = query.filter_by(kind=kind)
    assets = query.order_by(Asset.kind, Asset.identifier).all()
    return jsonify([asset.to_dict() for asset in assets])


@api_bp.post("/programs/<int:pid>/assets")
@api_key_required
def create_asset(pid):
    _require_program(pid)
    data = request.get_json(force=True) or {}
    identifier = (data.get("identifier") or "").strip()
    if not identifier:
        return jsonify({"error": "identifier is required"}), 400

    kind = data.get("kind", "other")
    err = _validate_from_data(kind, "kind", ASSET_KINDS)
    if err:
        return err

    environment = data.get("environment", "unknown")
    err = _validate_from_data(environment, "environment", ASSET_ENVIRONMENTS)
    if err:
        return err

    asset = Asset(
        program_id=pid,
        kind=kind,
        identifier=identifier,
        environment=environment,
        notes=data.get("notes", ""),
        active=data.get("active", True),
    )
    _save(asset)
    return jsonify(asset.to_dict()), 201


@api_bp.patch("/assets/<int:aid>")
@api_key_required
def update_asset(aid):
    asset = Asset.query.get_or_404(aid)
    data = request.get_json(force=True) or {}
    _apply_fields(asset, data, ["identifier", "notes"])

    for field, allowed in [
        ("kind", ASSET_KINDS),
        ("environment", ASSET_ENVIRONMENTS),
    ]:
        if field in data:
            err = _validate_from_data(data, field, allowed)
            if err:
                return err
            setattr(asset, field, data[field])

    if "active" in data:
        asset.active = bool(data["active"])
    _touch(asset)
    _save()
    return jsonify(asset.to_dict())


@api_bp.delete("/assets/<int:aid>")
@api_key_required
def delete_asset(aid):
    asset = Asset.query.get_or_404(aid)
    db.session.delete(asset)
    _save()
    return jsonify({"deleted": aid})


# ── Endpoints ──────────────────────────────────────────────────────────────


@api_bp.get("/assets/<int:aid>/endpoints")
@api_key_required
def list_endpoints(aid):
    Asset.query.get_or_404(aid)
    method = request.args.get("method", "").strip()
    query = Endpoint.query.filter_by(asset_id=aid)
    if method:
        query = query.filter_by(method=method)
    endpoints = query.order_by(Endpoint.method, Endpoint.path).all()
    return jsonify([endpoint.to_dict() for endpoint in endpoints])


@api_bp.post("/assets/<int:aid>/endpoints")
@api_key_required
def create_endpoint(aid):
    Asset.query.get_or_404(aid)
    data = request.get_json(force=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400
    method = data.get("method", "GET")
    protocol = data.get("protocol", "https")
    err = _validate_from_data(protocol, "protocol", ENDPOINT_PROTOCOLS)
    if err:
        return err
    endpoint = Endpoint(
        asset_id=aid,
        method=method,
        path=path,
        protocol=protocol,
        content_type=data.get("content_type"),
        auth_required=data.get("auth_required"),
        discovered_by=data.get("discovered_by"),
        notes=data.get("notes", ""),
    )
    _save(endpoint)
    return jsonify(endpoint.to_dict()), 201


@api_bp.patch("/endpoints/<int:eid>")
@api_key_required
def update_endpoint(eid):
    endpoint = Endpoint.query.get_or_404(eid)
    data = request.get_json(force=True) or {}
    _apply_fields(endpoint, data, ["path", "content_type", "discovered_by", "notes"])
    if "method" in data:
        endpoint.method = data["method"]
    if "protocol" in data:
        err = _validate_from_data(data, "protocol", ENDPOINT_PROTOCOLS)
        if err:
            return err
        endpoint.protocol = data["protocol"]
    if "auth_required" in data:
        endpoint.auth_required = bool(data["auth_required"]) if data["auth_required"] is not None else None
    _touch(endpoint)
    _save()
    return jsonify(endpoint.to_dict())


@api_bp.delete("/endpoints/<int:eid>")
@api_key_required
def delete_endpoint(eid):
    endpoint = Endpoint.query.get_or_404(eid)
    db.session.delete(endpoint)
    _save()
    return jsonify({"deleted": eid})


@api_bp.post("/similarity/check")
@api_key_required
def similarity_check():
    data = request.get_json(force=True) or {}

    query = {
        "program_id": data.get("program_id"),
        "target": data.get("target") or data.get("asset_identifier"),
        "title": data.get("title"),
        "cwe": data.get("cwe"),
        "description": data.get("description"),
    }

    if not any([query["target"], query["title"], query["cwe"], query["description"]]):
        return jsonify({"error": "provide target, title, cwe, or description"}), 400

    program_id = query["program_id"]

    finding_query = Finding.query
    observation_query = Observation.query
    hypothesis_query = Hypothesis.query
    if program_id:
        finding_query = finding_query.filter_by(program_id=program_id)
        observation_query = observation_query.filter_by(program_id=program_id)
        hypothesis_query = hypothesis_query.filter_by(program_id=program_id)

    def _score(item_dict, summary, kind="finding"):
        score, reasons = _similarity_score(item_dict, query)
        if score < 20:
            return None
        if kind == "observation":
            relation = "likely_duplicate" if score >= 45 else "related_work"
        else:
            relation = "exact_match" if score >= 65 else "likely_duplicate" if score >= 40 else "related_work"
        return {"relation": relation, "score": score, "reasons": reasons, "item": summary}

    scored = []

    for finding in finding_query.order_by(Finding.updated_at.desc()).limit(150).all():
        result = _score(
            {"id": finding.id, "title": finding.title, "target": finding.target,
             "cwe": finding.cwe, "description": finding.description},
            _finding_summary(finding),
            kind="finding",
        )
        if result:
            scored.append({"kind": "finding", **result})

    for observation in observation_query.order_by(Observation.updated_at.desc()).limit(150).all():
        result = _score(
            {"id": observation.id, "title": observation.title,
             "program_name": observation.program.name if observation.program else "",
             "summary": observation.summary},
            _observation_summary(observation),
            kind="observation",
        )
        if result:
            scored.append({"kind": "observation", **result})

    for hypothesis in hypothesis_query.order_by(Hypothesis.updated_at.desc()).limit(150).all():
        result = _score(
            {"id": hypothesis.id, "title": hypothesis.title,
             "program_name": hypothesis.program.name if hypothesis.program else "",
             "cwe": hypothesis.cwe, "summary": hypothesis.attack_path or hypothesis.impact_hypothesis},
            _hypothesis_summary(hypothesis),
            kind="hypothesis",
        )
        if result:
            scored.append({"kind": "hypothesis", **result})

    scored.sort(key=lambda item: item["score"], reverse=True)
    exact_matches = [item for item in scored if item["relation"] == "exact_match"][:10]
    likely_duplicates = [item for item in scored if item["relation"] == "likely_duplicate"][:10]
    related_work = [item for item in scored if item["relation"] == "related_work"][:10]

    return jsonify(
        {
            "query": query,
            "exact_matches": exact_matches,
            "likely_duplicates": likely_duplicates,
            "related_work": related_work,
        }
    )


@api_bp.post("/findings/<int:fid>/notes")
@api_key_required
def add_note(fid):
    data = request.get_json(force=True) or {}
    err = _require_fields(data, "content")
    if err:
        return err
    note = Note(
        finding_id=fid,
        content=data["content"],
        agent=data.get("agent", "manual"),
    )
    _save(note)
    return jsonify(note.to_dict()), 201


@api_bp.delete("/notes/<int:nid>")
@api_key_required
def delete_note(nid):
    note = Note.query.get_or_404(nid)
    db.session.delete(note)
    _save()
    return jsonify({"deleted": nid})


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
            "findings": [finding.to_dict() for finding in results],
        }
    )


@api_bp.patch("/findings/bulk/status")
@api_key_required
def bulk_update_status():
    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    status = data.get("status")
    if not ids or not status:
        return jsonify({"error": "ids (list) and status are required"}), 400
    err = _validate_from_data(status, "status", STATUSES)
    if err:
        return err

    updated = []
    for fid in ids:
        finding = db.session.get(Finding, fid)
        if finding:
            finding.status = status
            _touch(finding)
            updated.append(fid)
    _save()
    return jsonify({"updated": updated, "status": status})


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
