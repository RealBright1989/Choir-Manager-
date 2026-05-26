from datetime import datetime, date
from flask import Blueprint, render_template, request, Response
from utils import login_required, export_csv, get_hierarchical_report, generate_hierarchy_pdf, generate_hierarchy_excel
from models import db, Member, Payment, Attendance, Setting, Song, User
import csv as csv_mod
import io as io_mod

bp = Blueprint("reports", __name__)


@bp.route("/reports", defaults={"section": "standard"}, methods=["GET"])
@bp.route("/reports/<section>")
@login_required
def reports(section="standard"):
    if section == "hierarchy":
        zone_f = request.args.get("zone", "")
        area_f = request.args.get("area", "")
        state_f = request.args.get("state", "")
        country_f = request.args.get("country", "")
        zones = [r[0] for r in Member.query.with_entities(Member.zone).filter(Member.zone.isnot(None), Member.zone != "").distinct().order_by(Member.zone).all()]
        areas = [r[0] for r in Member.query.with_entities(Member.area).filter(Member.area.isnot(None), Member.area != "").distinct().order_by(Member.area).all()]
        states = [r[0] for r in Member.query.with_entities(Member.state_of_origin).filter(Member.state_of_origin.isnot(None), Member.state_of_origin != "").distinct().order_by(Member.state_of_origin).all()]
        countries = [r[0] for r in Member.query.with_entities(Member.country).filter(Member.country.isnot(None), Member.country != "").distinct().order_by(Member.country).all()]
        flat, hierarchy, grand = get_hierarchical_report(zone_f, area_f, state_f, country_f)
        return render_template("reports.html", section="hierarchy", flat=flat, grand=grand,
                               zones=zones, areas=areas, states=states, countries=countries,
                               filters={"zone": zone_f, "area": area_f, "state": state_f, "country": country_f})

    member_financials = db.session.query(
        Member.first_name, Member.last_name, Member.section, Member.join_date,
        db.func.coalesce(db.func.sum(Payment.amount), 0).label("total_paid"),
        db.func.count(Payment.id).label("payment_count")
    ).outerjoin(Payment, Payment.member_id == Member.id).group_by(Member.id).order_by(Member.last_name).all()

    monthly_summary = db.session.query(
        db.func.strftime("%Y-%m", Payment.payment_date).label("month"),
        db.func.count(Payment.id).label("txns"),
        db.func.sum(Payment.amount).label("total")
    ).group_by("month").order_by(db.text("month DESC")).all()

    section_counts = db.session.query(Member.section, db.func.count(Member.id).label("count")).group_by(Member.section).all()
    attendance_summary = db.session.query(Attendance.status, db.func.count(Attendance.id).label("count")).group_by(Attendance.status).all()

    return render_template("reports.html", section="standard",
                           member_financials=member_financials, monthly_summary=monthly_summary,
                           section_counts=section_counts, attendance_summary=attendance_summary)


@bp.route("/export/members")
@login_required
def export_members():
    rows = Member.query.order_by(Member.last_name, Member.first_name).all()
    return export_csv(["id", "first_name", "last_name", "other_names", "phone", "email", "section", "join_date",
                       "address", "dob", "state_of_origin", "lga", "nin_number", "academic_qualification",
                       "country", "passport_number", "zone", "area", "notes"], rows, "members.csv")


@bp.route("/export/payments")
@login_required
def export_payments():
    rows = db.session.execute(
        db.select(Payment.id, Member.first_name, Member.last_name, Payment.amount, Payment.payment_date, Payment.payment_for, Payment.notes)
        .join(Member).order_by(Payment.payment_date.desc())
    ).all()
    return export_csv(["id", "first_name", "last_name", "amount", "payment_date", "payment_for", "notes"],
                      rows, "payments.csv")


@bp.route("/export/attendance")
@login_required
def export_attendance():
    rows = db.session.execute(
        db.select(Attendance.id, Member.first_name, Member.last_name, Attendance.date, Attendance.status, Attendance.notes)
        .join(Member).order_by(Attendance.date.desc())
    ).all()
    return export_csv(["id", "first_name", "last_name", "date", "status", "notes"], rows, "attendance.csv")


@bp.route("/export/backup")
@login_required
def export_backup():
    output = io_mod.StringIO()
    members = Member.query.all()
    if members:
        cols = ["id", "first_name", "last_name", "other_names", "phone", "email", "section", "join_date", "address",
                "dob", "state_of_origin", "lga", "nin_number", "academic_qualification", "country",
                "passport_number", "photo", "zone", "area", "notes"]
        output.write("--- members ---\n")
        csv_mod.writer(output).writerow(cols)
        for m in members:
            csv_mod.writer(output).writerow([getattr(m, c, "") or "" for c in cols])
        output.write("\n")
    payments = Payment.query.all()
    if payments:
        cols = ["id", "member_id", "amount", "payment_date", "payment_for", "notes"]
        output.write("--- payments ---\n")
        csv_mod.writer(output).writerow(cols)
        for p in payments:
            csv_mod.writer(output).writerow([getattr(p, c, "") or "" for c in cols])
        output.write("\n")
    attendance = Attendance.query.all()
    if attendance:
        cols = ["id", "member_id", "date", "status", "notes"]
        output.write("--- attendance ---\n")
        csv_mod.writer(output).writerow(cols)
        for a in attendance:
            csv_mod.writer(output).writerow([getattr(a, c, "") or "" for c in cols])
        output.write("\n")
    songs = db.session.query(Song).all()
    if songs:
        cols = ["id", "title", "composer", "lyrics", "audio_file", "upload_date", "notes"]
        output.write("--- songs ---\n")
        csv_mod.writer(output).writerow(cols)
        for s in songs:
            csv_mod.writer(output).writerow([getattr(s, c, "") or "" for c in cols])
        output.write("\n")
    settings = Setting.query.all()
    if settings:
        output.write("--- settings ---\n")
        csv_mod.writer(output).writerow(["key", "value"])
        for s in settings:
            csv_mod.writer(output).writerow([s.key, s.value or ""])
        output.write("\n")
    users = db.session.query(User).all()
    if users:
        cols = ["id", "username", "role", "created_at"]
        output.write("--- users ---\n")
        csv_mod.writer(output).writerow(cols)
        for u in users:
            csv_mod.writer(output).writerow([getattr(u, c, "") or "" for c in cols])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=choir_full_backup_{date.today().strftime('%Y%m%d')}.csv"})


@bp.route("/reports/hierarchy/pdf")
@login_required
def reports_hierarchy_pdf():
    zone_f = request.args.get("zone", "")
    area_f = request.args.get("area", "")
    state_f = request.args.get("state", "")
    country_f = request.args.get("country", "")
    flat, hierarchy, grand = get_hierarchical_report(zone_f, area_f, state_f, country_f)
    choir_name = db.session.get(Setting, "choir_name").value if db.session.get(Setting, "choir_name") else "Choir"
    currency = db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$"
    buf = generate_hierarchy_pdf(flat, grand, choir_name, currency)
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=hierarchy_report_{datetime.now().strftime('%Y%m%d')}.pdf"})


@bp.route("/reports/hierarchy/excel")
@login_required
def reports_hierarchy_excel():
    zone_f = request.args.get("zone", "")
    area_f = request.args.get("area", "")
    state_f = request.args.get("state", "")
    country_f = request.args.get("country", "")
    flat, hierarchy, grand = get_hierarchical_report(zone_f, area_f, state_f, country_f)
    choir_name = db.session.get(Setting, "choir_name").value if db.session.get(Setting, "choir_name") else "Choir"
    currency = db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$"
    buf = generate_hierarchy_excel(flat, grand, choir_name, currency)
    return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=hierarchy_report_{datetime.now().strftime('%Y%m%d')}.xlsx"})
