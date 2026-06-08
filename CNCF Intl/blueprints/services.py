from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import login_required
from models import db, ServicePlan

bp = Blueprint("services", __name__)


@bp.route("/services")
@login_required
def list():
    plans = ServicePlan.query.order_by(ServicePlan.date.desc()).all()
    return render_template("services.html", plans=plans)


@bp.route("/services/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        p = ServicePlan(
            title=request.form["title"],
            date=request.form["date"],
            description=request.form.get("description"),
            location=request.form.get("location"),
            conductor=request.form.get("conductor"),
            songs_list=request.form.get("songs_list"),
            notes=request.form.get("notes"),
            created_by=session.get("user_id"),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(p)
        db.session.commit()
        flash(f"'{p.title}' planned!", "success")
        return redirect(url_for("services.list"))
    return render_template("service_form.html", plan=None)


@bp.route("/services/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    p = db.session.get(ServicePlan, id)
    if not p:
        flash("Plan not found.", "danger")
        return redirect(url_for("services.list"))
    if request.method == "POST":
        p.title = request.form["title"]
        p.date = request.form["date"]
        p.description = request.form.get("description")
        p.location = request.form.get("location")
        p.conductor = request.form.get("conductor")
        p.songs_list = request.form.get("songs_list")
        p.notes = request.form.get("notes")
        db.session.commit()
        flash(f"'{p.title}' updated!", "success")
        return redirect(url_for("services.list"))
    return render_template("service_form.html", plan=p)


@bp.route("/services/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    p = db.session.get(ServicePlan, id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash(f"'{p.title}' deleted.", "success")
    return redirect(url_for("services.list"))
