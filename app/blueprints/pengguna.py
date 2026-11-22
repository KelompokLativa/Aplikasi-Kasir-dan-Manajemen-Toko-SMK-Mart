
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User

pengguna_bp = Blueprint(
    "pengguna",
    __name__,
    url_prefix="/pengguna"
)


@pengguna_bp.route("/")
@login_required
def index():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    pengguna = User.query.order_by(User.nama.asc()).all()

    return render_template(
        "pengguna/index.html",
        pengguna=pengguna,
        users=pengguna,
    )


@pengguna_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    if request.method == "POST":
        nama = (request.form.get("nama") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        peran = (request.form.get("peran") or "kasir").strip()

        if not nama or not username or not password:
            flash("Semua data wajib diisi.", "danger")
            return render_template("pengguna/tambah.html")

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan.", "danger")
            return render_template("pengguna/tambah.html")

        if peran not in ("admin", "kasir"):
            peran = "kasir"

        user = User(
            nama=nama,
            username=username,
            peran=peran,
            aktif=True,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Pengguna berhasil ditambahkan.", "success")
        return redirect(url_for("pengguna.index"))

    return render_template("pengguna/tambah.html")


@pengguna_bp.route("/<int:id>/ubah", methods=["GET", "POST"])
@login_required
def ubah(id):
    if not current_user.is_admin:
        return "Akses ditolak", 403

    user = db.session.get(User, id)

    if user is None:
        return "Pengguna tidak ditemukan", 404

    if request.method == "POST":
        nama = (request.form.get("nama") or user.nama).strip()
        username = (request.form.get("username") or user.username).strip()
        peran = (request.form.get("peran") or user.peran).strip()

        pemilik_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if pemilik_username:
            flash("Username sudah digunakan.", "danger")
            return render_template(
                "pengguna/ubah.html",
                pengguna=user,
                user=user,
            )

        user.nama = nama
        user.username = username
        user.peran = peran if peran in ("admin", "kasir") else "kasir"
        user.aktif = request.form.get("aktif") == "on"

        password = request.form.get("password") or ""
        if password:
            user.set_password(password)

        db.session.commit()

        flash("Data pengguna berhasil diperbarui.", "success")
        return redirect(url_for("pengguna.index"))

    return render_template(
        "pengguna/ubah.html",
        pengguna=user,
        user=user,
    )


@pengguna_bp.route("/<int:id>/reset-password", methods=["POST"])
@login_required
def reset_password(id):
    if not current_user.is_admin:
        return "Akses ditolak", 403

    user = db.session.get(User, id)

    if user is None:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for("pengguna.index"))

    password_baru = request.form.get("password_baru") or ""

    if len(password_baru) < 8:
        flash("Password baru minimal 8 karakter.", "danger")
        return redirect(url_for("pengguna.index"))

    user.set_password(password_baru)
    db.session.commit()

    flash("Password pengguna berhasil diperbarui.", "success")
    return redirect(url_for("pengguna.index"))
