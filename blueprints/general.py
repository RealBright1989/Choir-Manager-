from datetime import datetime
from flask import Blueprint, render_template, request
from utils import login_required, generate_csrf, session
from models import db, Member, Payment, Attendance, Song, AuditLog

bp = Blueprint("general", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    total_members = Member.query.count()
    total_payments = Payment.query.count()
    total_revenue = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar()
    total_present = Attendance.query.filter_by(status="Present").count()
    total_attendance = Attendance.query.count()
    attendance_rate = round((total_present / total_attendance * 100) if total_attendance > 0 else 0, 1)
    total_songs = Song.query.count()
    top_members = db.session.query(
        Member.first_name, Member.last_name, db.func.sum(Payment.amount).label("total")
    ).join(Payment, Payment.member_id == Member.id).group_by(Payment.member_id).order_by(
        db.func.sum(Payment.amount).desc()).limit(5).all()
    recent_payments = db.session.query(
        Member.first_name, Member.last_name, Payment.amount, Payment.payment_date, Payment.payment_for
    ).join(Member, Payment.member_id == Member.id).order_by(Payment.payment_date.desc()).limit(5).all()
    return render_template("dashboard.html", total_members=total_members, total_payments=total_payments,
                           total_revenue=total_revenue, attendance_rate=attendance_rate, total_songs=total_songs,
                           top_members=top_members, recent_payments=recent_payments)


@bp.route("/audit-log")
@login_required
def audit_log():
    page = request.args.get("page", 1, type=int)
    per_page = 50
    pagination = AuditLog.query.order_by(AuditLog.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("audit_log.html", logs=pagination.items, pagination=pagination)
