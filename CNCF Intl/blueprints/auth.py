from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils import generate_csrf, login_required
from models import db, User, Member


bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if user.status == "pending":
                flash("Your account is pending approval by an admin.", "warning")
                return redirect(url_for("auth.pending_approval"))
            if user.status == "rejected":
                flash("Your registration was rejected. Contact an administrator.", "danger")
                return render_template("login.html", csrf=generate_csrf)
            session["user_id"] = user.id
            session["username"] = user.username
            session["display_name"] = user.display_name
            session["role"] = user.role
            flash(f"Welcome back, {user.display_name}!", "success")
            return redirect(url_for("general.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", csrf=generate_csrf)


@bp.route("/pending-approval")
def pending_approval():
    return render_template("pending_approval.html")


@bp.route("/admin/approvals", methods=["GET", "POST"])
@login_required
def approvals():
    if session.get("role") != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("general.dashboard"))

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        action = request.form.get("action")
        user = db.session.get(User, user_id)
        if user and action in ("approve", "reject"):
            user.status = "approved" if action == "approve" else "rejected"
            db.session.commit()
            flash(f"User '{user.display_name}' {action}d.", "success")
        return redirect(url_for("auth.approvals"))

    pending = User.query.filter_by(status="pending").order_by(User.created_at.desc()).all()
    return render_template("admin_approvals.html", pending=pending)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user = User.query.filter_by(username=username).first()
        if user:
            flash(f"A password reset link has been sent to your registered email address.", "success")
        else:
            flash("No account found with that username.", "danger")
        return redirect(url_for("auth.forgot_password"))
    return render_template("forgot_password.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
