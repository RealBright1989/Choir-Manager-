from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import login_required
from models import db, Setting

bp = Blueprint("settings_bp", __name__)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        for key in request.form:
            if key == "csrf_token":
                continue
            setting = db.session.get(Setting, key)
            if setting:
                setting.value = request.form[key]
            else:
                db.session.add(Setting(key=key, value=request.form[key]))
        db.session.commit()
        flash("Settings saved!", "success")
        return redirect(url_for("settings_bp.settings"))
    return render_template("settings.html")
