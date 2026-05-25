import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import shutil
import webbrowser

DB_FILE = "choir.db"
UPLOAD_DIR = "song_uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            section TEXT NOT NULL DEFAULT 'Soprano',
            join_date TEXT NOT NULL,
            address TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            payment_for TEXT,
            notes TEXT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            composer TEXT,
            lyrics TEXT,
            audio_file TEXT,
            upload_date TEXT NOT NULL,
            notes TEXT
        );
    """)
    conn.commit()
    conn.close()


class ChoirApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Choir Management System")
        self.root.geometry("900x650")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.build_members_tab()
        self.build_payments_tab()
        self.build_songs_tab()
        self.build_social_tab()

    # ─── Members Tab ────────────────────────────────────────────────

    def build_members_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Members")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="Register New Member", command=self.register_member).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh List", command=self.refresh_members).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_member).pack(side="left", padx=5)

        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.member_search_var = tk.StringVar()
        self.member_search_var.trace("w", lambda *a: self.refresh_members())
        ttk.Entry(search_frame, textvariable=self.member_search_var, width=40).pack(side="left", padx=5)

        cols = ("ID", "First Name", "Last Name", "Phone", "Email", "Section", "Join Date")
        self.member_tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.member_tree.heading(col, text=col)
            self.member_tree.column(col, width=100)
        self.member_tree.column("ID", width=40)
        self.member_tree.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.member_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.member_tree.configure(yscrollcommand=scrollbar.set)

        self.member_tree.bind("<Double-1>", lambda e: self.edit_member())

        self.refresh_members()

    def refresh_members(self):
        for row in self.member_tree.get_children():
            self.member_tree.delete(row)
        conn = get_db()
        cur = conn.cursor()
        search = self.member_search_var.get().strip()
        if search:
            cur.execute("""
                SELECT * FROM members
                WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
                ORDER BY last_name, first_name
            """, (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            cur.execute("SELECT * FROM members ORDER BY last_name, first_name")
        for row in cur.fetchall():
            self.member_tree.insert("", "end", values=(
                row["id"], row["first_name"], row["last_name"],
                row["phone"], row["email"], row["section"], row["join_date"]
            ))
        conn.close()

    def register_member(self):
        self._member_form(title="Register New Member")

    def edit_member(self):
        sel = self.member_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a member to edit.")
            return
        item = self.member_tree.item(sel[0])
        member_id = item["values"][0]
        self._member_form(title="Edit Member", member_id=member_id)

    def _member_form(self, title="Member", member_id=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("500x400")
        win.grab_set()

        fields = ["first_name", "last_name", "phone", "email", "section", "join_date", "address", "notes"]
        labels = ["First Name*", "Last Name*", "Phone", "Email", "Section", "Join Date (YYYY-MM-DD)*", "Address", "Notes"]
        entries = {}

        data = {}
        if member_id:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM members WHERE id=?", (member_id,))
            row = cur.fetchone()
            if row:
                data = dict(row)
            conn.close()

        for i, (field, label) in enumerate(zip(fields, labels)):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=3)
            if field == "section":
                cb = ttk.Combobox(win, values=["Soprano", "Alto", "Tenor", "Bass"], state="readonly")
                cb.grid(row=i, column=1, sticky="ew", padx=10, pady=3)
                cb.set(data.get(field, "Soprano"))
                entries[field] = cb
            elif field in ("address", "notes"):
                txt = tk.Text(win, height=3, width=30)
                txt.grid(row=i, column=1, sticky="ew", padx=10, pady=3)
                if data.get(field):
                    txt.insert("1.0", data[field])
                entries[field] = txt
            else:
                ent = ttk.Entry(win, width=30)
                ent.grid(row=i, column=1, sticky="ew", padx=10, pady=3)
                if data.get(field):
                    ent.insert(0, data[field])
                if field == "join_date" and not data:
                    ent.insert(0, datetime.now().strftime("%Y-%m-%d"))
                entries[field] = ent

        def save():
            values = {}
            for field in fields:
                if field in ("address", "notes"):
                    values[field] = entries[field].get("1.0", "end-1c").strip()
                elif field == "section":
                    values[field] = entries[field].get()
                else:
                    values[field] = entries[field].get().strip()

            if not values["first_name"] or not values["last_name"] or not values["join_date"]:
                messagebox.showwarning("Required fields", "First Name, Last Name, and Join Date are required.")
                return

            conn = get_db()
            cur = conn.cursor()
            if member_id:
                cur.execute("""
                    UPDATE members SET first_name=?, last_name=?, phone=?, email=?, section=?,
                    join_date=?, address=?, notes=? WHERE id=?
                """, (values["first_name"], values["last_name"], values["phone"],
                      values["email"], values["section"], values["join_date"],
                      values["address"], values["notes"], member_id))
            else:
                cur.execute("""
                    INSERT INTO members (first_name, last_name, phone, email, section, join_date, address, notes)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (values["first_name"], values["last_name"], values["phone"],
                      values["email"], values["section"], values["join_date"],
                      values["address"], values["notes"]))
            conn.commit()
            conn.close()
            win.destroy()
            self.refresh_members()

        ttk.Button(win, text="Save", command=save).grid(row=len(fields), column=1, pady=15, sticky="e")
        win.columnconfigure(1, weight=1)

    def delete_member(self):
        sel = self.member_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a member to delete.")
            return
        item = self.member_tree.item(sel[0])
        member_id = item["values"][0]
        name = f"{item['values'][1]} {item['values'][2]}"
        if messagebox.askyesno("Confirm Delete", f"Delete {name} and all their payment records?"):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM payments WHERE member_id=?", (member_id,))
            cur.execute("DELETE FROM members WHERE id=?", (member_id,))
            conn.commit()
            conn.close()
            self.refresh_members()

    # ─── Payments Tab ──────────────────────────────────────────────

    def build_payments_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Payments")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="Record Payment", command=self.record_payment).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_payments).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_payment).pack(side="left", padx=5)

        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill="x", pady=5)
        ttk.Label(filter_frame, text="Filter by member:").pack(side="left", padx=5)
        self.payment_filter_var = tk.StringVar()
        self.payment_filter_combo = ttk.Combobox(filter_frame, textvariable=self.payment_filter_var,
                                                  state="readonly", width=35)
        self.payment_filter_combo.pack(side="left", padx=5)
        self.payment_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_payments())
        ttk.Button(filter_frame, text="Show All", command=lambda: (
            self.payment_filter_var.set(""), self.refresh_payments()
        )).pack(side="left", padx=5)

        cols = ("ID", "Member", "Amount", "Date", "Payment For", "Notes")
        self.payment_tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.payment_tree.heading(col, text=col)
            self.payment_tree.column(col, width=120)
        self.payment_tree.column("ID", width=40)
        self.payment_tree.column("Amount", width=80)
        self.payment_tree.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.payment_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.payment_tree.configure(yscrollcommand=scrollbar.set)

        self.refresh_payments()
        self._load_payment_filter()

    def _load_payment_filter(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name FROM members ORDER BY last_name, first_name")
        members = cur.fetchall()
        conn.close()
        vals = [f"{m['id']} - {m['first_name']} {m['last_name']}" for m in members]
        self.payment_filter_combo["values"] = vals

    def refresh_payments(self):
        for row in self.payment_tree.get_children():
            self.payment_tree.delete(row)
        conn = get_db()
        cur = conn.cursor()
        filter_val = self.payment_filter_var.get()
        if filter_val:
            mid = int(filter_val.split(" - ")[0])
            cur.execute("""
                SELECT p.*, m.first_name, m.last_name FROM payments p
                JOIN members m ON p.member_id = m.id
                WHERE p.member_id = ?
                ORDER BY p.payment_date DESC
            """, (mid,))
        else:
            cur.execute("""
                SELECT p.*, m.first_name, m.last_name FROM payments p
                JOIN members m ON p.member_id = m.id
                ORDER BY p.payment_date DESC
            """)
        for row in cur.fetchall():
            self.payment_tree.insert("", "end", values=(
                row["id"], f"{row['first_name']} {row['last_name']}",
                f"${row['amount']:.2f}", row["payment_date"],
                row["payment_for"], row["notes"]
            ))
        conn.close()
        self._load_payment_filter()

    def record_payment(self):
        win = tk.Toplevel(self.root)
        win.title("Record Payment")
        win.geometry("450x350")
        win.grab_set()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name FROM members ORDER BY last_name, first_name")
        members = cur.fetchall()
        conn.close()

        if not members:
            messagebox.showwarning("No members", "Register at least one member first.")
            win.destroy()
            return

        member_options = {f"{m['id']} - {m['first_name']} {m['last_name']}": m['id'] for m in members}

        ttk.Label(win, text="Member*").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        member_combo = ttk.Combobox(win, values=list(member_options.keys()), state="readonly", width=35)
        member_combo.grid(row=0, column=1, padx=10, pady=5)
        if member_options:
            member_combo.set(list(member_options.keys())[0])

        ttk.Label(win, text="Amount ($)*").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        amount_entry = ttk.Entry(win, width=30)
        amount_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(win, text="Date (YYYY-MM-DD)*").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        date_entry = ttk.Entry(win, width=30)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(win, text="Payment For").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        pf_entry = ttk.Entry(win, width=30)
        pf_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(win, text="Notes").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        notes_text = tk.Text(win, height=3, width=30)
        notes_text.grid(row=4, column=1, padx=10, pady=5)

        def save():
            member_key = member_combo.get()
            amount_str = amount_entry.get().strip()
            date_str = date_entry.get().strip()
            payment_for = pf_entry.get().strip()
            notes = notes_text.get("1.0", "end-1c").strip()

            if not member_key or not amount_str or not date_str:
                messagebox.showwarning("Required fields", "Member, Amount, and Date are required.")
                return
            try:
                amount = float(amount_str)
            except ValueError:
                messagebox.showwarning("Invalid amount", "Amount must be a number.")
                return

            member_id = member_options[member_key]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO payments (member_id, amount, payment_date, payment_for, notes)
                VALUES (?,?,?,?,?)
            """, (member_id, amount, date_str, payment_for, notes))
            conn.commit()
            conn.close()
            win.destroy()
            self.refresh_payments()

        ttk.Button(win, text="Save Payment", command=save).grid(row=5, column=1, pady=15, sticky="e")
        win.columnconfigure(1, weight=1)

    def delete_payment(self):
        sel = self.payment_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a payment to delete.")
            return
        item = self.payment_tree.item(sel[0])
        payment_id = item["values"][0]
        if messagebox.askyesno("Confirm Delete", "Delete this payment record?"):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM payments WHERE id=?", (payment_id,))
            conn.commit()
            conn.close()
            self.refresh_payments()

    # ─── Songs Tab ─────────────────────────────────────────────────

    def build_songs_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Songs")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="Upload New Song", command=self.upload_song).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_songs).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_song).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Play Audio", command=self.play_song).pack(side="left", padx=5)

        cols = ("ID", "Title", "Composer", "Upload Date", "Audio File")
        self.song_tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.song_tree.heading(col, text=col)
            self.song_tree.column(col, width=150)
        self.song_tree.column("ID", width=40)
        self.song_tree.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.song_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.song_tree.configure(yscrollcommand=scrollbar.set)

        self.song_tree.bind("<Double-1>", lambda e: self.view_song_details())

        self.refresh_songs()

    def refresh_songs(self):
        for row in self.song_tree.get_children():
            self.song_tree.delete(row)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM songs ORDER BY upload_date DESC")
        for row in cur.fetchall():
            audio = os.path.basename(row["audio_file"]) if row["audio_file"] else ""
            self.song_tree.insert("", "end", values=(
                row["id"], row["title"], row["composer"] or "",
                row["upload_date"], audio
            ))
        conn.close()

    def upload_song(self):
        win = tk.Toplevel(self.root)
        win.title("Upload New Song")
        win.geometry("550x450")
        win.grab_set()

        fields = ["title", "composer", "lyrics", "notes"]
        labels = ["Title*", "Composer", "Lyrics", "Notes"]
        entries = {}

        ttk.Label(win, text="Title*").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        entries["title"] = ttk.Entry(win, width=35)
        entries["title"].grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(win, text="Composer").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        entries["composer"] = ttk.Entry(win, width=35)
        entries["composer"].grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(win, text="Lyrics").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        lyrics_text = tk.Text(win, height=8, width=40)
        lyrics_text.grid(row=2, column=1, padx=10, pady=5)
        entries["lyrics"] = lyrics_text

        ttk.Label(win, text="Notes").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        notes_text = tk.Text(win, height=3, width=40)
        notes_text.grid(row=3, column=1, padx=10, pady=5)
        entries["notes"] = notes_text

        audio_path_var = tk.StringVar()
        ttk.Label(win, text="Audio File").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        audio_frame = ttk.Frame(win)
        audio_frame.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        ttk.Entry(audio_frame, textvariable=audio_path_var, width=30).pack(side="left", padx=2)
        ttk.Button(audio_frame, text="Browse...", command=lambda: (
            audio_path_var.set(filedialog.askopenfilename(
                title="Select audio file",
                filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("All files", "*.*")]
            ))
        )).pack(side="left", padx=2)

        def save():
            title = entries["title"].get().strip()
            composer = entries["composer"].get().strip()
            lyrics = entries["lyrics"].get("1.0", "end-1c").strip()
            notes = entries["notes"].get("1.0", "end-1c").strip()
            src_audio = audio_path_var.get().strip()

            if not title:
                messagebox.showwarning("Required", "Title is required.")
                return

            dest_audio = ""
            if src_audio and os.path.isfile(src_audio):
                ext = os.path.splitext(src_audio)[1]
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title.replace(' ', '_')}{ext}"
                dest_audio = os.path.join(UPLOAD_DIR, filename)
                shutil.copy2(src_audio, dest_audio)

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO songs (title, composer, lyrics, audio_file, upload_date, notes)
                VALUES (?,?,?,?,?,?)
            """, (title, composer, lyrics, dest_audio, datetime.now().strftime("%Y-%m-%d"), notes))
            conn.commit()
            conn.close()
            win.destroy()
            self.refresh_songs()

        ttk.Button(win, text="Save Song", command=save).grid(row=5, column=1, pady=15, sticky="e")
        win.columnconfigure(1, weight=1)

    def delete_song(self):
        sel = self.song_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a song to delete.")
            return
        item = self.song_tree.item(sel[0])
        song_id = item["values"][0]
        title = item["values"][1]
        if messagebox.askyesno("Confirm Delete", f"Delete '{title}'?"):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT audio_file FROM songs WHERE id=?", (song_id,))
            row = cur.fetchone()
            if row and row["audio_file"] and os.path.isfile(row["audio_file"]):
                os.remove(row["audio_file"])
            cur.execute("DELETE FROM songs WHERE id=?", (song_id,))
            conn.commit()
            conn.close()
            self.refresh_songs()

    def play_song(self):
        sel = self.song_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a song.")
            return
        item = self.song_tree.item(sel[0])
        song_id = item["values"][0]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT audio_file FROM songs WHERE id=?", (song_id,))
        row = cur.fetchone()
        conn.close()
        if row and row["audio_file"] and os.path.isfile(row["audio_file"]):
            os.startfile(row["audio_file"])
        else:
            messagebox.showinfo("No Audio", "This song has no audio file attached.")

    def view_song_details(self):
        sel = self.song_tree.selection()
        if not sel:
            return
        item = self.song_tree.item(sel[0])
        song_id = item["values"][0]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM songs WHERE id=?", (song_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return

        win = tk.Toplevel(self.root)
        win.title(f"Song: {row['title']}")
        win.geometry("500x400")
        win.grab_set()

        text = tk.Text(win, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", f"Title: {row['title']}\n")
        text.insert("end", f"Composer: {row['composer'] or 'N/A'}\n")
        text.insert("end", f"Upload Date: {row['upload_date']}\n")
        text.insert("end", f"Audio: {os.path.basename(row['audio_file']) if row['audio_file'] else 'None'}\n")
        text.insert("end", f"Notes: {row['notes'] or ''}\n\n")
        text.insert("end", "── Lyrics ──\n")
        text.insert("end", row["lyrics"] or "")
        text.configure(state="disabled")


    # ─── Social Tab ────────────────────────────────────────────────

    def build_social_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Social Links")

        header = ttk.Label(tab, text="Follow us on social media!", font=("Arial", 14, "bold"))
        header.pack(pady=20)

        links = [
            ("Facebook", "https://facebook.com", "blue"),
            ("YouTube", "https://youtube.com", "red"),
            ("Instagram", "https://instagram.com", "purple"),
            ("TikTok", "https://tiktok.com", "black"),
        ]

        for name, url, color in links:
            btn = tk.Button(tab, text=f"  {name}  ", font=("Arial", 12, "bold"),
                            fg=color, cursor="hand2", relief="ridge", bd=2,
                            command=lambda u=url: webbrowser.open(u))
            btn.pack(pady=8, ipadx=10, ipady=5)

        info = ttk.Label(tab, text="(Links open in your default browser)", foreground="gray")
        info.pack(pady=30)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ChoirApp(root)
    root.mainloop()
