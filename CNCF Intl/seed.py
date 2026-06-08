"""Seed the database with realistic mock data for testing and development."""

import os
import sys
from datetime import datetime, timedelta
from random import choice, randint, uniform, sample

from werkzeug.security import generate_password_hash

# Ensure the app context is available
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from models import db, User, Member, Document, MusicSheet, ServicePlan, Transaction, Setting

# ── Nigerian choir-appropriate names ──────────────────────────
FIRST_NAMES = [
    "Chioma", "Oluwaseun", "Ngozi", "Chidi", "Adebayo", "Funmi", "Emeka",
    "Zainab", "Kelechi", "Yemi", "Chinwe", "Tunde", "Adaeze", "Ebuka",
    "Ifeanyi", "Nkechi", "Olumide", "Simisola", "Chibueze", "Folake",
    "Ayodeji", "Chiamaka", "Obinna", "Yetunde", "Somtochukwu", "Ejiro",
    "Chinyere", "Oluwafemi", "Amara", "Ikenna", "Bolanle", "Onome",
    "Chisom", "Tolulope", "Arinze", "Kemi", "Uchenna", "Damilola",
    "Chigozie", "Moyinoluwa", "Akintunde", "Ifeoluwa", "Oluchi", "Onyekachi",
    "Faith", "David", "Esther", "Samuel", "Grace", "Daniel",
    "Blessing", "Emmanuel", "Priscilla", "Michael", "Deborah", "Joseph",
    "Ruth", "Joshua", "Hannah", "Solomon",
]

LAST_NAMES = [
    "Adebayo", "Okonkwo", "Okafor", "Eze", "Nwachukwu", "Bamidele",
    "Ogunlade", "Ibrahim", "Onyema", "Adegoke", "Chukwu", "Oluwaseun",
    "Adeyemi", "Nwosu", "Ogunbiyi", "Ekene", "Ogundipe", "Okoro",
    "Akinwale", "Ibekwe", "Oshodi", "Fadipe", "Oyediran", "Ugwu",
    "Adeleke", "Ezeh", "Ogunyemi", "Nnamdi", "Ogunsanya", "Akinola",
    "Mensah", "Afari", "Oppong", "Amoako", "Donkor", "Darkwah",
    "Sarpong", "Owusu", "Asante", "Osei", "Boateng", "Adjei",
]

SECTIONS = ["Treble", "Alto", "Tenor", "Bass"]
ROLES = ["Choir Leader", "Section Lead", "Member", "Member", "Member"]

NATIONS = ["Nigeria", "Ghana", "Cameroon", "Benin", "Togo", "Cote", "USA", "UK", "Other"]

# States with their areas (matching locationData in the form JS)
STATES = [
    ("Abia", ["Umuahia", "Aba", "Ohafia"]),
    ("Adamawa", ["Yola", "Mubi", "Numan"]),
    ("Akwa Ibom", ["Uyo", "Ikot Ekpene", "Eket"]),
    ("Anambra", ["Awka", "Onitsha", "Nnewi"]),
    ("Bauchi", ["Bauchi", "Katagum"]),
    ("Cross River", ["Calabar", "Ikom", "Ogoja", "Obudu"]),
    ("Delta", ["Warri", "Asaba", "Sapele"]),
    ("Edo", ["Benin", "Auchi"]),
    ("Ekiti", ["Ado Ekiti", "Ikere"]),
    ("Enugu", ["Enugu", "Nsukka"]),
    ("FCT", ["Abuja", "Bwari"]),
    ("Imo", ["Owerri", "Orlu", "Okigwe"]),
    ("Kaduna", ["Kaduna", "Zaria", "Kafanchan"]),
    ("Kano", ["Kano", "Wudil", "Rano"]),
    ("Lagos", ["Ikeja", "Badagry", "Ikorodu", "Epe"]),
    ("Ogun", ["Abeokuta", "Ijebu Ode", "Sagamu"]),
    ("Ondo", ["Akure", "Ondo", "Owo"]),
    ("Osun", ["Osogbo", "Ife", "Ilesa"]),
    ("Oyo", ["Ibadan", "Ogbomoso", "Iseyin"]),
    ("Plateau", ["Jos", "Pankshin"]),
    ("Rivers", ["Port Harcourt", "Obio/Akpor", "Bonny"]),
    ("Sokoto", ["Sokoto", "Tambuwal"]),
    ("Taraba", ["Jalingo", "Wukari"]),
]
ZONES = ["Zone 1", "Zone 2", "Zone A", "Zone B", "Zone North", "Zone South"]
BETHELS = ["Bethel A", "Bethel B", "Bethel C", "Bethel D", "Bethel E"]

MUSIC_TITLES = [
    ("Great Is Thy Faithfulness", "Thomas Chisholm", "William Runyan"),
    ("Amazing Grace", "John Newton", "Edwin O. Excell"),
    ("How Great Thou Art", "Carl Boberg", "Stuart K. Hine"),
    ("It Is Well With My Soul", "Horatio Spafford", "Philip Bliss"),
    ("The Old Rugged Cross", "George Bennard", "George Bennard"),
    ("Blessed Assurance", "Fanny Crosby", "Phoebe Knapp"),
    ("Holy, Holy, Holy", "Reginald Heber", "John Bacchus Dykes"),
    ("What a Friend We Have in Jesus", "Joseph Scriven", "Charles Crozat Converse"),
    ("O Come, O Come, Emmanuel", "Latin Hymn", "Thomas Helmore"),
    ("Hallelujah Chorus", "G.F. Handel", "G.F. Handel"),
    ("Ave Maria", "Franz Schubert", "Franz Schubert"),
    ("Panis Angelicus", "César Franck", "César Franck"),
    ("Gloria in Excelsis Deo", "Traditional", "Vivaldi"),
    ("Jubilate Deo", "John Rutter", "John Rutter"),
    ("The Lord Bless You", "John Rutter", "John Rutter"),
    ("Be Thou My Vision", "Irish Hymn", "Traditional"),
    ("Jesus, Joy of Man's Desiring", "J.S. Bach", "J.S. Bach"),
    ("Nigerian National Anthem", "Benedict Odiase", "Benedict Odiase"),
    ("O Worship the King", "Robert Grant", "J. Michael Haydn"),
    ("All Creatures of Our God and King", "Francis of Assisi", "Ralph Vaughan Williams"),
    ("Crown Him with Many Crowns", "Matthew Bridges", "George J. Elvey"),
    ("Fairest Lord Jesus", "Traditional", "Traditional"),
    ("Nearer, My God, to Thee", "Sarah F. Adams", "Lowell Mason"),
    ("Rock of Ages", "Augustus Toplady", "Thomas Hastings"),
    ("Stand Up, Stand Up for Jesus", "George Duffield Jr.", "Adam Geibel"),
]

CATEGORIES = ["sheet_music", "hymn", "anthem", "gospel", "classical"]
SECTION_TAGS = ["S,A,T,B", "S,A,T", "S,A", "T,B", "S,A,T,B", "S,T,B"]

DOC_TITLES = [
    ("BCS CNCF Constitution", "pdf", "240 KB"),
    ("Annual General Report 2025", "pdf", "1.2 MB"),
    ("Choir Bylaws (Revised)", "docx", "180 KB"),
    ("Voice Section Handbook", "pdf", "890 KB"),
    ("Rehearsal Schedule Q4", "xlsx", "64 KB"),
    ("Attendance Register Template", "xlsx", "48 KB"),
    ("Music Manuscript - Gloria", "pdf", "4.2 MB"),
    ("Membership Directory", "pdf", "3.1 MB"),
    ("Budget Proposal 2026", "xlsx", "120 KB"),
    ("Event Planning Checklist", "docx", "96 KB"),
    ("Choir Robe Inventory", "xlsx", "72 KB"),
    ("Safety & Fire Drill Protocol", "pdf", "560 KB"),
    ("Pastoral Support Roster", "docx", "104 KB"),
    ("Media Consent Forms", "pdf", "380 KB"),
    ("Annual Financial Statement", "pdf", "2.4 MB"),
]

DOC_FOLDERS = [
    "Organizational Constitutions",
    "Music Manuscripts",
    "Choir Bylaws",
    "Reports & Minutes",
    "Administrative Forms",
]

SERVICE_TITLES = [
    ("Sunday Morning Worship", "Main Sanctuary"),
    ("Evening Choral Vespers", "Chapel Hall"),
    ("Youth Choir Rehearsal", "Music Room"),
    ("Section Leader Workshop", "Conference Room"),
    ("Anniversary Preparation", "Main Sanctuary"),
    ("Easter Cantata Rehearsal", "Chapel Hall"),
    ("Community Outreach Concert", "Town Hall"),
    ("Music Theory Clinic", "Classroom B"),
    ("Interdenominational Choir Fest", "Civic Center"),
    ("End-of-Year Concert", "Auditorium"),
    ("Choir Retreat Planning", "Retreat Center"),
    ("Weekly Section Practice", "Music Room"),
]

TRANS_CATEGORIES = [
    ("Donation", "income"),
    ("Tithe", "income"),
    ("Offering", "income"),
    ("Grant", "income"),
    ("Choir Dues", "income"),
    ("Equipment Purchase", "expense"),
    ("Transport", "expense"),
    ("Refreshments", "expense"),
    ("Printing & Stationery", "expense"),
    ("Music Licensing", "expense"),
    ("Uniform Maintenance", "expense"),
    ("Event Catering", "expense"),
]


def seed():
    with app.app_context():
        # Drop and recreate all tables to pick up schema changes
        db.drop_all()
        db.create_all()

        # ── Ensure admin exists ──────────────────────────
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                display_name="Admin Director",
                role="admin",
                status="approved",
                created_at="2024-01-15",
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user (admin / admin123)")
        else:
            print("Admin user already exists")

        # ── Settings ─────────────────────────────────────
        if not Setting.query.filter_by(key="org_name").first():
            db.session.add(Setting(key="org_name", value="BCS CNCF International"))
            db.session.commit()

        # ── Members (60) ─────────────────────────────────
        existing = Member.query.count()
        if existing >= 60:
            print(f"Members already seeded ({existing})")
        else:
            to_add = 60 - existing
            for i in range(to_add):
                fn = choice(FIRST_NAMES)
                ln = choice(LAST_NAMES)
                section = choice(SECTIONS)
                role = choice(ROLES)
                join = datetime(2024, 1, 1) + timedelta(days=randint(0, 500))
                s_name, areas = choice(STATES)
                area = choice(areas)
                zone = choice(ZONES)
                m = Member(
                    first_name=fn,
                    last_name=ln,
                    email=f"{fn.lower()}.{ln.lower()}@choir.org",
                    phone=f"+234-80{randint(20000000, 99999999)}",
                    section=section,
                    role=role,
                    join_date=join.strftime("%Y-%m-%d"),
                    address=f"{randint(1, 50)}, {choice(['Peace Avenue', 'Kingston Road', 'Chapel Street', 'Melody Close', 'Harmony Lane'])}",
                    nation="Nigeria",
                    state=s_name,
                    area=area,
                    zone=zone,
                    bethel=choice(BETHELS),
                    is_active=choice([True, True, True, False]),
                    created_at=join.strftime("%Y-%m-%d %H:%M:%S"),
                )
                db.session.add(m)
            db.session.commit()
            print(f"Seeded {to_add} members (total: {Member.query.count()})")

        # ── Music Sheets (25) ────────────────────────────
        existing = MusicSheet.query.count()
        if existing >= 25:
            print(f"Music sheets already seeded ({existing})")
        else:
            to_add = 25 - existing
            for title, composer, arranger in MUSIC_TITLES[:to_add]:
                ms = MusicSheet(
                    title=title,
                    composer=composer,
                    arranger=arranger,
                    lyrics=f"Lyrics for {title}...\n\nVerse 1\nLorem ipsum dolor sit amet.\n\nVerse 2\nConsectetur adipiscing elit.",
                    key=choice(["C", "D", "Eb", "F", "G", "Ab", "Bb"]),
                    tempo=choice(["Andante", "Moderato", "Allegro", "Maestoso", "Adagio"]),
                    file=f"sheets/{title.lower().replace(' ', '_')}.pdf",
                    category=choice(CATEGORIES),
                    sections=choice(SECTION_TAGS),
                    duration=f"{randint(3, 6)}:{randint(10, 59):02d}",
                    uploaded_by=admin.id,
                    created_at=(datetime(2024, 6, 1) + timedelta(days=randint(0, 365))).strftime("%Y-%m-%d %H:%M:%S"),
                )
                db.session.add(ms)
            db.session.commit()
            print(f"Seeded {to_add} music sheets (total: {MusicSheet.query.count()})")

        # ── Documents (15) ───────────────────────────────
        existing = Document.query.count()
        if existing >= 15:
            print(f"Documents already seeded ({existing})")
        else:
            to_add = 15 - existing
            for title, ftype, fsize in DOC_TITLES[:to_add]:
                doc = Document(
                    title=title,
                    filename=f"{title.lower().replace(' ', '_')}.{ftype}",
                    file_type=ftype.upper(),
                    file_size=fsize,
                    folder=choice(DOC_FOLDERS),
                    permissions=choice(["Standard", "Admin Only", "Public"]),
                    description=f"{title} — official document for BCS CNCF choir administration.",
                    uploaded_by=admin.id,
                    uploaded_at=(datetime(2024, 3, 1) + timedelta(days=randint(0, 400))).strftime("%Y-%m-%d"),
                )
                db.session.add(doc)
            db.session.commit()
            print(f"Seeded {to_add} documents (total: {Document.query.count()})")

        # ── Service Plans (12) ───────────────────────────
        existing = ServicePlan.query.count()
        if existing >= 12:
            print(f"Service plans already seeded ({existing})")
        else:
            to_add = 12 - existing
            for title, location in SERVICE_TITLES[:to_add]:
                d = datetime(2025, 1, 1) + timedelta(days=randint(0, 365))
                sp = ServicePlan(
                    title=title,
                    date=d.strftime("%Y-%m-%d"),
                    description=f"Scheduled {title.lower()} at {location}.",
                    location=location,
                    conductor=choice(["Mr. Adeyemi", "Dr. Okafor", "Mrs. Eze", "Prof. Okonkwo"]),
                    songs_list=", ".join([t[0] for t in sample(MUSIC_TITLES, min(5, len(MUSIC_TITLES)))]),
                    notes="All members kindly arrive 30 minutes early for sound check.",
                    created_by=admin.id,
                    created_at=(d - timedelta(days=randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
                )
                db.session.add(sp)
            db.session.commit()
            print(f"Seeded {to_add} service plans (total: {ServicePlan.query.count()})")

        # ── Transactions (25) ────────────────────────────
        existing = Transaction.query.count()
        if existing >= 25:
            print(f"Transactions already seeded ({existing})")
        else:
            to_add = 25 - existing
            for _ in range(to_add):
                label, ttype = choice(TRANS_CATEGORIES)
                amt = round(uniform(500, 50000) if ttype == "income" else uniform(200, 15000), 2)
                d = datetime(2025, 1, 1) + timedelta(days=randint(0, 150))
                tx = Transaction(
                    type=ttype,
                    amount=amt,
                    description=label,
                    date=d.strftime("%Y-%m-%d"),
                    category=label,
                    recorded_by=admin.id,
                    created_at=d.strftime("%Y-%m-%d %H:%M:%S"),
                )
                db.session.add(tx)
            db.session.commit()
            print(f"Seeded {to_add} transactions (total: {Transaction.query.count()})")

        print("\n-- Database seeding complete! --")


if __name__ == "__main__":
    seed()
