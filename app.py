import sqlite3
import os
import csv
import io
import re
import secrets
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, session, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "choir-fixed-secret-key-2026-eton-natural"
app.config["UPLOAD_FOLDER"] = "song_uploads"
app.config["PHOTO_FOLDER"] = "member_photos"
DB_FILE = "choir_web.db"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PHOTO_FOLDER"], exist_ok=True)


# ─── Database ─────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            section TEXT NOT NULL DEFAULT 'Soprano',
            join_date TEXT NOT NULL,
            address TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            payment_for TEXT,
            notes TEXT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Present',
            notes TEXT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            composer TEXT,
            lyrics TEXT,
            audio_file TEXT,
            upload_date TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS phone_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            otp TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
    """)
    for col in ["dob", "state_of_origin", "lga", "nin_number", "academic_qualification", "country", "passport_number", "photo", "other_names"]:
        try:
            cur.execute(f"ALTER TABLE members ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('choir_name', '8 Eton Natural Choir')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('currency', '$')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('dues_amount', '10')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('sms_provider', 'log')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('twilio_account_sid', '')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('twilio_auth_token', '')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('twilio_phone', '')")

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                    ("admin", generate_password_hash("admin123"), "admin", date.today().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()


init_db()


# ─── SMS / Phone Verification ─────────────────────────────────────

def get_sms_settings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings WHERE key IN ('sms_provider','twilio_account_sid','twilio_auth_token','twilio_phone')")
    s = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return s


def send_otp_sms(phone, otp):
    sms = get_sms_settings()
    provider = sms.get("sms_provider", "log")

    if provider == "twilio" and TWILIO_AVAILABLE:
        sid = sms.get("twilio_account_sid", "")
        token = sms.get("twilio_auth_token", "")
        from_phone = sms.get("twilio_phone", "")
        if sid and token and from_phone:
            try:
                client = TwilioClient(sid, token)
                client.messages.create(
                    body=f"Your {sms.get('choir_name','Choir')} verification code is: {otp}",
                    from_=from_phone,
                    to=phone
                )
                logger.info(f"OTP sent via Twilio to {phone}")
                return True
            except Exception as e:
                logger.error(f"Twilio error: {e}")
                return False

    logger.info(f"[DEV MODE] OTP for {phone}: {otp}")
    return True


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


@app.route("/join/send-otp", methods=["POST"])
def send_otp():
    phone = request.form.get("phone", "").strip()
    if not phone:
        return {"ok": False, "error": "Phone number required"}

    otp = generate_otp()
    expires = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM phone_verifications WHERE phone=?", (phone,))
    cur.execute("INSERT INTO phone_verifications (phone, otp, verified, created_at, expires_at) VALUES (?,?,0,?,?)",
                (phone, otp, expires, expires))
    conn.commit()
    conn.close()

    ok = send_otp_sms(phone, otp)
    if ok:
        return {"ok": True, "message": "OTP sent to your phone"}
    return {"ok": False, "error": "Failed to send OTP. Check SMS settings."}


@app.route("/join/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get("phone", "").strip()
    otp = request.form.get("otp", "").strip()
    if not phone or not otp:
        return {"ok": False, "error": "Phone and OTP required"}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM phone_verifications WHERE phone=? AND otp=? AND verified=0",
                (phone, otp))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE phone_verifications SET verified=1 WHERE id=?", (row["id"],))
        conn.commit()
        conn.close()
        return {"ok": True, "message": "Phone verified!"}
    conn.close()
    return {"ok": False, "error": "Invalid or expired OTP"}


# ─── CSRF ──────────────────────────────────────────────────────────

def generate_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf():
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        flash("Invalid form token. Please try again.", "danger")
        return False
    return True


@app.context_processor
def inject_globals():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings")
    settings = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return dict(settings=settings, now=datetime.now, csrf=generate_csrf,
                session=session)


# ─── Auth decorator ────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─── Validation helpers ────────────────────────────────────────────

def validate_required(val, field_name):
    if not val or not val.strip():
        return f"{field_name} is required."
    return None


def validate_email(email):
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return "Invalid email format."
    return None


def validate_amount(amount):
    try:
        a = float(amount)
        if a <= 0:
            return "Amount must be greater than zero."
    except (ValueError, TypeError):
        return "Amount must be a valid number."
    return None


def validate_date(d, fmt="%Y-%m-%d"):
    try:
        datetime.strptime(d, fmt)
    except (ValueError, TypeError):
        return f"Invalid date format. Use {fmt}."
    return None


# ─── Auth Routes ──────────────────────────────────────────────────

@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("member_join"))
        phone = request.form.get("phone", "").strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT verified FROM phone_verifications WHERE phone=? AND verified=1", (phone,))
        verified_row = cur.fetchone()
        conn.close()

        if not verified_row:
            flash("Please verify your phone number first.", "danger")
            return redirect(url_for("member_join"))

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
        for v, n in [(fn, "First name"), (ln, "Last name"), (dob, "Date of birth"),
                      (phone, "Phone number"), (section, "Singing part")]:
            e = validate_required(v, n)
            if e:
                errs.append(e)

        if is_nigeria:
            for v, n in [(state_origin, "State of origin"), (lga, "LGA"), (nin, "NIN number")]:
                e = validate_required(v, n)
                if e:
                    errs.append(e)

        if email:
            e = validate_email(email)
            if e:
                errs.append(e)

        photo_filename = ""
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(app.config["PHOTO_FOLDER"], photo_filename))

        if errs:
            for e in errs:
                flash(e, "danger")
            return redirect(url_for("member_join"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO members
                       (first_name, last_name, other_names, phone, email, section, join_date,
                        dob, state_of_origin, lga, nin_number, academic_qualification,
                        country, passport_number, photo, notes)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (fn, ln, other_names, phone, email, section, date.today().strftime("%Y-%m-%d"),
                     dob, state_origin, lga, nin, qualification,
                     country, passport_number, photo_filename,
                     f"Self-registered via join form"))
        conn.commit()
        cur.execute("DELETE FROM phone_verifications WHERE phone=?", (phone,))
        conn.commit()
        conn.close()
        flash("Registration submitted successfully!", "success")
        return redirect(url_for("landing"))
    return render_template("member_join.html")


@app.route("/join/guidelines")
def join_guidelines():
    return render_template("join_guidelines.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("signup"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errs = []
        e = validate_required(username, "Username")
        if e:
            errs.append(e)
        if len(password) < 4:
            errs.append("Password must be at least 4 characters.")
        if password != confirm:
            errs.append("Passwords do not match.")

        if errs:
            for e in errs:
                flash(e, "danger")
            return redirect(url_for("signup"))

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                        (username, generate_password_hash(password), "viewer", date.today().strftime("%Y-%m-%d")))
            conn.commit()
            flash("Account created! You can now sign in.", "success")
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash(f"Username '{username}' is already taken.", "danger")
            conn.close()
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", csrf=generate_csrf)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if session.get("role") != "admin":
        flash("Only admins can manage users.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("users"))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "viewer")
        err = validate_required(username, "Username")
        if err:
            flash(err, "danger")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
        else:
            try:
                cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
                            (username, generate_password_hash(password), role, date.today().strftime("%Y-%m-%d")))
                conn.commit()
                flash(f"User '{username}' created!", "success")
            except sqlite3.IntegrityError:
                flash(f"Username '{username}' already exists.", "danger")
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
    users_list = cur.fetchall()
    conn.close()
    return render_template("users.html", users=users_list)


@app.route("/users/delete/<int:id>")
@login_required
def user_delete(id):
    if session.get("role") != "admin":
        flash("Only admins can delete users.", "danger")
        return redirect(url_for("dashboard"))
    if id == session["user_id"]:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for("users"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("User deleted.", "success")
    return redirect(url_for("users"))


# ─── Landing Page ─────────────────────────────────────────────────

@app.route("/")
def landing():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings WHERE key IN ('facebook_url','youtube_url','instagram_url','tiktok_url')")
    social_links = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return render_template("landing.html", social_links=social_links)


@app.route("/user-manual")
def user_manual():
    return render_template("user_manual.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


# ─── Dashboard ────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM members")
    total_members = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM payments")
    total_payments = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
    total_revenue = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
    total_present = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance")
    total_attendance = cur.fetchone()[0]
    attendance_rate = round((total_present / total_attendance * 100) if total_attendance > 0 else 0, 1)

    cur.execute("SELECT COUNT(*) FROM songs")
    total_songs = cur.fetchone()[0]

    cur.execute("""SELECT m.first_name, m.last_name, SUM(p.amount) as total
                   FROM payments p JOIN members m ON p.member_id = m.id
                   GROUP BY p.member_id ORDER BY total DESC LIMIT 5""")
    top_members = cur.fetchall()

    cur.execute("""SELECT m.first_name, m.last_name, p.amount, p.payment_date, p.payment_for
                   FROM payments p JOIN members m ON p.member_id = m.id
                   ORDER BY p.payment_date DESC LIMIT 5""")
    recent_payments = cur.fetchall()

    conn.close()
    return render_template("dashboard.html", total_members=total_members,
                           total_payments=total_payments, total_revenue=total_revenue,
                           attendance_rate=attendance_rate, total_songs=total_songs,
                           top_members=top_members, recent_payments=recent_payments)


# ─── Members ──────────────────────────────────────────────────────

@app.route("/members")
@login_required
def members():
    conn = get_db()
    cur = conn.cursor()
    search = request.args.get("search", "")
    if search:
        cur.execute("""SELECT * FROM members
                       WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
                       ORDER BY last_name, first_name""",
                    (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM members ORDER BY last_name, first_name")
    members = cur.fetchall()
    cur.execute("SELECT member_id, SUM(amount) FROM payments GROUP BY member_id")
    payment_totals = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return render_template("members.html", members=members, payment_totals=payment_totals, search=search)


@app.route("/members/add", methods=["GET", "POST"])
@login_required
def member_add():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members"))
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        join_date = request.form.get("join_date", "").strip()

        errs = []
        for v, n in [(fn, "First name"), (ln, "Last name"), (join_date, "Join date")]:
            e = validate_required(v, n)
            if e:
                errs.append(e)
        e = validate_email(email)
        if e:
            errs.append(e)

        photo_filename = ""
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(app.config["PHOTO_FOLDER"], photo_filename))

        if errs:
            for e in errs:
                flash(e, "danger")
            return redirect(url_for("member_add"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO members
                       (first_name, last_name, other_names, phone, email, section, join_date, address, notes,
                        dob, state_of_origin, lga, nin_number, academic_qualification,
                        country, passport_number, photo)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (fn, ln, request.form.get("other_names", "").strip(), request.form.get("phone", "").strip(), email,
                     request.form.get("section", "Soprano"), join_date,
                     request.form.get("address", "").strip(), request.form.get("notes", "").strip(),
                     request.form.get("dob", "").strip(), request.form.get("state_of_origin", "").strip(),
                     request.form.get("lga", "").strip(), request.form.get("nin_number", "").strip(),
                     request.form.get("academic_qualification", "").strip(),
                     request.form.get("country", "Nigeria").strip(),
                     request.form.get("passport_number", "").strip(), photo_filename))
        conn.commit()
        conn.close()
        flash("Member added successfully!", "success")
        return redirect(url_for("members"))
    return render_template("member_form.html", member=None, title="Add Member")


@app.route("/members/edit/<int:id>", methods=["GET", "POST"])
def member_edit(id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("members"))
        fn = request.form.get("first_name", "").strip()
        ln = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        join_date = request.form.get("join_date", "").strip()

        errs = []
        for v, n in [(fn, "First name"), (ln, "Last name"), (join_date, "Join date")]:
            e = validate_required(v, n)
            if e:
                errs.append(e)
        e = validate_email(email)
        if e:
            errs.append(e)

        photo_filename = request.form.get("existing_photo", "")
        if "photo" in request.files:
            f = request.files["photo"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1] or ".jpg"
                photo_filename = f"member_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                f.save(os.path.join(app.config["PHOTO_FOLDER"], photo_filename))
                old_photo = request.form.get("existing_photo", "")
                if old_photo:
                    old_path = os.path.join(app.config["PHOTO_FOLDER"], old_photo)
                    if os.path.isfile(old_path):
                        os.remove(old_path)

        if errs:
            for e in errs:
                flash(e, "danger")
            return redirect(url_for("member_edit", id=id))

        cur.execute("""UPDATE members SET first_name=?, last_name=?, other_names=?, phone=?, email=?, section=?,
                       join_date=?, address=?, notes=?,
                       dob=?, state_of_origin=?, lga=?, nin_number=?, academic_qualification=?,
                       country=?, passport_number=?, photo=?
                       WHERE id=?""",
                    (fn, ln, request.form.get("other_names", "").strip(), request.form.get("phone", "").strip(), email,
                     request.form.get("section", "Soprano"), join_date,
                     request.form.get("address", "").strip(), request.form.get("notes", "").strip(),
                     request.form.get("dob", "").strip(), request.form.get("state_of_origin", "").strip(),
                     request.form.get("lga", "").strip(), request.form.get("nin_number", "").strip(),
                     request.form.get("academic_qualification", "").strip(),
                     request.form.get("country", "Nigeria").strip(),
                     request.form.get("passport_number", "").strip(), photo_filename, id))
        conn.commit()
        conn.close()
        flash("Member updated!", "success")
        return redirect(url_for("members"))
    cur.execute("SELECT * FROM members WHERE id=?", (id,))
    member = cur.fetchone()
    conn.close()
    return render_template("member_form.html", member=member, title="Edit Member")


@app.route("/members/delete/<int:id>")
@login_required
def member_delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE member_id=?", (id,))
    cur.execute("DELETE FROM attendance WHERE member_id=?", (id,))
    cur.execute("DELETE FROM members WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Member deleted.", "success")
    return redirect(url_for("members"))


@app.route("/members/<int:id>")
@login_required
def member_detail(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM members WHERE id=?", (id,))
    member = cur.fetchone()
    if not member:
        conn.close()
        return redirect(url_for("members"))
    cur.execute("SELECT * FROM payments WHERE member_id=? ORDER BY payment_date DESC", (id,))
    payments = cur.fetchall()
    cur.execute("SELECT * FROM attendance WHERE member_id=? ORDER BY date DESC", (id,))
    attendance_records = cur.fetchall()
    conn.close()
    return render_template("member_detail.html", member=member, payments=payments, attendance=attendance_records)


# ─── Attendance ───────────────────────────────────────────────────

@app.route("/attendance")
@login_required
def attendance():
    conn = get_db()
    cur = conn.cursor()
    date_filter = request.args.get("date", date.today().strftime("%Y-%m-%d"))
    cur.execute("SELECT DISTINCT date FROM attendance ORDER BY date DESC")
    available_dates = [row["date"] for row in cur.fetchall()]
    cur.execute("""SELECT a.*, m.first_name, m.last_name, m.section
                   FROM attendance a JOIN members m ON a.member_id = m.id
                   WHERE a.date=? ORDER BY m.last_name, m.first_name""", (date_filter,))
    records = cur.fetchall()
    cur.execute("SELECT * FROM members ORDER BY last_name, first_name")
    members = cur.fetchall()
    conn.close()
    return render_template("attendance.html", records=records, members=members,
                           available_dates=available_dates, selected_date=date_filter)


@app.route("/attendance/take", methods=["POST"])
@login_required
def attendance_take():
    if not validate_csrf():
        return redirect(url_for("attendance"))
    date_val = request.form.get("date", "").strip()
    err = validate_required(date_val, "Date")
    if err:
        flash(err, "danger")
        return redirect(url_for("attendance"))
    member_ids = request.form.getlist("member_ids")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM attendance WHERE date=?", (date_val,))
    for mid in member_ids:
        if mid.isdigit():
            status = request.form.get(f"status_{mid}", "Present")
            cur.execute("INSERT INTO attendance (member_id, date, status) VALUES (?,?,?)",
                        (int(mid), date_val, status))
    conn.commit()
    conn.close()
    flash(f"Attendance for {date_val} saved!", "success")
    return redirect(url_for("attendance", date=date_val))


# ─── Finance / Payments ───────────────────────────────────────────

@app.route("/finance")
@login_required
def finance():
    conn = get_db()
    cur = conn.cursor()
    member_filter = request.args.get("member_id", "")
    if member_filter and member_filter.isdigit():
        cur.execute("""SELECT p.*, m.first_name, m.last_name FROM payments p
                       JOIN members m ON p.member_id = m.id
                       WHERE p.member_id=? ORDER BY p.payment_date DESC""", (int(member_filter),))
    else:
        cur.execute("""SELECT p.*, m.first_name, m.last_name FROM payments p
                       JOIN members m ON p.member_id = m.id
                       ORDER BY p.payment_date DESC""")
    payments = cur.fetchall()
    cur.execute("SELECT * FROM members ORDER BY last_name, first_name")
    members = cur.fetchall()
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
    total_collected = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments")
    total_count = cur.fetchone()[0]
    cur.execute("""SELECT m.first_name, m.last_name, COALESCE(SUM(p.amount), 0) as total
                   FROM members m LEFT JOIN payments p ON m.id=p.member_id
                   GROUP BY m.id ORDER BY total""")
    member_totals = cur.fetchall()
    conn.close()
    return render_template("finance.html", payments=payments, members=members,
                           total_collected=total_collected, total_count=total_count,
                           member_totals=member_totals, selected_member=member_filter)


@app.route("/finance/add", methods=["POST"])
@login_required
def finance_add():
    if not validate_csrf():
        return redirect(url_for("finance"))
    member_id = request.form.get("member_id", "").strip()
    amount_str = request.form.get("amount", "").strip()
    payment_date = request.form.get("payment_date", "").strip()

    errs = []
    for v, n in [(member_id, "Member"), (amount_str, "Amount"), (payment_date, "Date")]:
        e = validate_required(v, n)
        if e:
            errs.append(e)
    if not errs:
        e = validate_amount(amount_str)
        if e:
            errs.append(e)
    if errs:
        for e in errs:
            flash(e, "danger")
        return redirect(url_for("finance"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO payments (member_id, amount, payment_date, payment_for, notes)
                   VALUES (?,?,?,?,?)""",
                (int(member_id), float(amount_str), payment_date,
                 request.form.get("payment_for", "").strip(),
                 request.form.get("notes", "").strip()))
    conn.commit()
    conn.close()
    flash("Payment recorded!", "success")
    return redirect(url_for("finance"))


@app.route("/finance/delete/<int:id>")
@login_required
def finance_delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Payment deleted.", "success")
    return redirect(url_for("finance"))


# ─── Reports ──────────────────────────────────────────────────────

@app.route("/reports")
@login_required
def reports():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""SELECT m.first_name, m.last_name, m.section, m.join_date,
                   COALESCE(SUM(p.amount), 0) as total_paid,
                   COUNT(p.id) as payment_count
                   FROM members m LEFT JOIN payments p ON m.id=p.member_id
                   GROUP BY m.id ORDER BY m.last_name""")
    member_financials = cur.fetchall()
    cur.execute("""SELECT strftime('%Y-%m', payment_date) as month,
                   COUNT(*) as txns, SUM(amount) as total
                   FROM payments GROUP BY month ORDER BY month DESC""")
    monthly_summary = cur.fetchall()
    cur.execute("""SELECT section, COUNT(*) as count FROM members GROUP BY section""")
    section_counts = cur.fetchall()
    cur.execute("""SELECT a.status, COUNT(*) as count
                   FROM attendance a GROUP BY a.status""")
    attendance_summary = cur.fetchall()
    conn.close()
    return render_template("reports.html", member_financials=member_financials,
                           monthly_summary=monthly_summary, section_counts=section_counts,
                           attendance_summary=attendance_summary)


# ─── Export / Backup ──────────────────────────────────────────────

def _export_csv(columns, rows, filename):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[c] if row[c] is not None else "" for c in columns])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/export/members")
@login_required
def export_members():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM members ORDER BY last_name, first_name")
    rows = cur.fetchall()
    conn.close()
    return _export_csv(
        ["id", "first_name", "last_name", "other_names", "phone", "email", "section", "join_date", "address",
         "dob", "state_of_origin", "lga", "nin_number", "academic_qualification",
         "country", "passport_number", "notes"],
        rows, "members.csv"
    )


@app.route("/export/payments")
@login_required
def export_payments():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""SELECT p.id, m.first_name, m.last_name, p.amount, p.payment_date, p.payment_for, p.notes
                   FROM payments p JOIN members m ON p.member_id = m.id
                   ORDER BY p.payment_date DESC""")
    rows = cur.fetchall()
    conn.close()
    return _export_csv(
        ["id", "first_name", "last_name", "amount", "payment_date", "payment_for", "notes"],
        rows, "payments.csv"
    )


@app.route("/export/attendance")
@login_required
def export_attendance():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""SELECT a.id, m.first_name, m.last_name, a.date, a.status, a.notes
                   FROM attendance a JOIN members m ON a.member_id = m.id
                   ORDER BY a.date DESC""")
    rows = cur.fetchall()
    conn.close()
    return _export_csv(
        ["id", "first_name", "last_name", "date", "status", "notes"],
        rows, "attendance.csv"
    )


@app.route("/export/backup")
@login_required
def export_backup():
    conn = get_db()
    cur = conn.cursor()
    output = io.StringIO()
    for table in ["members", "payments", "attendance", "songs", "settings", "users"]:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        if not rows:
            continue
        columns = [desc[0] for desc in cur.description]
        output.write(f"--- {table} ---\n")
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[c] if row[c] is not None else "" for c in columns])
        output.write("\n")
    conn.close()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=choir_full_backup_{date.today().strftime('%Y%m%d')}.csv"}
    )


# ─── Settings ─────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("settings"))
        for key in ["choir_name", "currency", "dues_amount", "facebook_url", "youtube_url",
                     "instagram_url", "tiktok_url", "sms_provider", "twilio_account_sid",
                     "twilio_auth_token", "twilio_phone"]:
            val = request.form.get(key, "").strip()
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, val))
        conn.commit()
        conn.close()
        flash("Settings saved!", "success")
        return redirect(url_for("settings"))
    cur.execute("SELECT key, value FROM settings")
    all_settings = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return render_template("settings.html", settings_data=all_settings)


# ─── Songs ────────────────────────────────────────────────────────

@app.route("/songs")
@login_required
def songs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM songs ORDER BY upload_date DESC")
    songs = cur.fetchall()
    conn.close()
    return render_template("songs.html", songs=songs)


@app.route("/songs/add", methods=["GET", "POST"])
@login_required
def song_add():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("songs"))
        title = request.form.get("title", "").strip()
        err = validate_required(title, "Title")
        if err:
            flash(err, "danger")
            return redirect(url_for("song_add"))

        composer = request.form.get("composer", "").strip()
        lyrics = request.form.get("lyrics", "").strip()
        notes = request.form.get("notes", "").strip()

        audio_file = ""
        if "audio" in request.files:
            f = request.files["audio"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title.replace(' ', '_')}{ext}"
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                audio_file = filename

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO songs (title, composer, lyrics, audio_file, upload_date, notes)
                       VALUES (?,?,?,?,?,?)""",
                    (title, composer, lyrics, audio_file, date.today().strftime("%Y-%m-%d"), notes))
        conn.commit()
        conn.close()
        flash("Song added!", "success")
        return redirect(url_for("songs"))
    return render_template("song_form.html", song=None, title="Add Song")


@app.route("/songs/delete/<int:id>")
@login_required
def song_delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT audio_file FROM songs WHERE id=?", (id,))
    row = cur.fetchone()
    if row and row["audio_file"]:
        fp = os.path.join(app.config["UPLOAD_FOLDER"], row["audio_file"])
        if os.path.isfile(fp):
            os.remove(fp)
    cur.execute("DELETE FROM songs WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Song deleted.", "success")
    return redirect(url_for("songs"))


@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/member-photos/<filename>")
def member_photo(filename):
    return send_from_directory(app.config["PHOTO_FOLDER"], filename)


# ─── Social ───────────────────────────────────────────────────────

@app.route("/social")
@login_required
def social():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings WHERE key IN ('facebook_url','youtube_url','instagram_url','tiktok_url')")
    links = {row["key"]: row["value"] for row in cur.fetchall()}
    conn.close()
    return render_template("social.html", links=links)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
