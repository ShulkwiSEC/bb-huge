from datetime import datetime, timezone
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

SEVERITY_COLORS = {
    "critical": "red",
    "high":     "orange",
    "medium":   "yellow",
    "low":      "blue",
    "informational": "gray",
}

STATUS_COLORS = {
    "discovered": "gray",
    "debugging":  "orange",
    "confirmed":  "teal",
    "reported":   "purple",
    "rewarded":   "green",
    "denied":     "red",
    "duplicate":  "gray",
    "n/a":        "gray",
}


class Finding(db.Model):
    __tablename__ = "findings"

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(300), nullable=False)
    target      = db.Column(db.String(300), nullable=False)        # domain / program name
    platform    = db.Column(db.String(100), nullable=False, default="private")  # HackerOne, Bugcrowd…
    severity    = db.Column(db.String(20),  nullable=False, default="medium")
    status      = db.Column(db.String(20),  nullable=False, default="discovered")
    agent       = db.Column(db.String(50),  nullable=False, default="manual")
    cwe         = db.Column(db.String(50),  nullable=True)         # e.g. CWE-79
    cvss        = db.Column(db.Float,       nullable=True)         # e.g. 8.5
    description = db.Column(db.Text,        nullable=False, default="")
    poc         = db.Column(db.Text,        nullable=False, default="")
    created_at  = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    attachments = db.relationship("Attachment", backref="finding",
                                  lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":          self.id,
            "title":       self.title,
            "target":      self.target,
            "platform":    self.platform,
            "severity":    self.severity,
            "status":      self.status,
            "agent":       self.agent,
            "cwe":         self.cwe,
            "cvss":        self.cvss,
            "description": self.description,
            "poc":         self.poc,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
            "attachments": [a.to_dict() for a in self.attachments],
        }


class Attachment(db.Model):
    __tablename__ = "attachments"

    id          = db.Column(db.Integer, primary_key=True)
    finding_id  = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    filename    = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    path        = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":            self.id,
            "finding_id":    self.finding_id,
            "filename":      self.filename,
            "original_name": self.original_name,
            "path":          self.path,
            "uploaded_at":   self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
