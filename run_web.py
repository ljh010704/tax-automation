"""Web ??????"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from web.app import create_app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting web app on port {port} (debug={debug})")
    # threaded=True: handles multiple users concurrently, low memory footprint
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
