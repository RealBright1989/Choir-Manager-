from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import login_required, validate_csrf, validate_required, validate_amount, log_audit
from models import db, Member, Payment

bp = Blueprint("finance", __name__)


@bp.route("/finance")
@login_required
def finance():
    member_filter = request.args.get("member_id", "")
    query = Payment.query.join(Member).add_columns(
        Member.first_name, Member.last_name).order_by(Payment.payment_date.desc())
    if member_filter and member_filter.isdigit():
        query = query.filter(Payment.member_id == int(member_filter))
    payments = query.all()
    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    total_collected = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar()
    total_count = Payment.query.count()
    member_totals = db.session.query(
        Member.first_name, Member.last_name,
        db.func.coalesce(db.func.sum(Payment.amount), 0).label("total")
    ).outerjoin(Payment, Payment.member_id == Member.id).group_by(Member.id).order_by(
        db.func.coalesce(db.func.sum(Payment.amount), 0)).all()
    return render_template("finance.html", payments=payments, members=members, total_collected=total_collected,
                           total_count=total_count, member_totals=member_totals, selected_member=member_filter)


@bp.route("/finance/add", methods=["POST"])
@login_required
def finance_add():
    if not validate_csrf():
        return redirect(url_for("finance.finance"))
    member_id = request.form.get("member_id", "").strip()
    amount_str = request.form.get("amount", "").strip()
    payment_date = request.form.get("payment_date", "").strip()
    errs = []
    for v, n in [(member_id, "Member"), (amount_str, "Amount"), (payment_date, "Date")]:
        e = validate_required(v, n)
        if e: errs.append(e)
    if not errs:
        e = validate_amount(amount_str)
        if e: errs.append(e)
    if errs:
        for e in errs: flash(e, "danger")
        return redirect(url_for("finance.finance"))
    p = Payment(member_id=int(member_id), amount=float(amount_str), payment_date=payment_date,
                payment_for=request.form.get("payment_for", "").strip(),
                notes=request.form.get("notes", "").strip())
    db.session.add(p)
    db.session.flush()
    db.session.commit()
    log_audit("create", "payment", p.id, f"Amount: {amount_str} for member #{member_id}")
    flash("Payment recorded!", "success")
    return redirect(url_for("finance.finance"))


@bp.route("/finance/delete/<int:id>")
@login_required
def finance_delete(id):
    Payment.query.filter_by(id=id).delete()
    db.session.commit()
    log_audit("delete", "payment", id, "Payment deleted")
    flash("Payment deleted.", "success")
    return redirect(url_for("finance.finance"))
