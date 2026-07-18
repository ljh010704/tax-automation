"""用户认证模块"""

import sqlite3
import os
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from web.csrf import csrf_required


# ======== 用户模型 ========

class User(UserMixin):
    def __init__(self, id, username, role="user"):
        self.id = id
        self.username = username
        self.role = role

    @property
    def is_admin(self):
        return self.role == "admin"


# ======== 数据库操作 ========

DB_PATH = os.environ.get('WEB_DATABASE_PATH', os.path.join(os.path.dirname(__file__), "..", "data", "web.db"))


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
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_user(username, password, role="user"):
    """Create a new user with Werkzeug password hashing (PBKDF2-SHA256)."""
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    """Verify user credentials. Supports migration from old SHA-256 hashes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None:
        return None

    stored_hash = row["password_hash"]

    # Modern Werkzeug hash (pbkdf2:sha256$...)
    if stored_hash.startswith('pbkdf2:'):
        if check_password_hash(stored_hash, password):
            return User(row["id"], row["username"], row["role"])
        return None

    # Legacy SHA-256 hash (64 hex chars) - verify and upgrade
    if len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash.lower()):
        import hashlib
        # Check if there was a salt column in old schema
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            salt_row = conn.execute("SELECT salt FROM users WHERE id = ?", (row["id"],)).fetchone()
            salt = salt_row["salt"] if salt_row and salt_row["salt"] else ''
        except (sqlite3.OperationalError, TypeError):
            salt = ''
        conn.close()

        legacy_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        if legacy_hash == stored_hash:
            # Upgrade to modern hashing on successful login
            new_hash = generate_password_hash(password, method='pbkdf2:sha256')
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row["id"]))
            conn.commit()
            conn.close()
            return User(row["id"], row["username"], row["role"])
        return None

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


# ======== Flask 认证 ========

login_manager = LoginManager()
auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))


# ======== 路由 ========

@auth_bp.route("/login", methods=["GET", "POST"])
@csrf_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_user(username, password)
        if user:
            login_user(user, remember=True)
            return redirect(url_for("main.dashboard"))
        flash("用户名或密码错误", "error")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@csrf_required
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password_confirm", "")
        if not username or not password:
            flash("用户名和密码不能为空", "error")
        elif password != password2:
            flash("两次密码不一致", "error")
        elif len(password) < 6:
            flash("密码至少 6 位", "error")
        elif create_user(username, password):
            flash("注册成功，请登录", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("用户名已存在", "error")
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
            flash("需要管理员权限", "error")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated
