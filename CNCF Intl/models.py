from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), default="Admin")
    role = db.Column(db.String(20), default="admin")
    status = db.Column(db.String(20), default="approved")
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"))
    created_at = db.Column(db.String(20))

    member = db.relationship("Member", backref="user", uselist=False)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    other_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.String(20))
    nation = db.Column(db.String(100))
    state = db.Column(db.String(100))
    area = db.Column(db.String(100))
    zone = db.Column(db.String(100))
    bethel = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    section = db.Column(db.String(20))
    role = db.Column(db.String(50))
    join_date = db.Column(db.String(20))
    address = db.Column(db.Text)
    photo = db.Column(db.String(256))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.String(20))

    @property
    def full_name(self):
        parts = [self.first_name]
        if self.other_name:
            parts.append(self.other_name)
        parts.append(self.last_name)
        return " ".join(parts)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(256))
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.String(20))
    folder = db.Column(db.String(100))
    permissions = db.Column(db.String(50), default="Standard")
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    uploaded_at = db.Column(db.String(20))

    uploader = db.relationship("User", backref="documents")


class MusicSheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    composer = db.Column(db.String(100))
    arranger = db.Column(db.String(100))
    lyrics = db.Column(db.Text)
    key = db.Column(db.String(20))
    tempo = db.Column(db.String(50))
    file = db.Column(db.String(256))
    category = db.Column(db.String(50), default="sheet_music")
    sections = db.Column(db.String(50), default="S,A,T,B")
    duration = db.Column(db.String(10), default="04:35")
    cover = db.Column(db.String(256))
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.String(20))


class ServicePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    conductor = db.Column(db.String(100))
    songs_list = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.String(20))


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50))
    recorded_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.String(20))

    recorder = db.relationship("User", backref="transactions")


class Setting(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    content = db.Column(db.Text)
    author_initials = db.Column(db.String(4))
    color = db.Column(db.String(50), default="primary")
    icon = db.Column(db.String(50), default="description")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.String(20))

    creator = db.relationship("User", backref="reports")
