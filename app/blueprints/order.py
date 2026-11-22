from datetime import datetime, timedelta

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import Order, User

order_bp = Blueprint("order", __name__, url_prefix="/order")


@order_bp.route("/")
@login_required
def index():
    today = datetime.now().date()
    start_date = today
    end_date = today

    query = Order.query

    # Kasir hanya melihat transaksi miliknya.
    if not current_user.is_admin:
        query = query.filter(
            Order.kasir_id == current_user.id
        )

    # Default hanya transaksi hari ini.
    awal = datetime.combine(
        start_date,
        datetime.min.time()
    )
    akhir = awal + timedelta(days=1)

    query = query.filter(
        Order.waktu >= awal,
        Order.waktu < akhir
    )

    orders = query.order_by(
        Order.waktu.desc()
    ).all()

    kasir_list = User.query.filter_by(
        peran="kasir",
        aktif=True
    ).order_by(User.nama.asc()).all()

    pengajuan_batal_count = Order.query.filter_by(
        status="pengajuan_batal"
    ).count()

    return render_template(
        "order/index.html",
        start_date=start_date,
        end_date=end_date,
        status="",
        kasir_id="",
        q="",
        kasir_list=kasir_list,
        orders=orders,
        pagination=None,
        pengajuan_batal_count=pengajuan_batal_count,
    )


@order_bp.route("/<int:order_id>/detail")
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)

    if not current_user.is_admin:
        if order.kasir_id != current_user.id:
            abort(403)

    return {
        "id": order.id,
        "nomor": order.nomor,
        "kasir": order.kasir.nama if order.kasir else "-",
        "waktu": order.waktu.isoformat() if order.waktu else None,
        "pelanggan": (
            order.pelanggan.nama
            if order.pelanggan else "-"
        ),
        "metode": (
            order.metode_bayar.nama
            if order.metode_bayar else "-"
        ),
        "status": order.status,
        "items": [
            {
                "nama_produk": item.nama_produk,
                "jumlah": item.jumlah,
                "harga_satuan": item.harga_satuan,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ],
        "subtotal": order.subtotal,
        "tarif_pajak": order.tarif_pajak,
        "pajak": order.pajak,
        "total": order.total,
        "alasan_batal": order.alasan_batal,
        "diajukan_oleh": (
            order.diajukan_oleh.nama
            if order.diajukan_oleh else None
        ),
        "dikonfirmasi_oleh": (
            order.dikonfirmasi_oleh.nama
            if order.dikonfirmasi_oleh else None
        ),
        "waktu_batal": (
            order.waktu_batal.isoformat()
            if order.waktu_batal else None
        ),
    }