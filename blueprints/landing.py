from flask import Blueprint, render_template
from models import db, Setting

bp = Blueprint("landing", __name__)


@bp.route("/")
def landing():
    keys = ["facebook_url", "youtube_url", "instagram_url", "tiktok_url"]
    social_links = {}
    for k in keys:
        s = db.session.get(Setting, k)
        if s:
            social_links[k] = s.value
    return render_template("landing.html", social_links=social_links)


@bp.route("/join/guidelines")
def join_guidelines():
    return render_template("join_guidelines.html")


@bp.route("/user-manual")
def user_manual():
    return render_template("user_manual.html")


@bp.route("/terms")
def terms():
    return render_template("terms.html")
