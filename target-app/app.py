"""
app.py — Flask application factory for TodoApp (target application).

REST API surface
────────────────
  GET    /api/health                       Health check
  POST   /api/auth/register                Register new user
  POST   /api/auth/login                   Login → JWT token
  GET    /api/auth/me                      Current user info  [auth]
  GET    /api/tasks                        List tasks          [auth]
  POST   /api/tasks                        Create task         [auth]
  GET    /api/tasks/<id>                   Get single task     [auth]
  PUT    /api/tasks/<id>                   Update task fields  [auth]
  DELETE /api/tasks/<id>                   Delete task         [auth]
  PATCH  /api/tasks/<id>/status            Transition status   [auth]
  GET    /api/tasks/export?format=json|csv Export tasks        [auth]

Validation rules (BVA / EP test targets)
─────────────────────────────────────────
  username : 4–20 chars, pattern [a-zA-Z0-9_]+
  password : 8–32 chars
  title    : 1–100 chars
  description : 0–500 chars
  priority : low | medium | high
  due_date : YYYY-MM-DD, not in the past (on create)
  max tasks per user : 100
  max failed logins  : 5  → account locked 15 min
"""

import re
import csv
import io
import jwt as pyjwt
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g, current_app, Response
from models import db, User, Task, VALID_PRIORITIES, VALID_STATUSES, ALLOWED_TRANSITIONS
from config import Config

# Username must be 4–20 chars, alphanumeric + underscore
_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{4,20}$')


# ─── App factory ──────────────────────────────────────────────────────────────

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # ── Auth helpers (closures over `app`) ────────────────────────────────────

    def _generate_token(user_id: int) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRY_HOURS']),
            'iat': datetime.utcnow(),
        }
        return pyjwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify({'error': 'Authorization header with Bearer token required'}), 401
            token = auth[7:]
            try:
                payload = pyjwt.decode(
                    token, current_app.config['SECRET_KEY'], algorithms=['HS256']
                )
            except pyjwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except pyjwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

            user = db.session.get(User, payload['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 401
            g.current_user = user
            return f(*args, **kwargs)
        return decorated

    # ── Validation helpers ────────────────────────────────────────────────────

    def _validate_username(username: str):
        """Return error string or None."""
        if not username:
            return 'Username is required'
        if len(username) < 4:
            return 'Username must be at least 4 characters'
        if len(username) > 20:
            return 'Username must be at most 20 characters'
        if not _USERNAME_RE.match(username):
            return 'Username may only contain letters, digits, and underscores'
        return None

    def _validate_password(password: str):
        """Return error string or None."""
        if not password:
            return 'Password is required'
        if len(password) < 8:
            return 'Password must be at least 8 characters'
        if len(password) > 32:
            return 'Password must be at most 32 characters'
        return None

    def _validate_task_fields(data: dict, is_update: bool = False) -> dict:
        """Return a dict of field -> error message for all violations."""
        errors = {}

        # title
        if not is_update:
            title = (data.get('title') or '').strip()
            if not title:
                errors['title'] = 'Title is required'
            elif len(title) > 100:
                errors['title'] = 'Title must be at most 100 characters'
        elif 'title' in data:
            title = (data['title'] or '').strip()
            if not title:
                errors['title'] = 'Title cannot be empty'
            elif len(title) > 100:
                errors['title'] = 'Title must be at most 100 characters'

        # description
        if 'description' in data:
            desc = data['description'] or ''
            if len(desc) > 500:
                errors['description'] = 'Description must be at most 500 characters'

        # priority
        if 'priority' in data:
            if data['priority'] not in VALID_PRIORITIES:
                errors['priority'] = (
                    f'Priority must be one of: {", ".join(VALID_PRIORITIES)}'
                )

        # due_date
        if 'due_date' in data:
            due_str = data['due_date']
            if due_str is not None:
                try:
                    parsed = date.fromisoformat(due_str)
                    if not is_update and parsed < date.today():
                        errors['due_date'] = 'Due date cannot be in the past'
                except (ValueError, TypeError):
                    errors['due_date'] = (
                        'Due date must be a valid date in YYYY-MM-DD format'
                    )

        return errors

    # ── Routes ────────────────────────────────────────────────────────────────

    # Health ──────────────────────────────────────────────────────────────────

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200

    # Auth ────────────────────────────────────────────────────────────────────

    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password', '')

        err = _validate_username(username)
        if err:
            return jsonify({'error': err}), 422
        err = _validate_password(password)
        if err:
            return jsonify({'error': err}), 422

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = _generate_token(user.id)
        return jsonify({'user': user.to_dict(), 'token': token}), 201

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if user.is_locked():
            remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            return jsonify({
                'error': 'Account locked due to too many failed login attempts',
                'locked_minutes_remaining': remaining,
            }), 423

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= current_app.config['MAX_FAILED_LOGINS']:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=current_app.config['LOCKOUT_MINUTES']
                )
                db.session.commit()
                return jsonify({
                    'error': 'Account locked due to too many failed attempts',
                    'locked_minutes': current_app.config['LOCKOUT_MINUTES'],
                }), 423
            db.session.commit()
            return jsonify({'error': 'Invalid credentials'}), 401

        # Successful login — reset failure counter
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

        token = _generate_token(user.id)
        return jsonify({'user': user.to_dict(), 'token': token}), 200

    @app.route('/api/auth/me', methods=['GET'])
    @login_required
    def me():
        return jsonify({'user': g.current_user.to_dict()}), 200

    # Tasks ───────────────────────────────────────────────────────────────────

    @app.route('/api/tasks', methods=['GET'])
    @login_required
    def list_tasks():
        query = g.current_user.tasks

        status = request.args.get('status')
        if status:
            if status not in VALID_STATUSES:
                return jsonify({'error': f'Invalid status filter: {status}'}), 422
            query = query.filter_by(status=status)

        priority = request.args.get('priority')
        if priority:
            if priority not in VALID_PRIORITIES:
                return jsonify({'error': f'Invalid priority filter: {priority}'}), 422
            query = query.filter_by(priority=priority)

        tasks = query.order_by(Task.created_at.desc()).all()
        return jsonify({'tasks': [t.to_dict() for t in tasks], 'total': len(tasks)}), 200

    @app.route('/api/tasks', methods=['POST'])
    @login_required
    def create_task():
        task_count = g.current_user.tasks.count()
        max_tasks  = current_app.config['MAX_TASKS_PER_USER']
        if task_count >= max_tasks:
            return jsonify({'error': f'Task limit reached ({max_tasks} max)'}), 422

        data   = request.get_json(silent=True) or {}
        errors = _validate_task_fields(data)
        if errors:
            return jsonify({'errors': errors}), 422

        due_date = None
        if data.get('due_date'):
            due_date = date.fromisoformat(data['due_date'])

        task = Task(
            title=data['title'].strip(),
            description=(data.get('description') or '').strip(),
            priority=data.get('priority', 'medium'),
            due_date=due_date,
            user_id=g.current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'task': task.to_dict()}), 201

    @app.route('/api/tasks/export', methods=['GET'])
    @login_required
    def export_tasks():
        """Export all tasks as JSON (default) or CSV."""
        fmt   = request.args.get('format', 'json').lower()
        tasks = g.current_user.tasks.order_by(Task.created_at.desc()).all()

        if fmt == 'csv':
            output = io.StringIO()
            fieldnames = [
                'id', 'title', 'description', 'priority',
                'status', 'due_date', 'created_at', 'updated_at',
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for t in tasks:
                row = t.to_dict()
                writer.writerow({k: row[k] for k in fieldnames})
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=tasks.csv'},
            )

        return jsonify({'tasks': [t.to_dict() for t in tasks], 'total': len(tasks)}), 200

    @app.route('/api/tasks/<int:task_id>', methods=['GET'])
    @login_required
    def get_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify({'task': task.to_dict()}), 200

    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    @login_required
    def update_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data   = request.get_json(silent=True) or {}
        errors = _validate_task_fields(data, is_update=True)
        if errors:
            return jsonify({'errors': errors}), 422

        if 'title' in data:
            task.title = data['title'].strip()
        if 'description' in data:
            task.description = (data['description'] or '').strip()
        if 'priority' in data:
            task.priority = data['priority']
        if 'due_date' in data:
            task.due_date = (
                date.fromisoformat(data['due_date']) if data['due_date'] else None
            )
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'task': task.to_dict()}), 200

    @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
    @login_required
    def delete_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200

    @app.route('/api/tasks/<int:task_id>/status', methods=['PATCH'])
    @login_required
    def update_task_status(task_id):
        """
        Enforce the state-transition FSM.
        Returns 422 with allowed_transitions when the transition is invalid.
        """
        task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data       = request.get_json(silent=True) or {}
        new_status = data.get('status')

        if not new_status:
            return jsonify({'error': 'status field is required'}), 422
        if new_status not in VALID_STATUSES:
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUSES)}'
            }), 422

        allowed = ALLOWED_TRANSITIONS.get(task.status, set())
        if new_status not in allowed:
            return jsonify({
                'error': (
                    f'Cannot transition from "{task.status}" to "{new_status}"'
                ),
                'current_status':     task.status,
                'requested_status':   new_status,
                'allowed_transitions': sorted(allowed),
            }), 422

        task.status     = new_status
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'task': task.to_dict()}), 200

    return app


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, host='127.0.0.1', port=5000)
