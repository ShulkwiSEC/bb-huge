from datetime import datetime, timezone
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash)
from .. import db
from ..models import Program, Finding, ReconEntry, PLATFORMS, RECON_CATEGORIES, SEVERITIES, STATUSES
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

    # Group recon by category
    recon_grouped = {}
    for r in recon:
        recon_grouped.setdefault(r.category, []).append(r)

    return render_template(
        "programs/detail.html",
        program=program,
        findings=findings,
        recon_grouped=recon_grouped,
        recon_categories=RECON_CATEGORIES,
        severities=SEVERITIES,
        statuses=STATUSES,
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
