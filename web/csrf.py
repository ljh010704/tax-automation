"""CSRF Protection Module"""
import secrets
from functools import wraps
from flask import session, request, abort


def generate_csrf_token():
    """Generate and store a CSRF token in the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token):
    """Validate a submitted CSRF token against the session."""
    expected = session.get('_csrf_token')
    if not expected or not token:
        return False
    return secrets.compare_digest(expected, token)


def csrf_required(f):
    """Decorator that requires a valid CSRF token for POST requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not validate_csrf_token(token):
                abort(403, description='CSRF token missing or invalid')
        return f(*args, **kwargs)
    return decorated_function
