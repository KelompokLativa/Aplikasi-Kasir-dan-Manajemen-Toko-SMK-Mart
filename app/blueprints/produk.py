from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Produk


produk_bp = Blueprint("produk", __name__, url_prefix="/produk")


@produk_bp.route("/")
@login_required
def index():
    produk = Produk.query.order_by(Produk.nama.asc()).all()

    return render_template(
        "produk/index.html",
        produk=produk,
        products=produk,
    )


@produk_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    if request.method == "POST":
        kode = (request.form.get("kode") or "").strip()
        nama = (request.form.get("nama") or "").strip()
        kategori = (request.form.get("kategori") or "").strip()

        try:
            harga = int(request.form.get("harga") or 0)
            stok = int(request.form.get("stok") or 0)
        except ValueError:
            flash("Harga dan stok harus berupa angka.", "danger")
            return render_template("produk/tambah.html")

        if not kode or not nama:
            flash("Kode dan nama produk wajib diisi.", "danger")
            return render_template("produk/tambah.html")

        if Produk.query.filter_by(kode=kode).first():
            flash("Kode produk sudah digunakan.", "danger")
            return render_template("produk/tambah.html")

        produk = Produk(
            kode=kode,
            nama=nama,
            kategori=kategori or None,
            harga=harga,
            stok=stok,
            aktif=True,
        )

        db.session.add(produk)
        db.session.commit()

        flash("Produk berhasil ditambahkan.", "success")
        return redirect(url_for("produk.index"))

    return render_template("produk/tambah.html")


@produk_bp.route("/<int:produk_id>/ubah", methods=["GET", "POST"])
@login_required
def ubah(produk_id):
    if not current_user.is_admin:
        return "Akses ditolak", 403

    produk = db.session.get(Produk, produk_id)

    if produk is None:
        return "Produk tidak ditemukan", 404

    if request.method == "POST":
        produk.kode = (
            request.form.get("kode") or produk.kode
        ).strip()

        produk.nama = (
            request.form.get("nama") or produk.nama
        ).strip()

        produk.kategori = (
            request.form.get("kategori") or ""
        ).strip() or None

        try:
            produk.harga = int(
                request.form.get("harga") or produk.harga
            )
            produk.stok = int(
                request.form.get("stok") or produk.stok
            )
        except ValueError:
            flash("Harga dan stok harus berupa angka.", "danger")
            return render_template(
                "produk/ubah.html",
                produk=produk,
            )

        db.session.commit()

        flash("Produk berhasil diperbarui.", "success")
        return redirect(url_for("produk.index"))

    return render_template(
        "produk/ubah.html",
        produk=produk,
    )