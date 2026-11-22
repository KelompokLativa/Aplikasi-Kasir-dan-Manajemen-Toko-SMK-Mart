import csv
import io
from datetime import datetime, timedelta
from types import SimpleNamespace

from flask import Blueprint, render_template, request, Response
from flask_login import login_required

from app.extensions import db
from app.models import Order, Produk, MetodeBayar, MutasiStok


laporan_bp = Blueprint(
    "laporan",
    __name__,
    url_prefix="/laporan"
)


def ambil_filter():
    hari_ini = datetime.now().date()

    try:
        tanggal_mulai = datetime.strptime(
            request.args.get("tanggal_mulai", ""),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        tanggal_mulai = hari_ini

    try:
        tanggal_akhir = datetime.strptime(
            request.args.get("tanggal_akhir", ""),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        tanggal_akhir = hari_ini

    if tanggal_mulai > tanggal_akhir:
        tanggal_mulai, tanggal_akhir = tanggal_akhir, tanggal_mulai

    status = request.args.get("status", "semua")
    if status not in [
        "semua",
        "selesai",
        "pengajuan_batal",
        "dibatalkan"
    ]:
        status = "semua"

    try:
        metode_id = int(request.args.get("metode_id", ""))
    except (ValueError, TypeError):
        metode_id = None

    return tanggal_mulai, tanggal_akhir, status, metode_id


def ambil_orders(tanggal_mulai, tanggal_akhir, status, metode_id):
    mulai = datetime.combine(
        tanggal_mulai,
        datetime.min.time()
    )

    akhir = datetime.combine(
        tanggal_akhir + timedelta(days=1),
        datetime.min.time()
    )

    query = Order.query.filter(
        Order.waktu >= mulai,
        Order.waktu < akhir
    )

    if status != "semua":
        query = query.filter(Order.status == status)

    if metode_id is not None:
        query = query.filter(
            Order.metode_bayar_id == metode_id
        )

    return query.order_by(Order.waktu.desc()).all()


@laporan_bp.route("/")
@login_required
def index():
    tanggal_mulai, tanggal_akhir, status, metode_id = ambil_filter()

    orders = ambil_orders(
        tanggal_mulai,
        tanggal_akhir,
        status,
        metode_id
    )

    transaksi_aktif = [
        order for order in orders
        if order.status in ("selesai", "pengajuan_batal")
    ]

    total_omzet = sum(
        order.total or 0 for order in transaksi_aktif
    )

    total_subtotal = sum(
        order.subtotal or 0 for order in transaksi_aktif
    )

    total_pajak = sum(
        order.pajak or 0 for order in transaksi_aktif
    )

    total_batal = sum(
        1 for order in orders
        if order.status == "dibatalkan"
    )

    rekap_metode = {}

    for order in transaksi_aktif:
        if order.metode_bayar:
            nama = order.metode_bayar.nama
        else:
            nama = "Tidak diketahui"

        if nama not in rekap_metode:
            rekap_metode[nama] = {
                "jumlah_order": 0,
                "total_nominal": 0
            }

        rekap_metode[nama]["jumlah_order"] += 1
        rekap_metode[nama]["total_nominal"] += order.total or 0

    metode_stats = [
        SimpleNamespace(
            nama=nama,
            jumlah_order=data["jumlah_order"],
            total_nominal=data["total_nominal"]
        )
        for nama, data in rekap_metode.items()
    ]

    metode_list = MetodeBayar.query.order_by(
        MetodeBayar.nama.asc()
    ).all()

    return render_template(
        "laporan/index.html",
        orders=orders,
        start_date=tanggal_mulai.strftime("%Y-%m-%d"),
        end_date=tanggal_akhir.strftime("%Y-%m-%d"),
        status=status,
        metode_id=metode_id,
        metode_list=metode_list,
        total_omzet=total_omzet,
        total_transaksi=len(transaksi_aktif),
        total_subtotal=total_subtotal,
        total_pajak=total_pajak,
        total_batal=total_batal,
        metode_stats=metode_stats,
    )


@laporan_bp.route("/ekspor-penjualan")
@login_required
def ekspor_penjualan():
    tanggal_mulai, tanggal_akhir, status, metode_id = ambil_filter()

    orders = ambil_orders(
        tanggal_mulai,
        tanggal_akhir,
        status,
        metode_id
    )

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow([
        "Nomor Order",
        "Waktu",
        "Kasir",
        "Pelanggan",
        "Metode Pembayaran",
        "Subtotal",
        "PPN",
        "Total",
        "Status"
    ])

    for order in orders:
        writer.writerow([
            order.nomor,
            order.waktu.strftime("%d-%m-%Y %H:%M:%S")
            if order.waktu else "",
            order.kasir.nama if order.kasir else "",
            order.pelanggan.nama if order.pelanggan else "",
            order.metode_bayar.nama if order.metode_bayar else "",
            order.subtotal or 0,
            order.pajak or 0,
            order.total or 0,
            order.status
        ])

    nama_file = (
        f"laporan-penjualan-{tanggal_mulai}-"
        f"sampai-{tanggal_akhir}.csv"
    )

    response = Response(
        "\ufeff" + output.getvalue(),
        content_type="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        f'attachment; filename="{nama_file}"'
    )

    return response



@laporan_bp.route("/kartu-stok")
@login_required
def kartu_stok():
    produk_list = Produk.query.order_by(Produk.nama.asc()).all()

    try:
        produk_id = int(request.args.get("produk_id", ""))
    except (ValueError, TypeError):
        produk_id = None

    tipe = request.args.get("tipe", "semua")
    if tipe not in ("semua", "masuk", "keluar", "batal"):
        tipe = "semua"

    selected_produk = db.session.get(Produk, produk_id) if produk_id else None

    query = MutasiStok.query

    if produk_id and selected_produk:
        query = query.filter(MutasiStok.produk_id == produk_id)
    elif produk_id:
        produk_id = None

    if tipe != "semua":
        query = query.filter(MutasiStok.tipe == tipe)

    query = query.order_by(MutasiStok.waktu.desc(), MutasiStok.id.desc())

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    pagination = query.paginate(page=page, per_page=50, error_out=False)

    return render_template(
        "laporan/kartu_stok.html",
        produk_list=produk_list,
        produk_id=produk_id,
        tipe=tipe,
        selected_produk=selected_produk,
        mutasi_list=pagination.items,
        pagination=pagination,
    )


@laporan_bp.route("/ekspor-kartu-stok")
@login_required
def ekspor_kartu_stok():
    produk_id = request.args.get("produk_id", type=int)
    tipe = request.args.get("tipe", "semua")

    query = MutasiStok.query

    if produk_id:
        query = query.filter(MutasiStok.produk_id == produk_id)

    if tipe in ("masuk", "keluar", "batal"):
        query = query.filter(MutasiStok.tipe == tipe)

    mutasi = query.order_by(MutasiStok.waktu.desc(), MutasiStok.id.desc()).all()

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow([
        "Waktu", "Kode Produk", "Nama Produk", "Tipe",
        "Jumlah", "Stok Sebelum", "Stok Sesudah",
        "Keterangan", "Petugas"
    ])

    for m in mutasi:
        writer.writerow([
            m.waktu.strftime("%d-%m-%Y %H:%M:%S") if m.waktu else "",
            m.produk.kode if m.produk else "",
            m.produk.nama if m.produk else "",
            m.tipe,
            m.jumlah,
            m.stok_sebelum,
            m.stok_sesudah,
            m.keterangan or "",
            m.user.nama if m.user else "Sistem",
        ])

    response = Response(
        "\ufeff" + output.getvalue(),
        content_type="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = 'attachment; filename="kartu-stok.csv"'
    return response
