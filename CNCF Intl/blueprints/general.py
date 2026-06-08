from datetime import datetime, date
from flask import Blueprint, render_template
from sqlalchemy import extract
from utils import login_required
from models import db, Member, Document, MusicSheet, ServicePlan, Transaction


bp = Blueprint("general", __name__)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    total_members = Member.query.filter_by(is_active=True).count()
    total_members_all = Member.query.count()
    total_documents = Document.query.count()
    total_music = MusicSheet.query.count()
    total_services = ServicePlan.query.count()

    recent_members = Member.query.order_by(Member.id.desc()).limit(5).all()

    sections = {"Treble": 0, "Alto": 0, "Tenor": 0, "Bass": 0}
    members_all = Member.query.all()
    for m in members_all:
        s = m.section if m.section else "Treble"
        if s in sections:
            sections[s] += 1
    total_sec = sum(sections.values()) or 1
    birthdays_today = Member.query.filter(
        extract("month", Member.date_of_birth) == date.today().month,
        extract("day", Member.date_of_birth) == date.today().day
    ).count() if hasattr(Member, "date_of_birth") else 0

    stats = {
        "member_growth": 12, "active_members": total_members,
        "active_growth": 4, "active_target": "1,200",
        "new_registrations": len([m for m in recent_members if m.is_active]),
        "registration_decline": 2,
        "attendance_growth": 5, "attendance_rate": 94.2,
        "rehearsals": total_services,
        "birthdays": birthdays_today,
        "soprano_pct": round(sections["Treble"] / total_sec * 100),
        "alto_pct": round(sections["Alto"] / total_sec * 100),
        "tenor_pct": round(sections["Tenor"] / total_sec * 100),
        "bass_pct": round(sections["Bass"] / total_sec * 100),
    }

    announcements = [
        {"title": "Grand Anniversary Concert", "body": "Rehearsals scheduled for all sections this Saturday at 10 AM. Mandatory attendance.", "time": "2 hours ago", "color": "var(--secondary)"},
        {"title": "New Sheet Music Uploaded", "body": "The 'Hallelujah Chorus' arrangement has been updated. Please download the latest PDF.", "time": "Yesterday", "color": "var(--outline-variant)"},
        {"title": "Uniform Inspection", "body": "Section leaders to conduct uniform checks before next service.", "time": "3 days ago", "color": "var(--outline-variant)"},
    ]

    upcoming = [
        {"month": "OCT", "day": "15", "title": "Section Leader Meeting", "detail": "Conference Hall • 5:00 PM"},
        {"month": "OCT", "day": "18", "title": "Youth Choir Workshop", "detail": "Main Chapel • 2:00 PM"},
    ]

    return render_template("dashboard.html",
        total_members=total_members_all,
        total_members_all=total_members_all,
        total_documents=total_documents,
        total_music=total_music,
        total_services=total_services,
        recent_members=recent_members,
        stats=stats,
        announcements=announcements,
        upcoming=upcoming)
