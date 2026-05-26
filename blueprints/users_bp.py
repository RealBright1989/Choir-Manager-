from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from utils import login_required, validate_csrf, validate_required, log_audit
from models import db, User

bp = Blueprint("users_bp", __name__)


@bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if session.get("role") != "admin":
        flash("Only admins can manage users.", "danger")
        return redirect(url_for("general.dashboard"))
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("users_bp.users"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "viewer")
        err = validate_required(username, "Username")
        if err: flash(err, "danger")
        elif len(password) < 4: flash("Password must be at least 4 characters.", "danger")
        else:
            if User.query.filter_by(username=username).first():
                flash(f"Username '{username}' already exists.", "danger")
            else:
                u = User(username=username, password_hash=generate_password_hash(password),
                         role=role, created_at=date.today().strftime("%Y-%m-%d"))
                db.session.add(u)
                db.session.flush()
                db.session.commit()
                log_audit("create", "user", u.id, f"Created user: {username} ({role})")
                flash(f"User '{username}' created!", "success")
    users_list = User.query.with_entities(User.id, User.username, User.role, User.created_at).order_by(User.username).all()
    return render_template("users.html", users=users_list)


@bp.route("/users/delete/<int:id>")
@login_required
def user_delete(id):
    if session.get("role") != "admin":
        flash("Only admins can delete users.", "danger")
        return redirect(url_for("general.dashboard"))
    if id == session["user_id"]:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for("users_bp.users"))
    user = db.session.get(User, id)
    if user:
        log_audit("delete", "user", id, f"Deleted user: {user.username}")
    User.query.filter_by(id=id).delete()
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("users_bp.users"))
