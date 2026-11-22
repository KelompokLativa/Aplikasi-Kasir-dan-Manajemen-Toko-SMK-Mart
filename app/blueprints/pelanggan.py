from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Pelanggan


pelanggan_bp = Blueprint(
    "pelanggan",
    __name__,
    url_prefix="/pelanggan"
)


@pelanggan_bp.route("/")
@login_required
def index():
    pelanggan = Pelanggan.query.order_by(
        Pelanggan.nama.asc()
    ).all()

    return render_template(
        "pelanggan/index.html",
        pelanggan=pelanggan,
    )


@pelanggan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    if request.method == "POST":
        nama = (request.form.get("nama") or "").strip()
        telepon = (request.form.get("telepon") or "").strip()

        if not nama:
            flash("Nama pelanggan wajib diisi.", "danger")
            return render_template("pelanggan/tambah.html")

        pelanggan = Pelanggan(
            nama=nama,
            telepon=telepon or None,
            bawaan=False,
        )

        db.session.add(pelanggan)
        db.session.commit()

        flash("Pelanggan berhasil ditambahkan.", "success")
        return redirect(url_for("pelanggan.index"))

    return render_template("pelanggan/tambah.html")


@pelanggan_bp.route("/<int:pelanggan_id>/ubah", methods=["GET", "POST"])
@login_required
def ubah(pelanggan_id):
    if not current_user.is_admin:
        return "Akses ditolak", 403

    pelanggan = db.session.get(Pelanggan, pelanggan_id)

    if pelanggan is None:
        return "Pelanggan tidak ditemukan", 404

    if request.method == "POST":
        nama = (request.form.get("nama") or "").strip()
        telepon = (request.form.get("telepon") or "").strip()

        if not nama:
            flash("Nama pelanggan wajib diisi.", "danger")
            return render_template(
                "pelanggan/ubah.html",
                pelanggan=pelanggan,
            )

        pelanggan.nama = nama
        pelanggan.telepon = telepon or None

        db.session.commit()

        flash("Pelanggan berhasil diperbarui.", "success")
        return redirect(url_for("pelanggan.index"))

    return render_template(
        "pelanggan/ubah.html",
        pelanggan=pelanggan,
    )