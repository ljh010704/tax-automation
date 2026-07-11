"""??????"""

import sqlite3
import os
import hashlib
import secrets
from functools import wraps
from flask import Flask, Blueprint, render_template, redirect, url_for, request, flash, session, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


# ======== ???? ========

class User(UserMixin):
    def __init__(self, id, username, role="user"):
        self.id = id
        self.username = username
        self.role = role

    @property
    def is_admin(self):
        return self.role == "admin"


# ======== ????? ========

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "web.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_auth_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

def create_user(username, password, role="user"):
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, salt, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None:
        return None
    password_hash = _hash_password(password, row["salt"])
    if password_hash == row["password_hash"]:
        return User(row["id"], row["username"], row["role"])
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row:
        return User(row["id"], row["username"], row["role"])
    return None

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ======== Flask ?? ========

login_manager = LoginManager()
auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))


# ======== ?? ========

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_user(username, password)
        if user:
            login_user(user, remember=True)
            return redirect(url_for("main.dashboard"))
        flash("????????", "error")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if not username or not password:
            flash("??????????", "error")
        elif password != password2:
            flash("???????", "error")
        elif len(password) < 6:
            flash("???? 6 ?", "error")
        elif create_user(username, password):
            flash("????????", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("??????", "error")
    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("???????", "error")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated
