import os
from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inisialisasi Aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi ---
# Gunakan variabel lingkungan untuk DATABASE_URL di produksi,
# dengan fallback ke database SQLite lokal untuk pengembangan.
# DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///donghua.db")
# Ganti 'sqlite:///' dengan 'postgresql://' jika Render menggunakan PostgreSQL
# if DATABASE_URL.startswith("postgres://"):
#     DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

if "PYTHONANYWHERE_DOMAIN" in os.environ:
    # Konfigurasi untuk database MySQL di PythonAnywhere
    # Ambil nilai dari environment variables
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    )
else:
    # Konfigurasi untuk database SQLite lokal
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///donghua.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Diperlukan untuk menggunakan flash messages
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "a-secret-key-for-development")


# Inisialisasi Database dan Migrasi
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# --- Model Database ---
class Donghua(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    last_episode = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Donghua {self.title}>"


# --- Routes ---
@app.route("/")
def index():
    """Menampilkan semua donghua, diurutkan berdasarkan judul."""
    donghuas = Donghua.query.order_by(Donghua.title.asc()).all()
    return render_template("index.html", donghuas=donghuas)


@app.route("/add", methods=["GET", "POST"])
def add():
    """Menambahkan donghua baru."""
    if request.method == "POST":
        title = request.form.get("title")
        episode_str = request.form.get("episode")

        # Validasi input
        if not title or not episode_str:
            flash("Judul dan episode tidak boleh kosong.", "error")
            return render_template("add.html")

        try:
            episode = int(episode_str)
            if episode < 0:
                flash("Episode tidak boleh negatif.", "error")
                return render_template("add.html")

            # Cek apakah judul sudah ada
            if Donghua.query.filter_by(title=title).first():
                flash(f"Donghua dengan judul '{title}' sudah ada.", "error")
                return render_template("add.html")

            new_donghua = Donghua(title=title, last_episode=episode)
            db.session.add(new_donghua)
            db.session.commit()
            flash(f"'{title}' berhasil ditambahkan!", "success")
            return redirect("/")
        except ValueError:
            flash("Episode harus berupa angka.", "error")
            return render_template("add.html")

    return render_template("add.html")


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    """Menghapus donghua berdasarkan ID."""
    donghua = Donghua.query.get_or_404(id)
    title = donghua.title
    db.session.delete(donghua)
    db.session.commit()
    flash(f"'{title}' berhasil dihapus.", "success")
    return redirect("/")


@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    """Memperbarui judul DAN episode terakhir dari sebuah donghua."""
    donghua = Donghua.query.get_or_404(id)

    # 1. Ambil data JUDUL dan EPISODE dari form
    new_title = request.form.get("title")
    new_episode_str = request.form.get("episode")

    # 2. Validasi dasar: pastikan input tidak kosong
    if not new_title or not new_episode_str:
        flash("Judul dan episode tidak boleh kosong.", "error")
        return redirect("/")

    try:
        new_episode = int(new_episode_str)

        # 3. PENTING: Cek apakah judul baru sudah dipakai oleh donghua LAIN
        #    Kita filter judul yang sama, TAPI bukan untuk item dengan ID yang sama (id != id)
        existing_donghua = Donghua.query.filter(
            Donghua.title == new_title, Donghua.id != id
        ).first()
        if existing_donghua:
            flash(f"Judul '{new_title}' sudah digunakan oleh donghua lain.", "error")
            return redirect("/")

        # 4. Jika semua validasi lolos, update data di database
        donghua.title = new_title
        donghua.last_episode = new_episode

        # 5. Simpan semua perubahan ke database
        db.session.commit()

        flash(f"Data untuk '{new_title}' berhasil diperbarui.", "success")

    except (ValueError, TypeError):
        flash("Input episode tidak valid. Harus berupa angka.", "error")

    return redirect("/")


# Blok ini hanya untuk menjalankan server development lokal.
# Di Render, Gunicorn yang akan menjalankan aplikasi.
if __name__ == "__main__":
    app.run(debug=True)
