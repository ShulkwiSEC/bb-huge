from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("findings.dashboard"))

    error = None
    if request.method == "POST":
        key = request.form.get("dev_key", "").strip()
        if key == current_app.config["DEV_KEY"]:
            session.permanent = True
            session["authenticated"] = True
            next_url = _safe_next_url(request.args.get("next")) or url_for("findings.dashboard")
            return redirect(next_url)
        error = "Invalid key. Try again."

    return render_template("auth/login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def _safe_next_url(next_url):
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return None
    if not next_url.startswith("/"):
        return None
    return next_url
