import os
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from utils import login_required, validate_csrf, validate_required, validate_email, generate_otp, send_otp_sms, secrets, log_audit
from models import db, Member, Payment, Attendance, PhoneVerification

bp = Blueprint("members", __name__)
PHOTO_FOLDER = "member_photos"


@bp.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members.member_join"))
        phone = request.form.get("phone", "").strip()
        pv = PhoneVerification.query.filter_by(phone=phone, verified=1).first()
        if not pv:
            flash("Please verify your phone number first.", "danger")
            return redirect(url_for("members.member_join"))
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
        PhoneVerification.query.filter_by(phone=phone).delete()
        db.session.commit()
        log_audit("create", "member", m.id, f"Self-registration: {fn} {ln}")
        flash("Registration submitted successfully!", "success")
        return redirect(url_for("landing.landing"))
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
    return render_template("member_detail.html", member=member, payments=payments, attendance=attendance_records)
