from app import create_app
from waitress import serve
import logging
import os

app = create_app()

# DEBUG frontend/template auto reload
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

# disable static cache in debug
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))

    if os.environ.get("FLASK_DEBUG") == "1":
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        logging.getLogger("waitress").setLevel(logging.INFO)
        serve(
            app,
            host="0.0.0.0",
            port=port,
            threads=4,
        )
