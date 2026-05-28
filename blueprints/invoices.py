import os
from datetime import datetime, date
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response, current_app
from utils import login_required, validate_csrf, validate_required, log_audit
from models import db, Member, Payment, Invoice, InvoiceItem, Setting
from fpdf import FPDF
from sqlalchemy import desc

bp = Blueprint("invoices", __name__)


def generate_invoice_number():
    last = Invoice.query.order_by(desc(Invoice.id)).first()
    num = (last.id + 1) if last else 1
    return f"INV-{datetime.now().strftime('%Y%m')}-{num:04d}"


@bp.route("/invoices")
@login_required
def invoices():
    all_invoices = Invoice.query.order_by(desc(Invoice.id)).all()
    return render_template("invoices.html", invoices=all_invoices)


@bp.route("/invoices/create", methods=["GET", "POST"])
@login_required
def invoice_create():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("invoices.invoices"))
        member_id = request.form.get("member_id", "").strip()
        issue_date = request.form.get("issue_date", "").strip()
        due_date = request.form.get("due_date", "").strip()
        notes = request.form.get("notes", "").strip()

        errs = []
        for v, n in [(member_id, "Member"), (issue_date, "Issue date"), (due_date, "Due date")]:
            e = validate_required(v, n)
            if e: errs.append(e)

        descriptions = request.form.getlist("item_description[]")
        quantities = request.form.getlist("item_quantity[]")
        unit_prices = request.form.getlist("item_unit_price[]")

        if not descriptions or not any(d.strip() for d in descriptions):
            errs.append("At least one invoice item is required")

        if errs:
            for e in errs: flash(e, "danger")
            return redirect(url_for("invoices.invoice_create"))

        items = []
        for i, desc in enumerate(descriptions):
            d = desc.strip()
            if not d:
                continue
            qty = int(quantities[i]) if i < len(quantities) and quantities[i].strip() else 1
            up = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i].strip() else 0
            items.append((d, qty, up))

        subtotal = sum(q * up for _, q, up in items)
        total = subtotal

        inv = Invoice(
            invoice_number=generate_invoice_number(),
            member_id=int(member_id),
            issue_date=issue_date,
            due_date=due_date,
            status="unpaid",
            subtotal=subtotal,
            total=total,
            paid_amount=0,
            notes=notes,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(inv)
        db.session.flush()

        for desc, qty, up in items:
            db.session.add(InvoiceItem(
                invoice_id=inv.id,
                description=desc,
                quantity=qty,
                unit_price=up,
                amount=qty * up
            ))

        db.session.commit()
        log_audit("create", "invoice", inv.id, f"Invoice {inv.invoice_number}: {inv.total:.2f}")
        flash(f"Invoice {inv.invoice_number} created!", "success")
        return redirect(url_for("invoices.invoice_view", id=inv.id))

    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    return render_template("invoice_form.html", invoice=None, members=members)


@bp.route("/invoices/<int:id>")
@login_required
def invoice_view(id):
    inv = db.session.get(Invoice, id)
    if not inv:
        flash("Invoice not found.", "danger")
        return redirect(url_for("invoices.invoices"))
    return render_template("invoice_view.html", invoice=inv)


@bp.route("/invoices/<int:id>/delete")
@login_required
def invoice_delete(id):
    inv = db.session.get(Invoice, id)
    if inv:
        db.session.delete(inv)
        db.session.commit()
        log_audit("delete", "invoice", id, f"Deleted invoice {inv.invoice_number}")
        flash("Invoice deleted.", "success")
    return redirect(url_for("invoices.invoices"))


@bp.route("/invoices/<int:id>/mark-paid")
@login_required
def invoice_mark_paid(id):
    inv = db.session.get(Invoice, id)
    if inv:
        if inv.status == "paid":
            flash("Invoice is already paid.", "info")
        else:
            inv.status = "paid"
            inv.paid_amount = inv.total
            db.session.commit()
            log_audit("update", "invoice", id, f"Marked {inv.invoice_number} as paid")
            flash(f"Invoice {inv.invoice_number} marked as paid.", "success")
    return redirect(url_for("invoices.invoice_view", id=id))


@bp.route("/invoices/<int:id>/pdf/<which>")
@login_required
def invoice_pdf(id, which):
    inv = db.session.get(Invoice, id)
    if not inv:
        flash("Invoice not found.", "danger")
        return redirect(url_for("invoices.invoices"))

    currency = (db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$")
    choir_name = (db.session.get(Setting, "choir_name").value if db.session.get(Setting, "choir_name") else "CHOIR")
    is_receipt = which == "receipt"

    pdf = FPDF()
    pdf.add_page()

    pdf.set_draw_color(233, 69, 96)
    pdf.set_line_width(0.6)
    pdf.rect(5, 5, pdf.w - 10, pdf.h - 10)
    pdf.set_line_width(0.3)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(6, 6, pdf.w - 12, pdf.h - 12)

    logo_path = current_app.root_path + "/static/logo_watermark.png"

    pdf.set_fill_color(233, 69, 96)
    pdf.rect(6, 6, pdf.w - 12, 28, "F")

    if os.path.exists(logo_path):
        pdf.image(logo_path, x=8, y=7, w=14)

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(26, 10)
    pdf.cell(0, 8, choir_name)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(26, 20)
    label = "RECEIPT / PAYMENT CONFIRMATION" if is_receipt else "INVOICE / PROFORMA INVOICE"
    pdf.cell(0, 8, label)

    pdf.set_y(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pdf.w - 12, 8, inv.invoice_number, align="R")

    status_colors = {"paid": (46, 125, 50), "unpaid": (230, 81, 0), "partial": (245, 124, 0), "cancelled": (198, 40, 40)}
    sc = status_colors.get(inv.status, (100, 100, 100))
    pdf.set_fill_color(*sc)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_y(18)
    pdf.cell(pdf.w - 12, 7, f"  {inv.status.upper()}  ", align="R", fill=True)

    pdf.set_y(36)
    pdf.set_draw_color(233, 69, 96)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())

    pdf.set_text_color(0, 0, 0)
    cur_y = 40

    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(26, 26, 46)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 6, "  BILL TO", fill=True)
    pdf.set_xy(105, cur_y)
    pdf.cell(0, 6, "  INVOICE DETAILS", fill=True)
    cur_y += 8

    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 5, f"  {inv.member.first_name} {inv.member.last_name}")
    pdf.set_xy(105, cur_y)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(35, 5, "Issue Date:")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, inv.issue_date)
    cur_y += 5

    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(90, 5, f"  {inv.member.phone or ''}")
    pdf.set_xy(105, cur_y)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(35, 5, "Due Date:")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, inv.due_date)
    cur_y += 5

    if inv.member.email:
        pdf.set_xy(10, cur_y)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(90, 5, f"  {inv.member.email}")
        cur_y += 5

    cur_y += 4
    col_w = [80, 20, 40, 40]
    row_h = 7
    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    for txt, w, a in [("  DESCRIPTION", col_w[0], "L"), ("QTY", col_w[1], "C"), ("UNIT PRICE", col_w[2], "C"), ("AMOUNT", col_w[3], "C")]:
        pdf.cell(w, row_h, txt, border=1, fill=True, align=a)
    cur_y += row_h

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    alt = False
    for item in inv.items:
        pdf.set_xy(10, cur_y)
        pdf.set_fill_color(248, 248, 252) if alt else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 6, f"  {item.description[:48]}", border=1, fill=True)
        pdf.cell(col_w[1], 6, str(item.quantity), border=1, align="C", fill=True)
        pdf.cell(col_w[2], 6, f"{currency}{item.unit_price:.2f}", border=1, align="C", fill=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(col_w[3], 6, f"{currency}{item.amount:.2f}", border=1, align="C", fill=True)
        pdf.set_font("Helvetica", "", 9)
        cur_y += 6
        alt = not alt

    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(sum(col_w[:3]), 9, "  TOTAL", border=1, fill=True)
    pdf.cell(col_w[3], 9, f"{currency}{inv.total:.2f}", border=1, fill=True, align="C")
    cur_y += 11

    if is_receipt or inv.paid_amount > 0:
        pdf.set_xy(10, cur_y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(232, 245, 233)
        pdf.set_text_color(46, 125, 50)
        pdf.cell(sum(col_w[:3]), 7, "  PAID AMOUNT", border=1, fill=True)
        pdf.cell(col_w[3], 7, f"{currency}{inv.paid_amount:.2f}", border=1, fill=True, align="C")
        cur_y += 7

        bal = max(0, inv.total - inv.paid_amount)
        pdf.set_xy(10, cur_y)
        if bal == 0:
            pdf.set_fill_color(232, 245, 233)
            pdf.set_text_color(46, 125, 50)
            lbl, val = "  BALANCE CLEARED", f"{currency}0.00"
        else:
            pdf.set_fill_color(255, 235, 238)
            pdf.set_text_color(198, 40, 40)
            lbl, val = "  BALANCE DUE", f"{currency}{bal:.2f}"
        pdf.cell(sum(col_w[:3]), 7, lbl, border=1, fill=True)
        pdf.cell(col_w[3], 7, val, border=1, fill=True, align="C")
        cur_y += 10

    cur_y += 3
    pdf.set_xy(10, cur_y)
    pdf.set_font("Helvetica", "I", 10)
    if is_receipt or inv.status == "paid":
        pdf.set_text_color(46, 125, 50)
        pdf.cell(0, 6, "Thank you for your payment. This document serves as your official receipt.")
    else:
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Please make payment by {inv.due_date}. Thank you for your patronage.")
    cur_y += 8

    if inv.notes:
        pdf.set_xy(10, cur_y)
        pdf.set_fill_color(255, 248, 225)
        pdf.set_text_color(100, 80, 0)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, f"  Notes: {inv.notes}", fill=True)

    pdf.set_y(-25)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.set_y(-22)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 4, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  {choir_name}  |  {inv.invoice_number}", align="C")

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    suf = "receipt" if is_receipt else "invoice"
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={inv.invoice_number}_{suf}.pdf"})
