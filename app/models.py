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

ASSET_KINDS = [
    "domain",
    "subdomain",
    "api_host",
    "mobile_app",
    "binary",
    "source_repo",
    "repo",
    "other",
]

ASSET_ENVIRONMENTS = ["prod", "staging", "dev", "test", "unknown"]

FIELDS = ["binary", "mobile", "source_code", "web"]

ENDPOINT_PROTOCOLS = ["http", "https", "graphql", "ws", "wss", "other"]

CONFIDENCE_LEVELS = ["low", "medium", "high"]

OBSERVATION_CATEGORIES = [
    "behavior",
    "auth",
    "access_control",
    "input_handling",
    "business_logic",
    "rate_limit",
    "recon",
    "other",
]

OBSERVATION_STATUSES = ["open", "testing", "closed", "promoted"]

HYPOTHESIS_STATUSES = [
    "open",
    "testing",
    "confirmed",
    "rejected",
    "duplicate",
    "promoted",
]

EVIDENCE_TYPES = [
    "http_exchange",
    "graphql_query",
    "note",
    "screenshot",
    "file",
    "repro_step",
    "environment",
    "credential_context",
    "mobile_static_analysis",
    "mobile_dynamic_analysis",
    "mobile_network_traffic",
    "binary_analysis_output",
    "binary_ioc",
    "binary_exploit",
    "source_code_vulnerability",
    "source_code_scan",
    "source_code_review_note",
    "other",
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


def _now():
    return datetime.now(timezone.utc)


def _load_json(value, default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def _dump_json(value, default):
    if value is None:
        value = default
    return json.dumps(value)


class Program(db.Model):
    __tablename__ = "programs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    platform = db.Column(db.String(100), nullable=False, default="private")
    program_url = db.Column(db.String(500), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    scope_in = db.Column(db.Text, nullable=False, default="")
    scope_out = db.Column(db.Text, nullable=False, default="")
    notes = db.Column(db.Text, nullable=False, default="")
    field = db.Column(db.String(20), nullable=False, default="web")
    summary = db.Column(db.Text, nullable=False, default="")
    auto_brief = db.Column(db.Text, nullable=False, default="")
    _tech_stack = db.Column("tech_stack", db.Text, nullable=False, default="[]")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    @property
    def tech_stack(self):
        return _load_json(self._tech_stack, [])

    @tech_stack.setter
    def tech_stack(self, value):
        if value is None:
            value = []
        elif isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        self._tech_stack = _dump_json(value, [])

    findings = db.relationship("Finding", backref="program", lazy=True)
    recon = db.relationship(
        "ReconEntry", backref="program", lazy=True, cascade="all, delete-orphan"
    )
    observations = db.relationship(
        "Observation", backref="program", lazy=True, cascade="all, delete-orphan"
    )
    hypotheses = db.relationship(
        "Hypothesis", backref="program", lazy=True, cascade="all, delete-orphan"
    )
    evidence_records = db.relationship(
        "EvidenceRecord", backref="program", lazy=True, cascade="all, delete-orphan"
    )

    def stats(self):
        sev = {s: 0 for s in SEVERITIES}
        sta = {s: 0 for s in STATUSES}
        for finding in self.findings:
            sev[finding.severity] = sev.get(finding.severity, 0) + 1
            sta[finding.status] = sta.get(finding.status, 0) + 1
        return {"total": len(self.findings), "by_severity": sev, "by_status": sta}

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "program_url": self.program_url,
            "logo_url": self.logo_url,
            "scope_in": self.scope_in,
            "scope_out": self.scope_out,
            "notes": self.notes,
            "field": self.field,
            "summary": self.summary,
            "auto_brief": self.auto_brief,
            "tech_stack": self.tech_stack,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "stats": self.stats(),
        }


class ReconEntry(db.Model):
    __tablename__ = "recon_entries"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="subdomain")
    value = db.Column(db.String(500), nullable=False)
    notes = db.Column(db.Text, nullable=False, default="")
    source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

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


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    agent = db.Column(db.String(50), nullable=False, default="manual")
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "content": self.content,
            "agent": self.agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TargetContext(db.Model):
    __tablename__ = "target_contexts"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(
        db.Integer, db.ForeignKey("programs.id"), nullable=False, unique=True
    )
    _data = db.Column("data", db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    # When a Program is deleted we want the associated TargetContext removed
    # as well instead of SQLAlchemy attempting to null the foreign key which
    # would violate the NOT NULL constraint. Add cascade so the TargetContext
    # is deleted together with its Program.
    program = db.relationship(
        "Program",
        backref=db.backref("target_context", uselist=False, cascade="all, delete-orphan"),
    )

    @property
    def data(self):
        return _load_json(self._data, {})

    @data.setter
    def data(self, value):
        self._data = _dump_json(value, {})

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WebhookConfig(db.Model):
    __tablename__ = "webhook_configs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wtype = db.Column(db.String(20), nullable=False)
    url_or_token = db.Column(db.String(500), nullable=False)
    chat_id = db.Column(db.String(100), nullable=True)
    _events = db.Column("events", db.Text, nullable=False, default="[]")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_now)

    @property
    def events(self):
        return _load_json(self._events, [])

    @events.setter
    def events(self, value):
        self._events = _dump_json(value if isinstance(value, list) else [], [])

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


class Observation(db.Model):
    __tablename__ = "observations"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text, nullable=False, default="")
    category = db.Column(db.String(50), nullable=False, default="other")
    status = db.Column(db.String(20), nullable=False, default="open")
    agent = db.Column(db.String(50), nullable=False, default="manual")
    source_tool = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.String(20), nullable=False, default="medium")
    claimed_by = db.Column(db.String(50), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    evidence_records = db.relationship(
        "EvidenceRecord",
        backref="observation",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="EvidenceRecord.created_at.desc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "status": self.status,
            "agent": self.agent,
            "source_tool": self.source_tool,
            "confidence": self.confidence,
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Hypothesis(db.Model):
    __tablename__ = "hypotheses"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    observation_id = db.Column(
        db.Integer, db.ForeignKey("observations.id"), nullable=True
    )
    title = db.Column(db.String(300), nullable=False)
    weakness_hint = db.Column(db.String(200), nullable=True)
    cwe = db.Column(db.String(50), nullable=True)
    severity_hint = db.Column(db.String(20), nullable=True)
    attack_path = db.Column(db.Text, nullable=False, default="")
    impact_hypothesis = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="open")
    agent = db.Column(db.String(50), nullable=False, default="manual")
    confidence = db.Column(db.String(20), nullable=False, default="medium")
    claimed_by = db.Column(db.String(50), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    observation = db.relationship(
        "Observation", backref=db.backref("hypotheses", lazy=True)
    )
    evidence_records = db.relationship(
        "EvidenceRecord",
        backref="hypothesis",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="EvidenceRecord.created_at.desc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "observation_id": self.observation_id,
            "title": self.title,
            "weakness_hint": self.weakness_hint,
            "cwe": self.cwe,
            "severity_hint": self.severity_hint,
            "attack_path": self.attack_path,
            "impact_hypothesis": self.impact_hypothesis,
            "status": self.status,
            "agent": self.agent,
            "confidence": self.confidence,
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Finding(db.Model):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=True)
    hypothesis_id = db.Column(
        db.Integer, db.ForeignKey("hypotheses.id"), nullable=True
    )
    title = db.Column(db.String(300), nullable=False)
    target = db.Column(db.String(300), nullable=False)
    platform = db.Column(db.String(100), nullable=False, default="private")
    field = db.Column(db.String(20), nullable=False, default="web")
    severity = db.Column(db.String(20), nullable=False, default="medium")
    status = db.Column(db.String(20), nullable=False, default="discovered")
    agent = db.Column(db.String(50), nullable=False, default="manual")
    cwe = db.Column(db.String(50), nullable=True)
    cvss = db.Column(db.Float, nullable=True)
    confidence = db.Column(db.String(20), nullable=False, default="high")
    description = db.Column(db.Text, nullable=False, default="")
    poc = db.Column(db.Text, nullable=False, default="")
    _tags = db.Column("tags", db.Text, nullable=False, default="[]")
    _related_finding_ids = db.Column("related_finding_ids", db.Text, nullable=False, default="[]")
    claimed_by = db.Column(db.String(50), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    hypothesis = db.relationship(
        "Hypothesis", backref=db.backref("findings", lazy=True)
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
    evidence_records = db.relationship(
        "EvidenceRecord",
        backref="finding",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="EvidenceRecord.created_at.desc()",
    )

    @property
    def tags(self):
        return _load_json(self._tags, [])

    @tags.setter
    def tags(self, value):
        if isinstance(value, str):
            value = [tag.strip() for tag in value.split(",") if tag.strip()]
        self._tags = _dump_json(value, [])

    @property
    def related_finding_ids(self):
        return _load_json(self._related_finding_ids, [])

    @related_finding_ids.setter
    def related_finding_ids(self, value):
        self._related_finding_ids = _dump_json(value if isinstance(value, list) else [], [])

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "target": self.target,
            "platform": self.platform,
            "field": self.field,
            "severity": self.severity,
            "status": self.status,
            "agent": self.agent,
            "cwe": self.cwe,
            "cvss": self.cvss,
            "confidence": self.confidence,
            "description": self.description,
            "poc": self.poc,
            "tags": self.tags,
            "related_finding_ids": self.related_finding_ids,
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "notes": [note.to_dict() for note in self.notes],
            "evidence_records": [
                evidence.to_dict() for evidence in self.evidence_records
            ],
        }


class EvidenceRecord(db.Model):
    __tablename__ = "evidence_records"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=True)
    hypothesis_id = db.Column(db.Integer, db.ForeignKey("hypotheses.id"), nullable=True)
    observation_id = db.Column(db.Integer, db.ForeignKey("observations.id"), nullable=True)
    evidence_type = db.Column(db.String(50), nullable=False, default="other")
    title = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text, nullable=False, default="")
    request_method = db.Column(db.String(20), nullable=True)
    request_url = db.Column(db.String(1000), nullable=True)
    request_headers_json = db.Column(db.Text, nullable=True)
    request_body_text = db.Column(db.Text, nullable=True)
    response_status = db.Column(db.Integer, nullable=True)
    response_headers_json = db.Column(db.Text, nullable=True)
    response_body_text = db.Column(db.Text, nullable=True)
    account_label = db.Column(db.String(100), nullable=True)
    auth_type = db.Column(db.String(100), nullable=True)
    source_tool = db.Column(db.String(100), nullable=True)
    occurred_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "finding_id": self.finding_id,
            "hypothesis_id": self.hypothesis_id,
            "observation_id": self.observation_id,
            "evidence_type": self.evidence_type,
            "title": self.title,
            "summary": self.summary,
            "request_method": self.request_method,
            "request_url": self.request_url,
            "request_headers": _load_json(self.request_headers_json, None),
            "request_body_text": self.request_body_text,
            "response_status": self.response_status,
            "response_headers": _load_json(self.response_headers_json, None),
            "response_body_text": self.response_body_text,
            "account_label": self.account_label,
            "auth_type": self.auth_type,
            "source_tool": self.source_tool,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    kind = db.Column(db.String(50), nullable=False, default="other")
    identifier = db.Column(db.String(500), nullable=False)
    environment = db.Column(db.String(20), nullable=False, default="unknown")
    notes = db.Column(db.Text, nullable=False, default="")
    active = db.Column(db.Boolean, nullable=False, default=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    deprecated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    program = db.relationship("Program", backref=db.backref("assets", lazy=True, cascade="all, delete-orphan"))
    endpoints = db.relationship(
        "Endpoint", backref="asset", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "kind": self.kind,
            "identifier": self.identifier,
            "environment": self.environment,
            "notes": self.notes,
            "active": self.active,
            "version": self.version,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Endpoint(db.Model):
    __tablename__ = "endpoints"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    method = db.Column(db.String(20), nullable=False, default="GET")
    path = db.Column(db.String(1000), nullable=False)
    protocol = db.Column(db.String(20), nullable=False, default="https")
    content_type = db.Column(db.String(100), nullable=True)
    auth_required = db.Column(db.Boolean, nullable=True)
    discovered_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "method": self.method,
            "path": self.path,
            "protocol": self.protocol,
            "content_type": self.content_type,
            "auth_required": self.auth_required,
            "discovered_by": self.discovered_by,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "filename": self.filename,
            "original_name": self.original_name,
            "path": self.path,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class Credential(db.Model):
    __tablename__ = "credentials"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    credential_type = db.Column(db.String(50), nullable=False, default="password")
    username_encrypted = db.Column(db.Text, nullable=True)
    secret_encrypted = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=False, default="")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    program = db.relationship("Program", backref=db.backref("credentials", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self, include_secret=False):
        result = {
            "id": self.id,
            "program_id": self.program_id,
            "label": self.label,
            "credential_type": self.credential_type,
            "url": self.url,
            "notes": self.notes,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_secret:
            result["username_encrypted"] = self.username_encrypted
            result["secret_encrypted"] = self.secret_encrypted
        return result


AUTH_SESSION_TYPES = ["cookie", "bearer", "custom_header", "mixed"]
AUTH_SESSION_STATUSES = ["active", "expired", "invalid"]


class AuthSession(db.Model):
    """A captured, reusable authenticated session (cookies/headers) for a
    program + identity label. Populated by the HAR importer once someone
    logs in via a real browser; consumed by any agent via bb_get_session
    so it never has to handle login/MFA/CSRF itself."""

    __tablename__ = "auth_sessions"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    label = db.Column(db.String(100), nullable=False, default="default")
    base_url = db.Column(db.String(500), nullable=True)
    auth_type = db.Column(db.String(50), nullable=False, default="cookie")
    cookies_encrypted = db.Column(db.Text, nullable=True)
    headers_encrypted = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    captured_by = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(50), nullable=False, default="har_import")
    captured_at = db.Column(db.DateTime, default=_now)
    expires_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    program = db.relationship("Program", backref=db.backref("auth_sessions", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self, include_secret=False):
        result = {
            "id": self.id,
            "program_id": self.program_id,
            "label": self.label,
            "base_url": self.base_url,
            "auth_type": self.auth_type,
            "status": self.status,
            "captured_by": self.captured_by,
            "source": self.source,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_secret:
            result["cookies"] = _load_json(self.cookies_encrypted, None)
            result["headers"] = _load_json(self.headers_encrypted, None)
        return result


RECON_JOB_STATUSES = ["running", "completed", "completed_with_errors", "failed"]


class ReconJob(db.Model):
    """One row per 'Restart Automatic Scripts' run — tracks the background
    subfinder/gau pipeline triggered from the program Danger Zone. Only one
    running job per program is allowed at a time (enforced in the route,
    not here)."""

    __tablename__ = "recon_jobs"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="running")
    triggered_by = db.Column(db.String(100), nullable=True)
    summary = db.Column(db.Text, nullable=False, default="")
    error = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=_now)
    finished_at = db.Column(db.DateTime, nullable=True)

    program = db.relationship("Program", backref=db.backref("recon_jobs", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "status": self.status,
            "triggered_by": self.triggered_by,
            "summary": self.summary,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class ReportDraft(db.Model):
    __tablename__ = "report_drafts"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    title = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=False, default="")
    poc = db.Column(db.Text, nullable=False, default="")
    summary = db.Column(db.Text, nullable=False, default="")
    impact = db.Column(db.Text, nullable=False, default="")
    cwe = db.Column(db.String(50), nullable=True)
    cvss = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    finding = db.relationship("Finding", backref=db.backref("report_drafts", lazy=True, cascade="all, delete-orphan",
                                                            order_by="ReportDraft.version.desc()"))

    def to_dict(self):
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "poc": self.poc,
            "summary": self.summary,
            "impact": self.impact,
            "cwe": self.cwe,
            "cvss": self.cvss,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AlertRule(db.Model):
    __tablename__ = "alert_rules"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    trigger_event = db.Column(db.String(100), nullable=False)
    filter_expression = db.Column(db.Text, nullable=False, default="")
    webhook_url = db.Column(db.Text, nullable=True)
    discord_channel = db.Column(db.String(200), nullable=True)
    telegram_chat_id = db.Column(db.String(100), nullable=True)
    slack_webhook_url = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    last_fired_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    program = db.relationship("Program", backref=db.backref("alert_rules", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "program_id": self.program_id,
            "name": self.name,
            "trigger_event": self.trigger_event,
            "filter_expression": self.filter_expression,
            "webhook_url": self.webhook_url,
            "discord_channel": self.discord_channel,
            "telegram_chat_id": self.telegram_chat_id,
            "slack_webhook_url": self.slack_webhook_url,
            "active": self.active,
            "last_fired_at": self.last_fired_at.isoformat() if self.last_fired_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
