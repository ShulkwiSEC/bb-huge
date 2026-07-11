"""
Background job for the "Restart Automatic Scripts" Danger Zone button.

Runs subfinder + gau against a program's tracked domain assets and imports
the results directly through the same dedup/creation helpers the
/recon/batch and /endpoints/batch REST endpoints use (app.routes.api) —
called in-process, not over HTTP, since this already runs inside the
Flask app with its own app context.

Deliberately two tools only, matching the existing bb-import-* scripts:
subfinder for subdomains, gau for endpoint URLs. No httpx/live-host
filtering, no tech-stack fingerprinting — same scope boundary as the
manual bulk-import phase.
"""

import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import db
from .models import Asset, ReconJob

SUBPROCESS_TIMEOUT = 300  # seconds, per tool invocation


def _run_tool(args, timeout=SUBPROCESS_TIMEOUT):
    """Returns (lines, error). Never raises — a missing/failing tool is a
    reportable job error, not a crash."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return [], f"{args[0]} not found in PATH"
    except subprocess.TimeoutExpired:
        return [], f"{args[0]} timed out after {timeout}s"
    except Exception as e:
        return [], f"{args[0]} failed: {e}"

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines, None


def _parse_url(url):
    parsed = urlparse(url)
    if not parsed.netloc or not parsed.scheme:
        return None
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return {
        "identifier": parsed.hostname,
        "path": path,
        "protocol": parsed.scheme if parsed.scheme in ("http", "https") else "https",
    }


def run_recon_job(app, job_id):
    """Entry point for the background thread. `app` is the real Flask app
    object (not current_app — threads outside a request need their own
    context)."""
    with app.app_context():
        from .routes.api import _import_recon_entries, _import_endpoints  # avoid import cycle

        job = ReconJob.query.get(job_id)
        if job is None:
            return

        domains = [
            a.identifier for a in Asset.query.filter_by(program_id=job.program_id, kind="domain").all()
        ]
        if not domains:
            job.status = "failed"
            job.error = "No domain assets configured — add one on the Assets tab first."
            job.finished_at = datetime.now(timezone.utc)
            db.session.commit()
            return

        log_lines = []
        tool_errors = []

        try:
            for domain in domains:
                subs, err = _run_tool(["subfinder", "-d", domain, "-silent"])
                if err:
                    tool_errors.append(err)
                else:
                    entries = [{"category": "subdomain", "value": s, "source": "subfinder"} for s in subs]
                    created, _, skipped = _import_recon_entries(job.program_id, entries)
                    asset_entries = [{"kind": "subdomain", "identifier": s, "environment": "unknown"} for s in subs]
                    _import_assets(job.program_id, asset_entries)
                    log_lines.append(
                        f"{domain}: subfinder found {len(subs)} subdomains "
                        f"({len(created)} new recon entries, {skipped} already known)"
                    )

                urls, err = _run_tool(["gau", domain, "--subs"])
                if err:
                    tool_errors.append(err)
                else:
                    endpoints = []
                    for url in urls:
                        parsed = _parse_url(url)
                        if parsed:
                            parsed["discovered_by"] = "gau"
                            endpoints.append(parsed)
                    created, _, skipped, kind_error = _import_endpoints(job.program_id, endpoints, "subdomain")
                    if kind_error:
                        tool_errors.append(kind_error)
                    else:
                        log_lines.append(
                            f"{domain}: gau found {len(urls)} URLs "
                            f"({len(created)} new endpoints, {skipped} already known)"
                        )
        except Exception as e:
            # A crash here must never leave the job stuck at status="running"
            # forever — that would silently block every future restart (see
            # the already_running guard in programs.restart_scripts) with no
            # diagnostic trail. Record what we got done before the crash and
            # report the exception as the job error.
            db.session.rollback()
            job = ReconJob.query.get(job_id)
            job.summary = "\n".join(log_lines) if log_lines else "Crashed before finishing."
            job.error = f"Unexpected error: {e}" + (f" (also: {'; '.join(tool_errors)})" if tool_errors else "")
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            db.session.commit()
            return

        job.summary = "\n".join(log_lines) if log_lines else "No new data found."
        job.error = "; ".join(tool_errors) if tool_errors else None
        job.status = "completed_with_errors" if tool_errors and log_lines else (
            "failed" if tool_errors else "completed"
        )
        job.finished_at = datetime.now(timezone.utc)
        db.session.commit()


def _import_assets(program_id, assets_data):
    """Local helper mirroring the /assets/batch dedup-by-identifier
    behavior closely enough for this job's purposes — subdomains are
    idempotent to (re)insert as assets since create_assets_batch doesn't
    dedupe by identifier itself, so we do it here to avoid piling up
    duplicate Asset rows across repeated restarts."""
    from .models import ASSET_KINDS

    existing_identifiers = {
        a.identifier for a in Asset.query.filter_by(program_id=program_id).all()
    }
    for entry in assets_data:
        identifier = (entry.get("identifier") or "").strip()
        kind = entry.get("kind", "other")
        if not identifier or kind not in ASSET_KINDS or identifier in existing_identifiers:
            continue
        existing_identifiers.add(identifier)
        db.session.add(Asset(
            program_id=program_id,
            kind=kind,
            identifier=identifier,
            environment=entry.get("environment", "unknown"),
        ))
    db.session.commit()
