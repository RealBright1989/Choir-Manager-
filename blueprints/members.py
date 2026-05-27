import os
from datetime import date, datetime
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, Response, current_app
from werkzeug.security import generate_password_hash
from utils import login_required, validate_csrf, validate_required, validate_email, generate_otp, send_otp_sms, secrets, log_audit
from models import db, Member, Payment, Attendance, PhoneVerification, User, Setting
from fpdf import FPDF

bp = Blueprint("members", __name__)
PHOTO_FOLDER = "member_photos"


@bp.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members.member_join"))
        phone = request.form.get("phone", "").strip()
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        other_names = request.form.get("other_names", "").strip()
        dob = request.form.get("dob", "").strip()
        state_origin = request.form.get("state_of_origin", "").strip()
        lga = request.form.get("lga", "").strip()
        email = request.form.get("email", "").strip()
        nin = request.form.get("nin_number", "").strip()
        qualification = request.form.get("academic_qualification", "").strip()
        section = request.form.get("section", "").strip()
        country = request.form.get("country", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        is_nigeria = country.lower() in ("", "nigeria")
        errs = []
        for v, n in [(fn, "First name"), (ln, "Last name"), (dob, "Date of birth"), (phone, "Phone number"), (section, "Singing part")]:
            e = validate_required(v, n)
            if e: errs.append(e)
        if is_nigeria:
            for v, n in [(state_origin, "State of origin"), (lga, "LGA"), (nin, "NIN number")]:
                e = validate_required(v, n)
                if e: errs.append(e)
        if email:
            e = validate_email(email)
            if e: errs.append(e)
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        if not password:
            errs.append("Password is required")
        elif password != confirm:
            errs.append("Passwords do not match")
        elif len(password) < 4:
            errs.append("Password must be at least 4 characters")
        photo_filename = ""
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(PHOTO_FOLDER, photo_filename))
        if errs:
            for e in errs: flash(e, "danger")
            return redirect(url_for("members.member_join"))
        m = Member(first_name=fn, last_name=ln, other_names=other_names, phone=phone, email=email,
                    section=section, join_date=date.today().strftime("%Y-%m-%d"), dob=dob,
                    state_of_origin=state_origin, lga=lga, nin_number=nin,
                    academic_qualification=qualification, country=country, passport_number=passport_number,
                    photo=photo_filename, notes="Self-registered via join form")
        db.session.add(m)
        db.session.flush()
        username = email if email else f"user_{phone.replace('+','')}"
        if User.query.filter_by(username=username).first():
            db.session.rollback()
            flash("A user with this email/phone already exists. Please sign in instead.", "danger")
            return redirect(url_for("members.member_join"))
        u = User(username=username, password_hash=generate_password_hash(password), role="viewer",
                 created_at=date.today().strftime("%Y-%m-%d"), email=email)
        db.session.add(u)
        PhoneVerification.query.filter_by(phone=phone).delete()
        db.session.commit()
        log_audit("create", "member", m.id, f"Self-registration: {fn} {ln}")
        flash("Registration submitted successfully! You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("member_join.html")


@bp.route("/join/send-otp", methods=["POST"])
def send_otp():
    phone = request.form.get("phone", "").strip()
    if not phone:
        return {"ok": False, "error": "Phone number required"}
    otp = generate_otp()
    expires = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    PhoneVerification.query.filter_by(phone=phone).delete()
    db.session.add(PhoneVerification(phone=phone, otp=otp, verified=0, created_at=expires, expires_at=expires))
    db.session.commit()
    ok = send_otp_sms(phone, otp)
    if ok:
        return {"ok": True, "message": "OTP sent to your phone"}
    return {"ok": False, "error": "Failed to send OTP. Check SMS settings."}


@bp.route("/join/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get("phone", "").strip()
    otp = request.form.get("otp", "").strip()
    if not phone or not otp:
        return {"ok": False, "error": "Phone and OTP required"}
    pv = PhoneVerification.query.filter_by(phone=phone, otp=otp, verified=0).first()
    if pv:
        pv.verified = 1
        db.session.commit()
        return {"ok": True, "message": "Phone verified!"}
    return {"ok": False, "error": "Invalid or expired OTP"}


@bp.route("/member-photos/<filename>")
def member_photo(filename):
    return send_from_directory(PHOTO_FOLDER, filename)


@bp.route("/members")
@login_required
def members():
    search = request.args.get("search", "")
    if search:
        query = Member.query.filter(
            db.or_(Member.first_name.like(f"%{search}%"), Member.last_name.like(f"%{search}%"), Member.phone.like(f"%{search}%"))
        ).order_by(Member.last_name, Member.first_name)
    else:
        query = Member.query.order_by(Member.last_name, Member.first_name)
    members_list = query.all()
    payment_totals = dict(db.session.query(Payment.member_id, db.func.sum(Payment.amount)).group_by(Payment.member_id).all())
    return render_template("members.html", members=members_list, payment_totals=payment_totals, search=search)


@bp.route("/members/add", methods=["GET", "POST"])
@login_required
def member_add():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members.members"))
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        join_date = request.form.get("join_date", "").strip()
        errs = []
        for v, n in [(fn, "First name"), (ln, "Last name"), (join_date, "Join date")]:
            e = validate_required(v, n)
            if e: errs.append(e)
        e = validate_email(email)
        if e: errs.append(e)
        photo_filename = ""
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(PHOTO_FOLDER, photo_filename))
        if errs:
            for e in errs: flash(e, "danger")
            return redirect(url_for("members.member_add"))
        m = Member(first_name=fn, last_name=ln, other_names=request.form.get("other_names", "").strip(),
                    phone=request.form.get("phone", "").strip(), email=email,
                    section=request.form.get("section", "Soprano"), join_date=join_date,
                    address=request.form.get("address", "").strip(), notes=request.form.get("notes", "").strip(),
                    dob=request.form.get("dob", "").strip(),
                    state_of_origin=request.form.get("state_of_origin", "").strip(),
                    lga=request.form.get("lga", "").strip(),
                    nin_number=request.form.get("nin_number", "").strip(),
                    academic_qualification=request.form.get("academic_qualification", "").strip(),
                    country=request.form.get("country", "Nigeria").strip(),
                    passport_number=request.form.get("passport_number", "").strip(),
                    photo=photo_filename, zone=request.form.get("zone", "").strip(),
                    area=request.form.get("area", "").strip())
        db.session.add(m)
        db.session.flush()
        db.session.commit()
        log_audit("create", "member", m.id, f"Admin added: {fn} {ln}")
        flash("Member added successfully!", "success")
        return redirect(url_for("members.members"))
    return render_template("member_form.html", member=None, title="Add Member")


@bp.route("/members/edit/<int:id>", methods=["GET", "POST"])
@login_required
def member_edit(id):
    member = db.session.get(Member, id)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("members.members"))
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members.members"))
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        join_date = request.form.get("join_date", "").strip()
        errs = []
        for v, n in [(fn, "First name"), (ln, "Last name"), (join_date, "Join date")]:
            e = validate_required(v, n)
            if e: errs.append(e)
        e = validate_email(email)
        if e: errs.append(e)
        photo_filename = request.form.get("existing_photo", "")
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(PHOTO_FOLDER, photo_filename))
                old_photo = request.form.get("existing_photo", "")
                if old_photo:
                    old_path = os.path.join(PHOTO_FOLDER, old_photo)
                    if os.path.isfile(old_path): os.remove(old_path)
        if errs:
            for e in errs: flash(e, "danger")
            return redirect(url_for("members.member_edit", id=id))
        for field in ["first_name", "last_name", "other_names", "phone", "section", "join_date", "address", "notes",
                      "dob", "state_of_origin", "lga", "nin_number", "academic_qualification", "country",
                      "passport_number", "zone", "area"]:
            setattr(member, field, request.form.get(field, "").strip())
        member.email = email
        member.photo = photo_filename
        db.session.commit()
        log_audit("update", "member", id, f"Updated member: {member.first_name} {member.last_name}")
        flash("Member updated!", "success")
        return redirect(url_for("members.members"))
    return render_template("member_form.html", member=member, title="Edit Member")


@bp.route("/members/delete/<int:id>", methods=["GET", "POST"])
@login_required
def member_delete(id):
    if request.method == "POST" and not validate_csrf():
        return redirect(url_for("members.members"))
    member = db.session.get(Member, id)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("members.members"))
    Payment.query.filter_by(member_id=id).delete()
    Attendance.query.filter_by(member_id=id).delete()
    db.session.delete(member)
    db.session.commit()
    log_audit("delete", "member", id, f"Deleted: {member.first_name} {member.last_name}")
    flash("Member deleted.", "success")
    return redirect(url_for("members.members"))


@bp.route("/members/<int:id>")
@login_required
def member_detail(id):
    member = db.session.get(Member, id)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("members.members"))
    payments = Payment.query.filter_by(member_id=id).order_by(Payment.payment_date.desc()).all()
    attendance_records = Attendance.query.filter_by(member_id=id).order_by(Attendance.date.desc()).all()
    settings = Setting.query.first()
    return render_template("member_detail.html", member=member, payments=payments, attendance=attendance_records, settings=settings)


@bp.route("/members/<int:id>/pdf")
@login_required
def member_pdf(id):
    member = db.session.get(Member, id)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("members.members"))
    payments = Payment.query.filter_by(member_id=id).order_by(Payment.payment_date.desc()).all()
    attendance_records = Attendance.query.filter_by(member_id=id).order_by(Attendance.date.desc()).all()
    curr = (db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$") + " "
    total_paid = sum(p.amount for p in payments)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    logo_path = current_app.root_path + "/static/logo_watermark.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=16)

    pdf.ln(6)
    pdf.set_y(16)
    pdf.cell(0, 10, f"{member.first_name} {member.last_name}", align="R")
    pdf.ln(14)

    if member.photo:
        photo_path = os.path.join(current_app.root_path, "member_photos", member.photo)
        if os.path.exists(photo_path):
            try:
                pdf.image(photo_path, x=82, y=30, w=46, h=58)
            except Exception:
                pass
            pdf.ln(60)
        else:
            pdf.ln(10)
    else:
        pdf.ln(10)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  PERSONAL INFORMATION", fill=True)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)

    fields = [
        ("Section", member.section),
        ("Phone", member.phone),
        ("Email", member.email or "-"),
        ("Date of Birth", member.dob or "-"),
        ("Country of Origin", member.country or "Nigeria"),
        ("State of Origin", member.state_of_origin or "-"),
        ("LGA", member.lga or "-"),
        ("NIN", member.nin_number or "-"),
    ]
    is_nigeria = not member.country or member.country.lower() == "nigeria"
    if not is_nigeria:
        fields.append(("Passport / ID", member.passport_number or "-"))
    fields += [
        ("Qualification", member.academic_qualification or "-"),
        ("Zone", member.zone or "-"),
        ("Area", member.area or "-"),
        ("Joined", member.join_date),
    ]
    for label, value in fields:
        pdf.cell(50, 6, f"  {label}:")
        pdf.cell(0, 6, value)
        pdf.ln(6)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  FINANCIAL SUMMARY", fill=True)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(50, 6, "  Total Paid:")
    pdf.cell(0, 6, f"{curr}{total_paid:.2f}")
    pdf.ln(6)
    pdf.cell(50, 6, "  Payments Made:")
    pdf.cell(0, 6, str(len(payments)))
    pdf.ln(10)

    if payments:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(26, 26, 46)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, "  PAYMENT HISTORY", fill=True)
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(35, 6, "Date", border=1, fill=True)
        pdf.cell(25, 6, "Amount", border=1, fill=True)
        pdf.cell(50, 6, "For", border=1, fill=True)
        pdf.cell(0, 6, "Notes", border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        for p in payments:
            pdf.cell(35, 5, p.payment_date, border=1)
            pdf.cell(25, 5, f"{curr}{p.amount:.2f}", border=1)
            pdf.cell(50, 5, (p.payment_for or "-")[:28], border=1)
            pdf.cell(0, 5, (p.notes or "-")[:40], border=1)
            pdf.ln()

    if attendance_records:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(26, 26, 46)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, "  ATTENDANCE HISTORY", fill=True)
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(35, 6, "Date", border=1, fill=True)
        pdf.cell(25, 6, "Status", border=1, fill=True)
        pdf.cell(0, 6, "Notes", border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        for a in attendance_records:
            pdf.cell(35, 5, a.date, border=1)
            pdf.cell(25, 5, a.status, border=1)
            pdf.cell(0, 5, (a.notes or "-")[:60], border=1)
            pdf.ln()

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={member.first_name}_{member.last_name}_profile.pdf"})
