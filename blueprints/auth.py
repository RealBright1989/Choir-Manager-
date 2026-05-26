import logging
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils import validate_csrf, validate_required, generate_csrf, send_reset_email, generate_reset_token, validate_email, log_audit
from models import db, User, PasswordResetToken

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            log_audit("login", "user", user.id, f"User {user.username} logged in")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("general.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", csrf=generate_csrf)


@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("auth.signup"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        errs = []
        e = validate_required(username, "Username")
        if e: errs.append(e)
        if len(password) < 4: errs.append("Password must be at least 4 characters.")
        if password != confirm: errs.append("Passwords do not match.")
        if errs:
            for e in errs: flash(e, "danger")
            return redirect(url_for("auth.signup"))
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken.", "danger")
            return redirect(url_for("auth.signup"))
        db.session.add(User(username=username, password_hash=generate_password_hash(password),
                            role="viewer", created_at=date.today().strftime("%Y-%m-%d")))
        db.session.commit()
        flash("Account created! You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("signup.html")


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("auth.forgot_password"))
        username = request.form.get("username", "").strip()
        err = validate_required(username, "Username")
        if err:
            flash(err, "danger")
            return redirect(url_for("auth.forgot_password"))
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("If that username exists, a reset link has been sent.", "info")
            return redirect(url_for("auth.forgot_password"))
        token = generate_reset_token()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        PasswordResetToken.query.filter_by(user_id=user.id, used=0).delete()
        db.session.add(PasswordResetToken(user_id=user.id, token=token, created_at=now,
                                          expires_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.session.commit()
        reset_url = url_for("auth.reset_password", token=token, _external=True)
        email = user.email
        if email:
            send_reset_email(email, user.username, reset_url)
        else:
            logger.info(f"[DEV MODE] Password reset link for {user.username}: {reset_url}")
        flash("If that username exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    prt = PasswordResetToken.query.filter_by(token=token, used=0).first()
    if not prt:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    try:
        expires = datetime.strptime(prt.expires_at, "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires:
            flash("Reset link has expired. Request a new one.", "danger")
            return redirect(url_for("auth.forgot_password"))
    except ValueError:
        pass
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("auth.reset_password", token=token))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
            return redirect(url_for("auth.reset_password", token=token))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_password", token=token))
        user = db.session.get(User, prt.user_id)
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("auth.forgot_password"))
        user.password_hash = generate_password_hash(password)
        prt.used = 1
        db.session.commit()
        flash("Password reset successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", token=token)
