from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app(config_object="config.Config"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # Ensure instance and uploads folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # Register blueprints
    from .routes.auth     import auth_bp
    from .routes.findings import findings_bp
    from .routes.api      import api_bp
    from .routes.programs import programs_bp
    from .routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(findings_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(programs_bp)
    app.register_blueprint(settings_bp)

    # Jinja helpers
    from .models import SEVERITY_COLORS, STATUS_COLORS
    app.jinja_env.globals.update(
        severity_color=lambda s: SEVERITY_COLORS.get(s, "gray"),
        status_color=lambda s:   STATUS_COLORS.get(s, "gray"),
    )

    with app.app_context():
        db.create_all()

    return app
