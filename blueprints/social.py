from flask import Blueprint, render_template
from utils import login_required
from models import db, Setting

bp = Blueprint("social", __name__)


@bp.route("/social")
@login_required
def social():
    keys = ["facebook_url", "youtube_url", "instagram_url", "tiktok_url"]
    links = {}
    for k in keys:
        s = db.session.get(Setting, k)
        if s:
            links[k] = s.value
    return render_template("social.html", links=links)
