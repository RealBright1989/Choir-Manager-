from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from sqlalchemy import extract, func
from utils import login_required
from models import db, Member, Transaction, ServicePlan, Report, User
from fpdf import FPDF

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("/")
@login_required
def index():
    now = datetime.now()

    total_members = Member.query.count()
    total_reports = Report.query.count()

    # KPI: Section distribution (used for attendance-style progress bars)
    sections_order = ["Treble", "Alto", "Tenor", "Bass"]
    section_counts = {}
    total_sec = 0
    for s in sections_order:
        cnt = Member.query.filter_by(section=s).count()
        section_counts[s] = cnt
        total_sec += cnt
    if total_sec == 0:
        total_sec = 1

    # KPI: Monthly revenue (sum of current month's transactions)
    month_start = now.strftime("%Y-%m") + "-01"
    monthly_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.date >= month_start,
        Transaction.type == "income",
    ).scalar() or 0

    # KPI: Completed events (ServicePlans)
    total_events = ServicePlan.query.count()

    # Membership growth by month (last 6 months)
    months_labels = []
    months_data = []
    for i in range(5, -1, -1):
        month = now.month - i
        year = now.year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        label = datetime(year, month, 1).strftime("%b")
        months_labels.append(label)
        prefix = f"{year}-{month:02d}"
        cnt = Member.query.filter(Member.join_date.startswith(prefix)).count()
        months_data.append(cnt)

    max_month = max(months_data) if months_data else 1

    # Reports from database
    db_reports = Report.query.order_by(Report.id.desc()).all()
    reports_data = []
    for r in db_reports:
        author_name = r.creator.display_name if r.creator else "System"
        reports_data.append({
            "id": r.id,
            "name": r.title,
            "category": r.category or "General",
            "date": r.created_at or "",
            "author": author_name,
            "initials": r.author_initials or author_name[0].upper(),
            "color": r.color,
            "icon": r.icon,
        })

    return render_template("reports.html",
        total_reports=total_reports,
        total_members=total_members,
        section_counts=section_counts,
        total_sec=total_sec,
        monthly_revenue=monthly_revenue,
        total_events=total_events,
        months_labels=months_labels,
        months_data=months_data,
        max_month=max_month,
        reports_data=reports_data,
        sections_order=sections_order,
    )


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    user = User.query.get(session.get("user_id"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "General")
        content = request.form.get("content", "").strip()
        if not title:
            return render_template("report_form.html", error="Title is required.")
        initials = "".join(w[0].upper() for w in user.display_name.split() if w) if user else "A"
        report = Report(
            title=title, category=category, content=content,
            author_initials=initials,
            created_by=user.id if user else None,
            created_at=datetime.now().strftime("%b %d, %Y"),
        )
        db.session.add(report)
        db.session.commit()
        return redirect(url_for("reports.index"))
    return render_template("report_form.html", report=None, error=None)


@bp.route("/edit/<int:report_id>", methods=["GET", "POST"])
@login_required
def edit(report_id):
    report = Report.query.get_or_404(report_id)
    if request.method == "POST":
        report.title = request.form.get("title", "").strip()
        report.category = request.form.get("category", "General")
        report.content = request.form.get("content", "").strip()
        db.session.commit()
        return redirect(url_for("reports.index"))
    return render_template("report_form.html", report=report, error=None)


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "BROTHERHOOD OF THE CROSS AND STAR", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, "Abuja General Fellowship (AGF) - State Fellowships Termly Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


@bp.route("/pdf")
@login_required
def pdf_all():
    now = datetime.now()
    total_members = Member.query.count()
    active_members = Member.query.filter_by(is_active=True).count()
    total_reports = Report.query.count()
    total_events = ServicePlan.query.count()
    month_start = now.strftime("%Y-%m") + "-01"
    monthly_revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.date >= month_start, Transaction.type == "income",
    ).scalar() or 0
    reports = Report.query.order_by(Report.id.desc()).all()

    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Reports & Analytics - {now.strftime('%B %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # KPI Section
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Key Performance Indicators", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Total Members: {total_members}  |  Active: {active_members}  |  Reports: {total_reports}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Monthly Revenue: ${monthly_revenue:,.0f}  |  Completed Events: {total_events}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Section Distribution
    sections_order = ["Treble", "Alto", "Tenor", "Bass"]
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Section Distribution", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for s in sections_order:
        cnt = Member.query.filter_by(section=s).count()
        pdf.cell(0, 6, f"{s}: {cnt} members", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Reports Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Detailed Reports", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    col_w = [60, 30, 30, 40, 30]
    headers = ["Report Name", "Category", "Date", "Author", "Status"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for r in reports:
        author = r.creator.display_name if r.creator else "System"
        pdf.cell(col_w[0], 6, r.title[:30], border=1)
        pdf.cell(col_w[1], 6, r.category or "General", border=1)
        pdf.cell(col_w[2], 6, r.created_at or "", border=1)
        pdf.cell(col_w[3], 6, author[:18], border=1)
        pdf.cell(col_w[4], 6, "Submitted", border=1)
        pdf.ln()
        if pdf.get_y() > 260:
            pdf.add_page()

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"BCS_CNCF_Report_{now.strftime('%Y%m%d')}.pdf")


@bp.route("/pdf/<int:report_id>")
@login_required
def pdf_single(report_id):
    report = Report.query.get_or_404(report_id)
    author = report.creator.display_name if report.creator else "System"

    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, report.title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Category: {report.category or 'General'}  |  Author: {author}  |  {report.created_at or ''}", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, report.content or "(No content)")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%b %d, %Y %I:%M %p')}", new_x="LMARGIN", new_y="NEXT")

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    safe_name = report.title.replace(" ", "_").replace("/", "_")[:50]
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"{safe_name}.pdf")
