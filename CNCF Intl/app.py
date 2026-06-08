import os
from datetime import datetime
from flask import Flask, session
from models import db, User, Setting
from utils import generate_csrf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cncf-sovereign-secret-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cncf_choir.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(os.path.join(app.root_path, app.config["UPLOAD_FOLDER"]), exist_ok=True)

db.init_app(app)

with app.app_context():
    from werkzeug.security import generate_password_hash
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            display_name="Admin Director",
            role="admin",
            created_at=datetime.now().strftime("%Y-%m-%d")
        ))
        db.session.commit()
    if not Setting.query.filter_by(key="org_name").first():
        db.session.add(Setting(key="org_name", value="BCS CNCF International"))
        db.session.commit()

from blueprints.auth import bp as auth_bp
from blueprints.general import bp as general_bp
from blueprints.members import bp as members_bp
from blueprints.documents import bp as documents_bp
from blueprints.music import bp as music_bp
from blueprints.services import bp as services_bp
from blueprints.finance import bp as finance_bp
from blueprints.settings_bp import bp as settings_bp
from blueprints.reports import bp as reports_bp

app.register_blueprint(auth_bp)
app.register_blueprint(general_bp)
app.register_blueprint(members_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(music_bp)
app.register_blueprint(services_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(reports_bp)


@app.context_processor
def inject_globals():
    settings = {s.key: s.value for s in Setting.query.all()}
    return dict(settings=settings, now=datetime.now, csrf=generate_csrf, session=session)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(debug=True, host="0.0.0.0", port=port)
