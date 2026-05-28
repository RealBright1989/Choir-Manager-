from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin")
    created_at = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120))


class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    other_names = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    section = db.Column(db.String(50), nullable=False, default="Soprano")
    join_date = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    dob = db.Column(db.String(10))
    state_of_origin = db.Column(db.String(100))
    lga = db.Column(db.String(100))
    nin_number = db.Column(db.String(20))
    academic_qualification = db.Column(db.String(100))
    country = db.Column(db.String(100))
    passport_number = db.Column(db.String(50))
    photo = db.Column(db.String(200))
    zone = db.Column(db.String(100))
    area = db.Column(db.String(100))
    payments = db.relationship("Payment", backref="member", lazy="dynamic", cascade="all, delete-orphan")
    attendance_records = db.relationship("Attendance", backref="member", lazy="dynamic", cascade="all, delete-orphan")


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"))
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.String(10), nullable=False)
    payment_for = db.Column(db.String(200))
    notes = db.Column(db.Text)


class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    issue_date = db.Column(db.String(10), nullable=False)
    due_date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="unpaid")
    subtotal = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, nullable=False, default=0)
    paid_amount = db.Column(db.Float, nullable=False, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.String(19), nullable=False)

    member = db.relationship("Member", backref="invoices")
    items = db.relationship("InvoiceItem", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Present")
    notes = db.Column(db.Text)


class Song(db.Model):
    __tablename__ = "songs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    composer = db.Column(db.String(200))
    lyrics = db.Column(db.Text)
    audio_file = db.Column(db.String(200))
    upload_date = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text)


class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)


class PhoneVerification(db.Model):
    __tablename__ = "phone_verifications"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    otp = db.Column(db.String(10), nullable=False)
    verified = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(19), nullable=False)
    expires_at = db.Column(db.String(19), nullable=False)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.String(19), nullable=False)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.String(19), nullable=False)
    expires_at = db.Column(db.String(19), nullable=False)
    used = db.Column(db.Integer, default=0)


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.String(19), nullable=False)
