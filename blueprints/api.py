from datetime import datetime, date
from flask import Blueprint, jsonify, request
from utils import login_required
from models import db, Member, Payment, Attendance, Invoice, InvoiceItem, Expense, Song, User

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/members")
@login_required
def api_members():
    members = Member.query.order_by(Member.last_name).all()
    return jsonify([{
        "id": m.id, "first_name": m.first_name, "last_name": m.last_name,
        "phone": m.phone, "email": m.email, "section": m.section,
        "join_date": m.join_date, "country": m.country or "Nigeria",
        "state_of_origin": m.state_of_origin, "lga": m.lga,
        "nin_number": m.nin_number, "zone": m.zone, "area": m.area,
        "photo": m.photo, "dob": m.dob,
    } for m in members])


@bp.route("/members/<int:id>")
@login_required
def api_member(id):
    m = db.session.get(Member, id)
    if not m:
        return jsonify({"error": "Member not found"}), 404
    return jsonify({
        "id": m.id, "first_name": m.first_name, "last_name": m.last_name,
        "other_names": m.other_names, "phone": m.phone, "email": m.email,
        "section": m.section, "join_date": m.join_date, "address": m.address,
        "dob": m.dob, "country": m.country or "Nigeria",
        "state_of_origin": m.state_of_origin, "lga": m.lga,
        "nin_number": m.nin_number, "academic_qualification": m.academic_qualification,
        "passport_number": m.passport_number, "zone": m.zone, "area": m.area,
        "photo": m.photo,
    })


@bp.route("/payments")
@login_required
def api_payments():
    member_id = request.args.get("member_id", type=int)
    q = Payment.query
    if member_id:
        q = q.filter_by(member_id=member_id)
    payments = q.order_by(Payment.payment_date.desc()).all()
    return jsonify([{
        "id": p.id, "member_id": p.member_id, "amount": p.amount,
        "payment_date": p.payment_date, "payment_for": p.payment_for,
        "notes": p.notes, "invoice_id": p.invoice_id,
    } for p in payments])


@bp.route("/invoices")
@login_required
def api_invoices():
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    return jsonify([{
        "id": inv.id, "invoice_number": inv.invoice_number,
        "member_id": inv.member_id, "member_name": f"{inv.member.first_name} {inv.member.last_name}",
        "issue_date": inv.issue_date, "due_date": inv.due_date,
        "status": inv.status, "subtotal": inv.subtotal, "total": inv.total,
        "paid_amount": inv.paid_amount,
        "items": [{"description": it.description, "quantity": it.quantity,
                    "unit_price": it.unit_price, "amount": it.amount}
                  for it in inv.items],
    } for inv in invoices])


@bp.route("/attendance")
@login_required
def api_attendance():
    date_str = request.args.get("date")
    q = Attendance.query
    if date_str:
        q = q.filter_by(date=date_str)
    records = q.order_by(Attendance.date.desc()).all()
    return jsonify([{
        "id": a.id, "member_id": a.member_id, "date": a.date,
        "status": a.status, "notes": a.notes,
    } for a in records])


@bp.route("/expenses")
@login_required
def api_expenses():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return jsonify([{
        "id": e.id, "description": e.description, "amount": e.amount,
        "expense_date": e.expense_date, "category": e.category, "notes": e.notes,
    } for e in expenses])


@bp.route("/songs")
@login_required
def api_songs():
    songs = Song.query.order_by(Song.title).all()
    return jsonify([{
        "id": s.id, "title": s.title, "composer": s.composer,
        "lyrics": s.lyrics[:200] if s.lyrics else "", "audio_file": s.audio_file,
        "upload_date": s.upload_date,
    } for s in songs])


@bp.route("/stats")
@login_required
def api_stats():
    total_members = Member.query.count()
    total_payments = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar()
    total_invoices = Invoice.query.count()
    unpaid_invoices = Invoice.query.filter(Invoice.status == "unpaid").count()
    total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0)).scalar()
    members_by_section = db.session.query(Member.section, db.func.count(Member.id)).group_by(Member.section).all()
    return jsonify({
        "total_members": total_members,
        "total_payments_received": float(total_payments),
        "total_expenses": float(total_expenses),
        "net_balance": float(total_payments - total_expenses),
        "total_invoices": total_invoices,
        "unpaid_invoices": unpaid_invoices,
        "members_by_section": {s: c for s, c in members_by_section},
    })
