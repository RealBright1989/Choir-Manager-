from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils import login_required
from models import db, MusicSheet

bp = Blueprint("music", __name__)


@bp.route("/music")
@login_required
def list():
    songs = MusicSheet.query.order_by(MusicSheet.title).all()
    if not songs:
        seed = [
            MusicSheet(title="Hallelujah Chorus", composer="G.F. Handel", key="D", category="sheet_music", sections="S,A,T,B", duration="04:35", tempo="Allegro", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="The Lord is My Shepherd", composer="H. Goodall", key="Eb", category="sheet_music", sections="S,B", duration="03:45", tempo="Andante", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="Abide With Me", composer="Traditional Arr.", key="C", category="practice_track", sections="S,A,T,B", duration="05:12", tempo="Moderato", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="Ave Maria", composer="F. Schubert", key="G", category="sheet_music", sections="S,A", duration="04:28", tempo="Adagio", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="Great Is Thy Faithfulness", composer="T. Chisholm", key="F", category="hymnal", sections="S,A,T,B", duration="03:30", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="How Great Thou Art", composer="S. Hine", key="Ab", category="hymnal", sections="S,A,T,B", duration="04:15", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="Oh Happy Day", composer="E. Hawkins", key="G", category="practice_track", sections="S,A,T,B", duration="03:55", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            MusicSheet(title="Total Praise", composer="R. Smallwood", key="Eb", category="video_tutorial", sections="S,A,T,B", duration="05:45", uploaded_by=session.get("user_id"), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ]
        for s in seed:
            db.session.add(s)
        db.session.commit()
        songs = MusicSheet.query.order_by(MusicSheet.title).all()
    return render_template("music.html", songs=songs)


@bp.route("/music/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        s = MusicSheet(
            title=request.form["title"],
            composer=request.form.get("composer"),
            arranger=request.form.get("arranger"),
            lyrics=request.form.get("lyrics"),
            key=request.form.get("key"),
            tempo=request.form.get("tempo"),
            category=request.form.get("category", "sheet_music"),
            sections=request.form.get("sections", "S,A,T,B"),
            duration=request.form.get("duration", "04:35"),
            uploaded_by=session.get("user_id"),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(s)
        db.session.commit()
        flash(f"'{s.title}' added to library!", "success")
        return redirect(url_for("music.list"))
    return render_template("music_form.html", song=None)


@bp.route("/music/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    s = db.session.get(MusicSheet, id)
    if not s:
        flash("Song not found.", "danger")
        return redirect(url_for("music.list"))
    if request.method == "POST":
        s.title = request.form["title"]
        s.composer = request.form.get("composer")
        s.arranger = request.form.get("arranger")
        s.lyrics = request.form.get("lyrics")
        s.key = request.form.get("key")
        s.tempo = request.form.get("tempo")
        s.category = request.form.get("category", "sheet_music")
        s.sections = request.form.get("sections", "S,A,T,B")
        s.duration = request.form.get("duration", "04:35")
        db.session.commit()
        flash(f"'{s.title}' updated!", "success")
        return redirect(url_for("music.list"))
    return render_template("music_form.html", song=s)


@bp.route("/music/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    s = db.session.get(MusicSheet, id)
    if s:
        db.session.delete(s)
        db.session.commit()
        flash(f"'{s.title}' deleted.", "success")
    return redirect(url_for("music.list"))
