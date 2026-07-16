"""Flask 应用工厂"""

import os
import sys
from flask import Flask
from web.auth import login_manager, auth_bp, init_auth_db


def create_app():
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请先登录"

    init_auth_db()

    from web.routes_entities import entities_bp
    from web.routes_tax import tax_bp
    from web.routes_bookkeeping import bookkeeping_bp
    from web.routes_main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(entities_bp, url_prefix="/entities")
    app.register_blueprint(tax_bp, url_prefix="/tax")
    app.register_blueprint(bookkeeping_bp, url_prefix="/bookkeeping")

    return app
