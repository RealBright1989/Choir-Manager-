import os
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from utils import login_required, validate_csrf, validate_required, log_audit
from models import db, Song

bp = Blueprint("songs", __name__)
UPLOAD_FOLDER = "song_uploads"


@bp.route("/songs")
@login_required
def songs():
    songs_list = Song.query.order_by(Song.upload_date.desc()).all()
    return render_template("songs.html", songs=songs_list)


@bp.route("/songs/add", methods=["GET", "POST"])
@login_required
def song_add():
    if request.method == "POST":
        if not validate_csrf():
            return redirect(url_for("songs.songs"))
        title = request.form.get("title", "").strip()
        err = validate_required(title, "Title")
        if err:
            flash(err, "danger")
            return redirect(url_for("songs.song_add"))
        composer = request.form.get("composer", "").strip()
        lyrics = request.form.get("lyrics", "").strip()
        notes = request.form.get("notes", "").strip()
        audio_file = ""
        if "audio" in request.files:
            f = request.files["audio"]
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title.replace(' ', '_')}{ext}"
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                audio_file = filename
        s = Song(title=title, composer=composer, lyrics=lyrics, audio_file=audio_file,
                  upload_date=date.today().strftime("%Y-%m-%d"), notes=notes)
        db.session.add(s)
        db.session.flush()
        db.session.commit()
        log_audit("create", "song", s.id, f"Song: {title}")
        flash("Song added!", "success")
        return redirect(url_for("songs.songs"))
    return render_template("song_form.html", song=None, title="Add Song")


@bp.route("/songs/delete/<int:id>")
@login_required
def song_delete(id):
    song = db.session.get(Song, id)
    if not song:
        flash("Song not found.", "danger")
        return redirect(url_for("songs.songs"))
    if song.audio_file:
        fp = os.path.join(UPLOAD_FOLDER, song.audio_file)
        if os.path.isfile(fp): os.remove(fp)
    db.session.delete(song)
    db.session.commit()
    log_audit("delete", "song", id, f"Song: {song.title}")
    flash("Song deleted.", "success")
    return redirect(url_for("songs.songs"))


@bp.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
