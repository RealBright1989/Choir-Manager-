import os
from datetime import datetime
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Setting, Expense
from utils import generate_csrf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "choir-fixed-secret-key-2026-eton-natural")
app.config["UPLOAD_FOLDER"] = "song_uploads"
app.config["PHOTO_FOLDER"] = "member_photos"

db_url = os.environ.get("DATABASE_URL", "sqlite:///choir_web.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PHOTO_FOLDER"], exist_ok=True)

db.init_app(app)

with app.app_context():
    from utils import init_db_data, auto_backup
    db.create_all()
    auto_backup()
    init_db_data()

from blueprints.auth import bp as auth_bp
from blueprints.members import bp as members_bp
from blueprints.finance import bp as finance_bp
from blueprints.attendance import bp as attendance_bp
from blueprints.reports import bp as reports_bp
from blueprints.songs import bp as songs_bp
from blueprints.settings_bp import bp as settings_bp
from blueprints.users_bp import bp as users_bp
from blueprints.landing import bp as landing_bp
from blueprints.social import bp as social_bp
from blueprints.general import bp as general_bp
from blueprints.invoices import bp as invoices_bp
from blueprints.api import bp as api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(members_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(songs_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(users_bp)
app.register_blueprint(landing_bp)
app.register_blueprint(social_bp)
app.register_blueprint(general_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(api_bp)


@app.context_processor
def inject_globals():
    settings = {s.key: s.value for s in Setting.query.all()}
    return dict(settings=settings, now=datetime.now, csrf=generate_csrf, session=session)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
