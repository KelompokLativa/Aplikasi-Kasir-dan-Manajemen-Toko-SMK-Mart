
from flask import Blueprint, render_template, request, jsonify, abort, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Produk,
    Pelanggan,
    MetodeBayar,
    Pengaturan,
    Order,
)

from app.blueprints.pos.services import (
    proses_checkout,
    buat_pelanggan_cepat,
)

pos_bp = Blueprint("pos", __name__)


@pos_bp.route("/pos")
@login_required
def index():
    produk = Produk.query.filter_by(
        aktif=True
    ).order_by(Produk.nama.asc()).all()

    pelanggan = Pelanggan.query.order_by(
        Pelanggan.nama.asc()
    ).all()

    metode_bayar = MetodeBayar.query.filter_by(
        aktif=True
    ).order_by(MetodeBayar.nama.asc()).all()

    pengaturan = Pengaturan.query.first()

    if pengaturan is None:
        pengaturan = Pengaturan(
            nama_toko="SMK Mart POS",
            tarif_pajak=0,
            ambang_stok_menipis=5
        )

    kategori = sorted({
        p.kategori for p in produk if p.kategori
    })

    return render_template(
        "pos/index.html",

        # Nama variabel untuk template POS
        produk_list=produk,
        pelanggan_list=pelanggan,
        metode_list=metode_bayar,
        kategori_list=kategori,

        # Nama variabel tambahan
        produk=produk,
        pelanggan=pelanggan,
        metode_bayar=metode_bayar,

        pengaturan=pengaturan,
        nama_toko=pengaturan.nama_toko,
    )


@pos_bp.route("/pos/checkout", methods=["POST"])
@login_required
def checkout():
    payload = request.get_json(silent=True) or {}

    try:
        order = proses_checkout(payload, current_user)

        return jsonify({
            "success": True,
            "message": "Transaksi berhasil disimpan.",
            "order_id": order.id,
            "nomor": order.nomor,
            "total": order.total,
            "kembalian": order.kembalian or 0,
            "redirect_url": url_for(
                "pos.struk",
                order_id=order.id
            ),
        }), 201

    except ValueError as exc:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Terjadi kesalahan saat menyimpan transaksi.",
        }), 500


@pos_bp.route(
    "/pos/pelanggan-cepat",
    methods=["POST"],
    endpoint="tambah_pelanggan_cepat"
)
@login_required
def pelanggan_cepat():
    payload = request.get_json(silent=True) or {}

    try:
        pelanggan = buat_pelanggan_cepat(
            payload.get("nama"),
            payload.get("telepon"),
        )

        return jsonify({
            "success": True,
            "id": pelanggan.id,
            "nama": pelanggan.nama,
            "telepon": pelanggan.telepon,
            "message": "Pelanggan berhasil ditambahkan.",
        }), 201

    except ValueError as exc:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(exc),
        }), 400


@pos_bp.route("/pos/struk/<int:order_id>")
@login_required
def struk(order_id):
    order = db.session.get(Order, order_id)

    if order is None:
        abort(404)

    if not current_user.is_admin:
        if order.kasir_id != current_user.id:
            abort(403)

    pengaturan = Pengaturan.query.first()

    if pengaturan is None:
        pengaturan = Pengaturan(
            nama_toko="SMK Mart POS",
            alamat_toko=""
        )

    return render_template(
        "pos/struk.html",
        order=order,
        pengaturan=pengaturan,
    )
