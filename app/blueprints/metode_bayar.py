from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import MetodeBayar

metode_bayar_bp = Blueprint(
    "metode_bayar",
    __name__,
    url_prefix="/metode-bayar"
)


@metode_bayar_bp.route("/")
@login_required
def index():
    metode_bayar = MetodeBayar.query.order_by(
        MetodeBayar.nama.asc()
    ).all()

    return render_template(
        "metode_bayar/index.html",
        metode_bayar=metode_bayar,
        metode=metode_bayar,
    )


@metode_bayar_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    if request.method == "POST":
        nama = (request.form.get("nama") or "").strip()
        jenis = (request.form.get("jenis") or "tunai").strip()

        if not nama:
            flash("Nama metode pembayaran wajib diisi.", "danger")
            return render_template("metode_bayar/tambah.html")

        db.session.add(MetodeBayar(
            nama=nama,
            jenis=jenis,
            aktif=True,
        ))
        db.session.commit()

        flash("Metode pembayaran berhasil ditambahkan.", "success")
        return redirect(url_for("metode_bayar.index"))

    return render_template("metode_bayar/tambah.html")


@metode_bayar_bp.route("/<int:id>/ubah", methods=["GET", "POST"])
@login_required
def ubah(id):
    if not current_user.is_admin:
        return "Akses ditolak", 403

    metode = db.session.get(MetodeBayar, id)

    if metode is None:
        return "Metode pembayaran tidak ditemukan", 404

    if request.method == "POST":
        metode.nama = (
            request.form.get("nama") or metode.nama
        ).strip()

        metode.jenis = (
            request.form.get("jenis") or metode.jenis
        ).strip()

        metode.aktif = request.form.get("aktif") == "on"

        db.session.commit()

        flash("Metode pembayaran berhasil diperbarui.", "success")
        return redirect(url_for("metode_bayar.index"))

    return render_template(
        "metode_bayar/ubah.html",
        metode=metode,
    )