from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import login_required
from models import db, Transaction

bp = Blueprint("finance", __name__)


@bp.route("/finance")
@login_required
def list():
    ttype = request.args.get("type")
    query = Transaction.query
    if ttype:
        query = query.filter_by(type=ttype)
    transactions = query.order_by(Transaction.date.desc()).all()
    income = sum(t.amount for t in Transaction.query.filter_by(type="income").all())
    expense = sum(t.amount for t in Transaction.query.filter_by(type="expense").all())
    return render_template("finance.html", transactions=transactions, income=income, expense=expense)


@bp.route("/finance/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        t = Transaction(
            type=request.form["type"],
            amount=float(request.form["amount"]),
            description=request.form.get("description"),
            date=request.form.get("date", datetime.now().strftime("%Y-%m-%d")),
            category=request.form.get("category"),
            recorded_by=session.get("user_id"),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(t)
        db.session.commit()
        flash("Transaction recorded!", "success")
        return redirect(url_for("finance.list"))
    return render_template("finance_form.html", transaction=None)


@bp.route("/finance/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    t = db.session.get(Transaction, id)
    if t:
        db.session.delete(t)
        db.session.commit()
        flash("Transaction deleted.", "success")
    return redirect(url_for("finance.list"))
