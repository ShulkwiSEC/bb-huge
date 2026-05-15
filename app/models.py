from datetime import datetime, timezone
import json
from . import db


SEVERITIES = ["critical", "high", "medium", "low", "informational"]

STATUSES = [
    "discovered",
    "debugging",
    "confirmed",
    "reported",
    "rewarded",
    "denied",
    "duplicate",
    "n/a",
]

AGENTS = [
    "gemini-cli",
    "claude-code",
    "claude",
    "codex",
    "emmu",
    "manual",
    "other",
]

PLATFORMS = [
    "HackerOne",
    "Bugcrowd",
    "Intigriti",
    "YesWeHack",
    "Synack",
    "private",
    "other",
]

RECON_CATEGORIES = [
    "subdomain",
    "endpoint",
    "technology",
    "parameter",
    "credential",
    "ip",
    "other",
]

WEBHOOK_EVENTS = [
    "finding.created",
    "finding.confirmed",
    "finding.reported",
    "finding.rewarded",
    "finding.denied",
    "finding.status_changed",
    "recon.added",
]

SEVERITY_COLORS = {
    "critical": "red",
    "high": "orange",
    "medium": "yellow",
    "low": "blue",
    "informational": "gray",
}

STATUS_COLORS = {
    "discovered": "gray",
    "debugging": "orange",
    "confirmed": "teal",
    "reported": "purple",
    "rewarded": "green",
    "denied": "red",
    "duplicate": "gray",
    "n/a": "gray",
}


# ── Program ───────────────────────────────────────────────────────────────────


class Program(db.Model):
    __tablename__ = "programs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    platform = db.Column(db.String(100), nullable=False, default="private")
    program_url = db.Column(db.String(500), nullable=True)  # link to program page
    scope_in = db.Column(db.Text, nullable=False, default="")  # Markdown — in-scope
    scope_out = db.Column(
        db.Text, nullable=False, default=""
    )  # Markdown — out-of-scope
    notes = db.Column(db.Text, nullable=False, default="")  # general notes
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    findings = db.relationship("Finding", backref="program", lazy=True)
    recon = db.relationship(
        "ReconEntry", backref="program", lazy=True, cascade="all, delete-orphan"
    )

    def stats(self):
        sev = {s: 0 for s in SEVERITIES}
        sta = {s: 0 for s in STATUSES}
        for f in self.findings:
            sev[f.severity] = sev.get(f.severity, 0) + 1
            sta[f.status] = sta.get(f.status, 0) + 1
        return {"total": len(self.findings), "by_severity": sev, "by_status": sta}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "program_url": self.program_url,
            "scope_in": self.scope_in,
            "scope_out": self.scope_out,
            "notes": self.notes,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "stats": self.stats(),
        }


# ── ReconEntry ────────────────────────────────────────────────────────────────


class ReconEntry(db.Model):
    __tablename__ = "recon_entries"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="subdomain")
    value = db.Column(db.String(500), nullable=False)  # the actual data
    notes = db.Column(db.Text, nullable=False, default="")
    source = db.Column(db.String(100), nullable=True)  # tool/agent that found it
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "category": self.category,
            "value": self.value,
            "notes": self.notes,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Note (per-finding activity log) ──────────────────────────────────────────


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    agent = db.Column(db.String(50), nullable=False, default="manual")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "content": self.content,
            "agent": self.agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── TargetContext (pre-hunt Q&A data) ─────────────────────────────────────────


class TargetContext(db.Model):
    __tablename__ = "target_contexts"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(
        db.Integer, db.ForeignKey("programs.id"), nullable=False, unique=True
    )
    _data = db.Column("data", db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    program = db.relationship(
        "Program", backref=db.backref("target_context", uselist=False)
    )

    @property
    def data(self):
        try:
            return json.loads(self._data)
        except:
            return {}

    @data.setter
    def data(self, val):
        self._data = json.dumps(val)

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── WebhookConfig ─────────────────────────────────────────────────────────────


class WebhookConfig(db.Model):
    __tablename__ = "webhook_configs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # display label
    wtype = db.Column(db.String(20), nullable=False)  # "discord" | "telegram"
    # Discord: webhook URL.  Telegram: bot token
    url_or_token = db.Column(db.String(500), nullable=False)
    chat_id = db.Column(db.String(100), nullable=True)  # Telegram chat_id
    _events = db.Column("events", db.Text, nullable=False, default="[]")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def events(self):
        try:
            return json.loads(self._events)
        except:
            return []

    @events.setter
    def events(self, val):
        self._events = json.dumps(val if isinstance(val, list) else [])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "wtype": self.wtype,
            "chat_id": self.chat_id,
            "events": self.events,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Finding ───────────────────────────────────────────────────────────────────


class Finding(db.Model):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=True)
    title = db.Column(db.String(300), nullable=False)
    target = db.Column(db.String(300), nullable=False)
    platform = db.Column(db.String(100), nullable=False, default="private")
    severity = db.Column(db.String(20), nullable=False, default="medium")
    status = db.Column(db.String(20), nullable=False, default="discovered")
    agent = db.Column(db.String(50), nullable=False, default="manual")
    cwe = db.Column(db.String(50), nullable=True)
    cvss = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=False, default="")
    poc = db.Column(db.Text, nullable=False, default="")
    _tags = db.Column("tags", db.Text, nullable=False, default="[]")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    attachments = db.relationship(
        "Attachment", backref="finding", lazy=True, cascade="all, delete-orphan"
    )
    notes = db.relationship(
        "Note",
        backref="finding",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Note.created_at",
    )

    @property
    def tags(self):
        try:
            return json.loads(self._tags)
        except:
            return []

    @tags.setter
    def tags(self, val):
        if isinstance(val, str):
            val = [t.strip() for t in val.split(",") if t.strip()]
        self._tags = json.dumps(val)

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "title": self.title,
            "target": self.target,
            "platform": self.platform,
            "severity": self.severity,
            "status": self.status,
            "agent": self.agent,
            "cwe": self.cwe,
            "cvss": self.cvss,
            "description": self.description,
            "poc": self.poc,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "attachments": [a.to_dict() for a in self.attachments],
            "notes": [n.to_dict() for n in self.notes],
        }


# ── Attachment ────────────────────────────────────────────────────────────────


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "path": self.path,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
