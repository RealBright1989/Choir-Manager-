from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import login_required, validate_csrf, validate_required, log_audit
from models import db, Member, Attendance

bp = Blueprint("attendance", __name__)


@bp.route("/attendance")
@login_required
def attendance():
    date_filter = request.args.get("date", date.today().strftime("%Y-%m-%d"))
    available_dates = [r[0] for r in Attendance.query.with_entities(Attendance.date).distinct().order_by(Attendance.date.desc()).all()]
    records = Attendance.query.join(Member).add_columns(
        Member.first_name, Member.last_name, Member.section
    ).filter(Attendance.date == date_filter).order_by(Member.last_name, Member.first_name).all()
    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    return render_template("attendance.html", records=records, members=members,
                           available_dates=available_dates, selected_date=date_filter)


@bp.route("/attendance/take", methods=["POST"])
@login_required
def attendance_take():
    if not validate_csrf():
        return redirect(url_for("attendance.attendance"))
    date_val = request.form.get("date", "").strip()
    err = validate_required(date_val, "Date")
    if err:
        flash(err, "danger")
        return redirect(url_for("attendance.attendance"))
    member_ids = request.form.getlist("member_ids")
    Attendance.query.filter_by(date=date_val).delete()
    for mid in member_ids:
        if mid.isdigit():
            status = request.form.get(f"status_{mid}", "Present")
            db.session.add(Attendance(member_id=int(mid), date=date_val, status=status))
    db.session.commit()
    log_audit("create", "attendance", 0, f"Attendance taken for {date_val} ({len(member_ids)} members)")
    flash(f"Attendance for {date_val} saved!", "success")
    return redirect(url_for("attendance.attendance", date=date_val))
