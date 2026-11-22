
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Pengaturan

pengaturan_bp = Blueprint(
    "pengaturan",
    __name__,
    url_prefix="/pengaturan"
)


@pengaturan_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if not current_user.is_admin:
        return "Akses ditolak", 403

    pengaturan = Pengaturan.query.first()

    if pengaturan is None:
        pengaturan = Pengaturan(
            nama_toko="SMK Mart POS",
            alamat_toko="",
            tarif_pajak=0,
            ambang_stok_menipis=5,
        )
        db.session.add(pengaturan)
        db.session.commit()

    if request.method == "POST":
        pengaturan.nama_toko = (
            request.form.get("nama_toko") or "SMK Mart POS"
        ).strip()

        pengaturan.alamat_toko = (
            request.form.get("alamat_toko") or ""
        ).strip()

        try:
            pengaturan.tarif_pajak = float(
                request.form.get("tarif_pajak") or 0
            )
            pengaturan.ambang_stok_menipis = int(
                request.form.get("ambang_stok_menipis") or 5
            )
        except ValueError:
            flash("Tarif pajak dan batas stok harus berupa angka.", "danger")
            return render_template(
                "pengaturan/index.html",
                pengaturan=pengaturan,
            )

        if pengaturan.tarif_pajak < 0 or pengaturan.ambang_stok_menipis < 0:
            flash("Nilai pengaturan tidak boleh negatif.", "danger")
            return render_template(
                "pengaturan/index.html",
                pengaturan=pengaturan,
            )

        db.session.commit()
        flash("Pengaturan berhasil disimpan.", "success")

        return redirect(url_for("pengaturan.index"))

    return render_template(
        "pengaturan/index.html",
        pengaturan=pengaturan,
    )
