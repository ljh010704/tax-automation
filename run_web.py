"""Web 版本入口"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def load_env():
    """加载 .env 文件"""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env()

from web.app import create_app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting web app on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
