from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response, current_app
from utils import login_required, validate_csrf, validate_required, validate_amount, log_audit, export_excel, export_pdf
from models import db, Member, Payment, Expense, Setting
from io import BytesIO

bp = Blueprint("finance", __name__)


def get_month_range(year, month):
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-31"


def get_finance_data(year, month):
    start_date, end_date = get_month_range(year, month)
    income = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(Payment.payment_date >= start_date, Payment.payment_date <= end_date).scalar()

    expenses = db.session.query(
        db.func.coalesce(db.func.sum(Expense.amount), 0)
    ).filter(Expense.expense_date >= start_date, Expense.expense_date <= end_date).scalar()

    prev_income = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(Payment.payment_date < start_date).scalar()
    prev_expenses = db.session.query(
        db.func.coalesce(db.func.sum(Expense.amount), 0)
    ).filter(Expense.expense_date < start_date).scalar()
    balance_bf = prev_income - prev_expenses

    payments = Payment.query.filter(
        Payment.payment_date >= start_date, Payment.payment_date <= end_date
    ).order_by(Payment.payment_date.desc()).all()

    expense_list = Expense.query.filter(
        Expense.expense_date >= start_date, Expense.expense_date <= end_date
    ).order_by(Expense.expense_date.desc()).all()

    closing_balance = balance_bf + income - expenses
    return income, expenses, balance_bf, closing_balance, payments, expense_list, start_date, end_date


@bp.route("/finance")
@login_required
def finance():
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    start_date, end_date = get_month_range(year, month)
    income, expenses, balance_bf, closing_balance, payments, expense_list, _, _ = get_finance_data(year, month)

    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    member_totals = db.session.query(
        Member.first_name, Member.last_name,
        db.func.coalesce(db.func.sum(Payment.amount), 0).label("total")
    ).outerjoin(Payment, Payment.member_id == Member.id).group_by(Member.id).order_by(
        db.func.coalesce(db.func.sum(Payment.amount), 0)).all()

    months = []
    for y in range(2024, now.year + 2):
        for m in range(1, 13):
            label = f"{y:04d}-{m:02d}"
            months.append((y, m, label))

    years = list(range(2024, now.year + 2))

    return render_template("finance.html",
                           year=year, month=month, years=years,
                           balance_bf=balance_bf, income=income, expenses=expenses,
                           closing_balance=closing_balance,
                           payments=payments, expense_list=expense_list,
                           members=members, member_totals=member_totals,
                           selected_date=f"{year:04d}-{month:02d}")


@bp.route("/finance/income/add", methods=["POST"])
@login_required
def finance_income_add():
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
    log_audit("create", "payment", p.id, f"Income: {amount_str} from member #{member_id}")
    flash("Income recorded!", "success")
    return redirect(url_for("finance.finance", year=payment_date[:4], month=payment_date[5:7]))


@bp.route("/finance/expense/add", methods=["POST"])
@login_required
def finance_expense_add():
    if not validate_csrf():
        return redirect(url_for("finance.finance"))
    description = request.form.get("description", "").strip()
    amount_str = request.form.get("amount", "").strip()
    expense_date = request.form.get("expense_date", "").strip()
    category = request.form.get("category", "").strip()
    errs = []
    for v, n in [(description, "Description"), (amount_str, "Amount"), (expense_date, "Date")]:
        e = validate_required(v, n)
        if e: errs.append(e)
    if not errs:
        e = validate_amount(amount_str)
        if e: errs.append(e)
    if errs:
        for e in errs: flash(e, "danger")
        return redirect(url_for("finance.finance"))
    e = Expense(description=description, amount=float(amount_str), expense_date=expense_date,
                category=category, notes=request.form.get("notes", "").strip(),
                created_by=session.get("user_id"),
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db.session.add(e)
    db.session.flush()
    db.session.commit()
    log_audit("create", "expense", e.id, f"Expense: {amount_str} for {description}")
    flash("Expense recorded!", "success")
    return redirect(url_for("finance.finance", year=expense_date[:4], month=expense_date[5:7]))


@bp.route("/finance/income/delete/<int:id>")
@login_required
def finance_income_delete(id):
    p = db.session.get(Payment, id)
    if p:
        date_val = p.payment_date
        db.session.delete(p)
        db.session.commit()
        log_audit("delete", "payment", id, "Income deleted")
        flash("Income entry deleted.", "success")
        return redirect(url_for("finance.finance", year=date_val[:4], month=date_val[5:7]))
    flash("Payment not found.", "danger")
    return redirect(url_for("finance.finance"))


@bp.route("/finance/expense/delete/<int:id>")
@login_required
def finance_expense_delete(id):
    e = db.session.get(Expense, id)
    if e:
        date_val = e.expense_date
        db.session.delete(e)
        db.session.commit()
        log_audit("delete", "expense", id, "Expense deleted")
        flash("Expense deleted.", "success")
        return redirect(url_for("finance.finance", year=date_val[:4], month=date_val[5:7]))
    flash("Expense not found.", "danger")
    return redirect(url_for("finance.finance"))


@bp.route("/finance/export/excel")
@login_required
def finance_export_excel():
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)
    income, expenses, balance_bf, closing_balance, payments, expense_list, _, _ = get_finance_data(year, month)
    currency = db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$"
    month_name = ["January","February","March","April","May","June","July","August","September","October","November","December"][month-1]
    logo = current_app.root_path + "/static/logo_watermark.png"

    headers = ["DESCRIPTION", "AMOUNT"]
    data = [
        (f"Balance Brought Forward", f"{currency}{balance_bf:.2f}"),
        (f"Total Income ({month_name} {year})", f"{currency}{income:.2f}"),
        (f"Total Expenditure ({month_name} {year})", f"{currency}{expenses:.2f})"),
        ("CLOSING BALANCE", f"{currency}{closing_balance:.2f}"),
    ]
    data.append(("", ""))
    data.append(("INCOME TRANSACTIONS", ""))
    data.append(("Date", "Member", "Amount", "For"))
    for p in payments:
        data.append((p.payment_date, f"{p.member.first_name} {p.member.last_name}", f"{currency}{p.amount:.2f}", p.payment_for or "-"))
    data.append(("", ""))
    data.append(("EXPENDITURE TRANSACTIONS", ""))
    data.append(("Date", "Description", "Amount", "Category"))
    for e in expense_list:
        data.append((e.expense_date, e.description, f"{currency}{e.amount:.2f}", e.category or "-"))

    buf = export_excel(f"Financial Statement - {month_name} {year}",
                       ["#", "DESCRIPTION", "AMOUNT"],
                       [(i+1, d[0], d[1]) for i, d in enumerate(data) if d],
                       "finance.xlsx", logo_path=logo)
    return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=finance_{year}-{month:02d}.xlsx"})


@bp.route("/finance/export/pdf")
@login_required
def finance_export_pdf():
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)
    income, expenses, balance_bf, closing_balance, payments, expense_list, _, _ = get_finance_data(year, month)
    currency = db.session.get(Setting, "currency").value if db.session.get(Setting, "currency") else "$"
    month_name = ["January","February","March","April","May","June","July","August","September","October","November","December"][month-1]
    logo = current_app.root_path + "/static/logo_watermark.png"

    headers = ["ITEM", "AMOUNT"]
    rows = [
        ("Balance Brought Forward", f"{currency}{balance_bf:.2f}"),
        (f"Income ({month_name})", f"{currency}{income:.2f}"),
        (f"Expenditure ({month_name})", f"{currency}{expenses:.2f})"),
        ("CLOSING BALANCE", f"{currency}{closing_balance:.2f}"),
    ]
    buf = export_pdf(f"Financial Statement - {month_name} {year}", headers, rows, "finance.pdf",
                     logo_path=logo)
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=finance_{year}-{month:02d}.pdf"})