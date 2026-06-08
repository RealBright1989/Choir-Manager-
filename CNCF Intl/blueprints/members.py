import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from utils import login_required
from models import db, Member, User

bp = Blueprint("members", __name__)


@bp.route("/members")
@login_required
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    section = request.args.get("section")
    query = Member.query
    if section:
        query = query.filter_by(section=section)
    total = query.count()
    members = query.order_by(Member.last_name).all()

    # Stats for KPI cards
    total_count = Member.query.count()
    active_count = Member.query.filter_by(is_active=True).count()
    new_count = Member.query.filter(
        Member.join_date >= (datetime.now().strftime("%Y-%m") + "-01")
    ).count() if total_count else 0

    section_counts = {}
    for s in ["Treble", "Alto", "Tenor", "Bass"]:
        section_counts[s] = Member.query.filter_by(section=s).count()
    pending_count = Member.query.filter_by(is_active=False).count()

    states = [r[0] for r in db.session.query(Member.state).filter(Member.state.isnot(None)).distinct().order_by(Member.state).all()]

    return render_template("members.html", members=members, total_count=total_count,
                           active_count=active_count, new_count=new_count, states=states,
                           section_counts=section_counts, pending_count=pending_count)


@bp.route("/members/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        m = Member(
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            other_name=request.form.get("other_name") or None,
            date_of_birth=request.form.get("date_of_birth") or None,
            nation=request.form.get("nation") or None,
            state=request.form.get("state") or None,
            area=request.form.get("area") or None,
            zone=request.form.get("zone") or None,
            bethel=request.form.get("bethel") or None,
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            section=request.form.get("section"),
            role=request.form.get("role"),
            join_date=request.form.get("join_date", datetime.now().strftime("%Y-%m-%d")),
            address=request.form.get("address"),
            notes=request.form.get("notes"),
            is_active=request.form.get("is_active") == "on",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        photo = request.files.get("photo")
        if photo and photo.filename:
            ext = photo.filename.rsplit(".", 1)[1].lower() if "." in photo.filename else "jpg"
            fname = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
            photo.save(os.path.join(current_app.root_path, path))
            m.photo = fname
        db.session.add(m)
        db.session.flush()

        # If no user is logged in, create a User account (self-registration)
        if "user_id" not in session:
            username = request.form.get("reg_username", "").strip()
            password = request.form.get("reg_password", "")
            if username and password:
                u = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    display_name=m.full_name,
                    role="user",
                    status="pending",
                    member_id=m.id,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                db.session.add(u)

        db.session.commit()
        flash(f"Registration submitted! Your account is pending approval.", "success")
        return redirect(url_for("auth.pending_approval"))

    is_registration = "user_id" not in session
    return render_template("member_form.html", member=None, is_registration=is_registration)


@bp.route("/members/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    m = db.session.get(Member, id)
    if not m:
        flash("Member not found.", "danger")
        return redirect(url_for("members.list"))
    if request.method == "POST":
        m.first_name = request.form["first_name"]
        m.last_name = request.form["last_name"]
        m.other_name = request.form.get("other_name") or None
        m.date_of_birth = request.form.get("date_of_birth") or None
        m.nation = request.form.get("nation") or None
        m.state = request.form.get("state") or None
        m.area = request.form.get("area") or None
        m.zone = request.form.get("zone") or None
        m.bethel = request.form.get("bethel") or None
        m.email = request.form.get("email")
        m.phone = request.form.get("phone")
        m.section = request.form.get("section")
        m.role = request.form.get("role")
        m.join_date = request.form.get("join_date")
        m.address = request.form.get("address")
        m.notes = request.form.get("notes")
        m.is_active = request.form.get("is_active") == "on"
        photo = request.files.get("photo")
        if photo and photo.filename:
            ext = photo.filename.rsplit(".", 1)[1].lower() if "." in photo.filename else "jpg"
            fname = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
            photo.save(os.path.join(current_app.root_path, path))
            m.photo = fname
        db.session.commit()
        flash(f"{m.full_name} updated!", "success")
        return redirect(url_for("members.list"))
    return render_template("member_form.html", member=m)


@bp.route("/members/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    m = db.session.get(Member, id)
    if m:
        db.session.delete(m)
        db.session.commit()
        flash(f"{m.full_name} removed.", "success")
    return redirect(url_for("members.list"))
