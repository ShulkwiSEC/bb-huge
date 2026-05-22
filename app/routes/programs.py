from datetime import datetime, timezone
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash)
from .. import db
from ..models import (
    ASSET_ENVIRONMENTS,
    ASSET_KINDS,
    CONFIDENCE_LEVELS,
    ENDPOINT_PROTOCOLS,
    HYPOTHESIS_STATUSES,
    OBSERVATION_CATEGORIES,
    OBSERVATION_STATUSES,
    PLATFORMS,
    RECON_CATEGORIES,
    SEVERITIES,
    STATUSES,
    Asset,
    Endpoint,
    EvidenceRecord,
    Finding,
    Hypothesis,
    Observation,
    Program,
    ReconEntry,
    TargetContext,
)
from .auth import login_required

programs_bp = Blueprint("programs", __name__)


# ── List ──────────────────────────────────────────────────────────────────────

@programs_bp.route("/programs")
@login_required
def list_programs():
    programs = Program.query.order_by(Program.active.desc(), Program.name).all()
    return render_template("programs/list.html", programs=programs)


# ── Detail ────────────────────────────────────────────────────────────────────

@programs_bp.route("/programs/<int:pid>")
@login_required
def detail(pid):
    program  = Program.query.get_or_404(pid)
    findings = (Finding.query
                .filter_by(program_id=pid)
                .order_by(Finding.created_at.desc())
                .all())
    recon    = (ReconEntry.query
                .filter_by(program_id=pid)
                .order_by(ReconEntry.category, ReconEntry.created_at.desc())
                .all())
    assets = (
        Asset.query.filter_by(program_id=pid)
        .order_by(Asset.kind, Asset.identifier)
        .all()
    )
    observations = (
        Observation.query.filter_by(program_id=pid)
        .order_by(Observation.updated_at.desc())
        .all()
    )
    hypotheses = (
        Hypothesis.query.filter_by(program_id=pid)
        .order_by(Hypothesis.updated_at.desc())
        .all()
    )
    evidence_records = (
        EvidenceRecord.query.filter_by(program_id=pid)
        .order_by(EvidenceRecord.created_at.desc())
        .limit(50)
        .all()
    )
    target_context = TargetContext.query.filter_by(program_id=pid).first()

    # Group recon by category
    recon_grouped = {}
    for r in recon:
        recon_grouped.setdefault(r.category, []).append(r)

    duplicate_hotspots = {
        "by_cwe": (
            db.session.query(Finding.cwe, db.func.count(Finding.id))
            .filter(Finding.program_id == pid, Finding.cwe.isnot(None))
            .group_by(Finding.cwe)
            .order_by(db.func.count(Finding.id).desc())
            .limit(5)
            .all()
        ),
        "by_target": (
            db.session.query(Finding.target, db.func.count(Finding.id))
            .filter(Finding.program_id == pid)
            .group_by(Finding.target)
            .order_by(db.func.count(Finding.id).desc())
            .limit(5)
            .all()
        ),
    }

    return render_template(
        "programs/detail.html",
        program=program,
        findings=findings,
        assets=assets,
        observations=observations,
        hypotheses=hypotheses,
        evidence_records=evidence_records,
        target_context=target_context,
        duplicate_hotspots=duplicate_hotspots,
        recon_grouped=recon_grouped,
        recon_categories=RECON_CATEGORIES,
        observation_categories=OBSERVATION_CATEGORIES,
        observation_statuses=OBSERVATION_STATUSES,
        hypothesis_statuses=HYPOTHESIS_STATUSES,
        confidence_levels=CONFIDENCE_LEVELS,
        severities=SEVERITIES,
        statuses=STATUSES,
        asset_kinds=ASSET_KINDS,
        asset_environments=ASSET_ENVIRONMENTS,
        endpoint_protocols=ENDPOINT_PROTOCOLS,
    )


# ── Add ───────────────────────────────────────────────────────────────────────

@programs_bp.route("/programs/add", methods=["GET", "POST"])
@login_required
def add_program():
    if request.method == "POST":
        p = Program(
            name        = request.form["name"].strip(),
            platform    = request.form.get("platform", "private"),
            program_url = request.form.get("program_url", "").strip() or None,
            scope_in    = request.form.get("scope_in", ""),
            scope_out   = request.form.get("scope_out", ""),
            notes       = request.form.get("notes", ""),
            active      = request.form.get("active") == "on",
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Program '{p.name}' created ✓", "success")
        return redirect(url_for("programs.detail", pid=p.id))

    return render_template("programs/form.html",
                           program=None, platforms=PLATFORMS)


# ── Edit ──────────────────────────────────────────────────────────────────────

@programs_bp.route("/programs/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def edit_program(pid):
    p = Program.query.get_or_404(pid)

    if request.method == "POST":
        p.name        = request.form["name"].strip()
        p.platform    = request.form.get("platform", p.platform)
        p.program_url = request.form.get("program_url", "").strip() or None
        p.scope_in    = request.form.get("scope_in", "")
        p.scope_out   = request.form.get("scope_out", "")
        p.notes       = request.form.get("notes", "")
        p.active      = request.form.get("active") == "on"
        p.updated_at  = datetime.now(timezone.utc)
        db.session.commit()
        flash("Program updated ✓", "success")
        return redirect(url_for("programs.detail", pid=p.id))

    return render_template("programs/form.html",
                           program=p, platforms=PLATFORMS)


# ── Delete ────────────────────────────────────────────────────────────────────

@programs_bp.route("/programs/<int:pid>/delete", methods=["POST"])
@login_required
def delete_program(pid):
    p = Program.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Program deleted.", "info")
    return redirect(url_for("programs.list_programs"))


# ── Recon: Add ────────────────────────────────────────────────────────────────

@programs_bp.route("/programs/<int:pid>/recon/add", methods=["POST"])
@login_required
def add_recon(pid):
    Program.query.get_or_404(pid)
    value = request.form.get("value", "").strip()
    if value:
        r = ReconEntry(
            program_id = pid,
            category   = request.form.get("category", "subdomain"),
            value      = value,
            notes      = request.form.get("notes", ""),
            source     = request.form.get("source", "manual").strip() or "manual",
        )
        db.session.add(r)
        db.session.commit()
        flash("Recon entry added ✓", "success")
    return redirect(url_for("programs.detail", pid=pid) + "#recon")


@programs_bp.route("/programs/<int:pid>/observations/add", methods=["POST"])
@login_required
def add_observation(pid):
    Program.query.get_or_404(pid)
    title = request.form.get("title", "").strip()
    if title:
        observation = Observation(
            program_id=pid,
            title=title,
            summary=request.form.get("summary", ""),
            category=request.form.get("category", "other"),
            status=request.form.get("status", "open"),
            agent=request.form.get("agent", "manual").strip() or "manual",
            source_tool=request.form.get("source_tool", "").strip() or None,
            confidence=request.form.get("confidence", "medium"),
        )
        db.session.add(observation)
        db.session.commit()
        flash("Observation added ✓", "success")
    else:
        flash("Observation title is required.", "error")
    return redirect(url_for("programs.detail", pid=pid) + "#observations")


@programs_bp.route("/programs/<int:pid>/hypotheses/add", methods=["POST"])
@login_required
def add_hypothesis(pid):
    Program.query.get_or_404(pid)
    title = request.form.get("title", "").strip()
    if title:
        observation_id = request.form.get("observation_id", type=int) or None
        if observation_id:
            observation = db.session.get(Observation, observation_id)
            if not observation or observation.program_id != pid:
                observation_id = None
        hypothesis = Hypothesis(
            program_id=pid,
            observation_id=observation_id,
            title=title,
            weakness_hint=request.form.get("weakness_hint", "").strip() or None,
            cwe=request.form.get("cwe", "").strip() or None,
            severity_hint=request.form.get("severity_hint", "").strip() or None,
            attack_path=request.form.get("attack_path", ""),
            impact_hypothesis=request.form.get("impact_hypothesis", ""),
            status=request.form.get("status", "open"),
            agent=request.form.get("agent", "manual").strip() or "manual",
            confidence=request.form.get("confidence", "medium"),
        )
        db.session.add(hypothesis)
        db.session.commit()
        flash("Hypothesis added ✓", "success")
    else:
        flash("Hypothesis title is required.", "error")
    return redirect(url_for("programs.detail", pid=pid) + "#hypotheses")


@programs_bp.route("/observations/<int:oid>/promote", methods=["POST"])
@login_required
def promote_observation(oid):
    observation = Observation.query.get_or_404(oid)
    hypothesis = Hypothesis(
        program_id=observation.program_id,
        observation_id=observation.id,
        title=request.form.get("title", "").strip() or observation.title,
        weakness_hint=request.form.get("weakness_hint", "").strip() or None,
        cwe=request.form.get("cwe", "").strip() or None,
        severity_hint=request.form.get("severity_hint", "").strip() or None,
        attack_path=request.form.get("attack_path", "").strip() or observation.summary,
        impact_hypothesis=request.form.get("impact_hypothesis", ""),
        status=request.form.get("status", "open"),
        agent=request.form.get("agent", "manual").strip() or observation.agent,
        confidence=request.form.get("confidence", "medium"),
    )
    observation.status = "promoted"
    observation.updated_at = datetime.now(timezone.utc)
    db.session.add(hypothesis)
    db.session.commit()
    flash("Observation promoted to hypothesis ✓", "success")
    return redirect(url_for("programs.detail", pid=observation.program_id) + "#hypotheses")


@programs_bp.route("/observations/<int:oid>/delete", methods=["POST"])
@login_required
def delete_observation(oid):
    observation = Observation.query.get_or_404(oid)
    pid = observation.program_id
    db.session.delete(observation)
    db.session.commit()
    flash("Observation deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#observations")


@programs_bp.route("/hypotheses/<int:hid>/promote", methods=["POST"])
@login_required
def promote_hypothesis(hid):
    hypothesis = Hypothesis.query.get_or_404(hid)
    target = request.form.get("target", "").strip() or hypothesis.program.name
    severity = request.form.get("severity", "").strip() or hypothesis.severity_hint or "medium"
    finding = Finding(
        program_id=hypothesis.program_id,
        hypothesis_id=hypothesis.id,
        title=request.form.get("title", "").strip() or hypothesis.title,
        target=target,
        platform=request.form.get("platform", "").strip() or hypothesis.program.platform,
        severity=severity,
        status=request.form.get("status", "discovered"),
        agent=request.form.get("agent", "manual").strip() or hypothesis.agent,
        cwe=request.form.get("cwe", "").strip() or hypothesis.cwe,
        cvss=None,
        confidence=request.form.get("confidence", "high"),
        description=request.form.get("description", ""),
        poc=request.form.get("poc", ""),
    )
    hypothesis.status = "promoted"
    hypothesis.updated_at = datetime.now(timezone.utc)
    db.session.add(finding)
    db.session.commit()
    flash("Hypothesis promoted to finding ✓", "success")
    return redirect(url_for("findings.detail", fid=finding.id))


@programs_bp.route("/hypotheses/<int:hid>/delete", methods=["POST"])
@login_required
def delete_hypothesis(hid):
    hypothesis = Hypothesis.query.get_or_404(hid)
    pid = hypothesis.program_id
    db.session.delete(hypothesis)
    db.session.commit()
    flash("Hypothesis deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#hypotheses")


@programs_bp.route("/evidence/<int:eid>/delete", methods=["POST"])
@login_required
def delete_evidence(eid):
    evidence = EvidenceRecord.query.get_or_404(eid)
    pid = evidence.program_id
    db.session.delete(evidence)
    db.session.commit()
    flash("Evidence deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#evidence")


# ── Assets: Add ─────────────────────────────────────────────────────────────

@programs_bp.route("/programs/<int:pid>/assets/add", methods=["POST"])
@login_required
def add_asset(pid):
    Program.query.get_or_404(pid)
    identifier = (request.form.get("identifier") or "").strip()
    if identifier:
        asset = Asset(
            program_id=pid,
            kind=request.form.get("kind", "other"),
            identifier=identifier,
            environment=request.form.get("environment", "unknown"),
            notes=request.form.get("notes", ""),
            active=request.form.get("active") == "on",
        )
        db.session.add(asset)
        db.session.commit()
        flash("Asset added ✓", "success")
    return redirect(url_for("programs.detail", pid=pid) + "#assets")


@programs_bp.route("/assets/<int:aid>/delete", methods=["POST"])
@login_required
def delete_asset(aid):
    asset = Asset.query.get_or_404(aid)
    pid = asset.program_id
    db.session.delete(asset)
    db.session.commit()
    flash("Asset deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#assets")


@programs_bp.route("/assets/<int:aid>/endpoints/add", methods=["POST"])
@login_required
def add_endpoint(aid):
    asset = Asset.query.get_or_404(aid)
    path = (request.form.get("path") or "").strip()
    if path:
        endpoint = Endpoint(
            asset_id=aid,
            method=request.form.get("method", "GET"),
            path=path,
            protocol=request.form.get("protocol", "https"),
            content_type=request.form.get("content_type", "").strip() or None,
            auth_required=True if request.form.get("auth_required") == "on" else False if "auth_required" in request.form else None,
            discovered_by=request.form.get("discovered_by", "").strip() or None,
            notes=request.form.get("notes", ""),
        )
        db.session.add(endpoint)
        db.session.commit()
        flash("Endpoint added ✓", "success")
    return redirect(url_for("programs.detail", pid=asset.program_id) + "#assets")


@programs_bp.route("/endpoints/<int:eid>/delete", methods=["POST"])
@login_required
def delete_endpoint(eid):
    endpoint = Endpoint.query.get_or_404(eid)
    pid = endpoint.asset.program_id
    db.session.delete(endpoint)
    db.session.commit()
    flash("Endpoint deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#assets")


# ── Recon: Edit ───────────────────────────────────────────────────────────────

@programs_bp.route("/recon/<int:rid>/edit", methods=["GET", "POST"])
@login_required
def edit_recon(rid):
    r = ReconEntry.query.get_or_404(rid)
    if request.method == "POST":
        r.category = request.form.get("category", r.category)
        r.value    = request.form.get("value", r.value).strip()
        r.notes    = request.form.get("notes", "")
        r.source   = request.form.get("source", r.source)
        db.session.commit()
        flash("Recon entry updated ✓", "success")
        return redirect(url_for("programs.detail", pid=r.program_id) + "#recon")
    return render_template("recon/form.html",
                           entry=r, categories=RECON_CATEGORIES)


# ── Recon: Delete ─────────────────────────────────────────────────────────────

@programs_bp.route("/recon/<int:rid>/delete", methods=["POST"])
@login_required
def delete_recon(rid):
    r = ReconEntry.query.get_or_404(rid)
    pid = r.program_id
    db.session.delete(r)
    db.session.commit()
    flash("Recon entry deleted.", "info")
    return redirect(url_for("programs.detail", pid=pid) + "#recon")
