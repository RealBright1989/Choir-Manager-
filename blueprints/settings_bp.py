from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import login_required, validate_csrf, log_audit
from models import db, Setting

bp = Blueprint("settings_bp", __name__)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("settings_bp.settings"))
        for key in ["choir_name", "currency", "dues_amount", "facebook_url", "youtube_url", "instagram_url",
                     "tiktok_url", "sms_provider", "twilio_account_sid", "twilio_auth_token", "twilio_phone",
                     "smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from"]:
            val = request.form.get(key, "").strip()
            s = db.session.get(Setting, key)
            if s:
                s.value = val
            else:
                db.session.add(Setting(key=key, value=val))
        db.session.commit()
        log_audit("update", "settings", 0, "Settings updated")
        flash("Settings saved!", "success")
        return redirect(url_for("settings_bp.settings"))
    all_settings = {s.key: s.value for s in Setting.query.all()}
    return render_template("settings.html", settings_data=all_settings)
