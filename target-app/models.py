"""
models.py — SQLAlchemy models for TodoApp target application.

Business rules embedded here drive the test-design material:
  - Username : 4–20 chars, alphanumeric + underscore
  - Password : 8–32 chars
  - Task title       : 1–100 chars
  - Task description : 0–500 chars
  - Priority  : low | medium | high
  - Status    : pending | in_progress | completed | archived
  - State-transition table (ALLOWED_TRANSITIONS) defines the valid FSM edges
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─── Enum constants ────────────────────────────────────────────────────────────

VALID_PRIORITIES = ('low', 'medium', 'high')
VALID_STATUSES   = ('pending', 'in_progress', 'completed', 'archived')

# State-transition table — maps current_status → set of reachable next statuses
#
#   pending     → in_progress  (start work)
#   pending     → archived     (cancel before start)
#   in_progress → completed    (finish)
#   in_progress → pending      (pause / reset)
#   in_progress → archived     (abandon mid-work)
#   completed   → archived     (archive finished task)
#   archived    → (none)       TERMINAL STATE
#
# Explicitly disallowed (test-design material):
#   completed   → pending      ✗
#   completed   → in_progress  ✗
#   archived    → *            ✗

ALLOWED_TRANSITIONS: dict[str, set] = {
    'pending':      {'in_progress', 'archived'},
    'in_progress':  {'completed', 'pending', 'archived'},
    'completed':    {'archived'},
    'archived':     set(),   # terminal — no outbound transitions
}


# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    id                    = db.Column(db.Integer,  primary_key=True)
    username              = db.Column(db.String(20),  unique=True, nullable=False, index=True)
    password_hash         = db.Column(db.String(256), nullable=False)
    failed_login_attempts = db.Column(db.Integer,  default=0,    nullable=False)
    locked_until          = db.Column(db.DateTime, nullable=True)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    tasks = db.relationship(
        'Task', backref='owner', lazy='dynamic', cascade='all, delete-orphan'
    )

    # ── Password helpers ──────────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ── Lock helpers ──────────────────────────────────────────────────────────

    def is_locked(self) -> bool:
        """Return True if the account is currently under a lockout penalty."""
        return bool(self.locked_until and self.locked_until > datetime.utcnow())

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'id':         self.id,
            'username':   self.username,
            'created_at': self.created_at.isoformat(),
            'is_locked':  self.is_locked(),
            'task_count': self.tasks.count(),
        }


class Task(db.Model):
    __tablename__ = 'tasks'

    id          = db.Column(db.Integer,  primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), default='',       nullable=False)
    priority    = db.Column(db.String(10),  default='medium', nullable=False)
    status      = db.Column(db.String(20),  default='pending',nullable=False)
    due_date    = db.Column(db.Date,        nullable=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)
    updated_at  = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)
    user_id     = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'id':          self.id,
            'title':       self.title,
            'description': self.description,
            'priority':    self.priority,
            'status':      self.status,
            'due_date':    self.due_date.isoformat() if self.due_date else None,
            'created_at':  self.created_at.isoformat(),
            'updated_at':  self.updated_at.isoformat(),
            'user_id':     self.user_id,
        }
