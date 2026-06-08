from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import login_required
from models import db, Document

bp = Blueprint("documents", __name__)


@bp.route("/documents")
@login_required
def list():
    folder = request.args.get("folder")
    query = Document.query
    if folder:
        query = query.filter_by(folder=folder)
    docs = query.order_by(Document.id.desc()).all()
    folders = db.session.query(Document.folder).distinct().all()
    folders = [f[0] for f in folders if f[0]]
    return render_template("documents.html", docs=docs, folders=folders)


@bp.route("/documents/upload", methods=["POST"])
@login_required
def upload():
    title = request.form.get("title", "Untitled")
    folder = request.form.get("folder", "General")
    permissions = request.form.get("permissions", "Standard")
    description = request.form.get("description", "")

    doc = Document(
        title=title,
        filename=title,
        file_type="document",
        file_size="—",
        folder=folder,
        permissions=permissions,
        description=description,
        uploaded_by=session.get("user_id"),
        uploaded_at=datetime.now().strftime("%Y-%m-%d")
    )
    db.session.add(doc)
    db.session.commit()
    flash(f"'{title}' uploaded to {folder}.", "success")
    return redirect(url_for("documents.list"))


@bp.route("/documents/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    doc = db.session.get(Document, id)
    if doc:
        db.session.delete(doc)
        db.session.commit()
        flash(f"'{doc.title}' deleted.", "success")
    return redirect(url_for("documents.list"))
