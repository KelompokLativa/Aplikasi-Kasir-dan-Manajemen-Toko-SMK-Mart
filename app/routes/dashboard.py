from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from app.decorators import admin_required
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.produk import Produk
from app.models.pengaturan import Pengaturan

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@admin_required
def index():
    # Waktu sekarang
    utc_now = datetime.now(timezone.utc)
    utc_naive = utc_now.replace(tzinfo=None)
    wib_now = utc_now + timedelta(hours=7)
    today_wib = wib_now.date()

    # Batas waktu hari ini (WIB dikonversi ke UTC)
    start_today = datetime.combine(
        today_wib, datetime.min.time()
    ) - timedelta(hours=7)

    end_today = start_today + timedelta(days=1)

    # Transaksi hari ini
    orders_today = Order.query.filter(
        Order.waktu >= start_today,
        Order.waktu < end_today,
        Order.status != "dibatalkan"
    ).all()

    omzet_hari_ini = sum(o.total for o in orders_today)
    jumlah_order_hari_ini = len(orders_today)
    rata_rata_order = (
        omzet_hari_ini // jumlah_order_hari_ini
        if jumlah_order_hari_ini else 0
    )

    # Grafik omzet 7 hari (termasuk hari ini)
    start_date_7 = today_wib - timedelta(days=6)
    start_7 = datetime.combine(
        start_date_7, datetime.min.time()
    ) - timedelta(hours=7)

    orders_7 = Order.query.filter(
        Order.waktu >= start_7,
        Order.waktu < end_today,
        Order.status != "dibatalkan"
    ).all()

    grafik_7_hari = []

    for i in range(7):
        tanggal = start_date_7 + timedelta(days=i)
        start_day = datetime.combine(
            tanggal, datetime.min.time()
        ) - timedelta(hours=7)
        end_day = start_day + timedelta(days=1)

        omzet_harian = sum(
            o.total for o in orders_7
            if start_day <= o.waktu < end_day
        )

        grafik_7_hari.append({
            "label": tanggal.strftime("%d/%m"),
            "omzet": omzet_harian,
            "is_today": tanggal == today_wib,
            "height_pct": 0,
        })

    total_omzet_7_hari = sum(
        item["omzet"] for item in grafik_7_hari
    )

    nilai_max = max(
        (item["omzet"] for item in grafik_7_hari),
        default=0
    )

    for item in grafik_7_hari:
        item["height_pct"] = (
            max(8, int(item["omzet"] / nilai_max * 100))
            if nilai_max else 8
        )

    # Produk terlaris 30 hari
    start_30 = utc_naive - timedelta(days=30)

    hasil_produk = (
        db.session.query(
            OrderItem.nama_produk,
            db.func.sum(OrderItem.subtotal),
            db.func.sum(OrderItem.jumlah),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.waktu >= start_30,
            Order.status != "dibatalkan"
        )
        .group_by(OrderItem.nama_produk)
        .order_by(db.func.sum(OrderItem.jumlah).desc())
        .limit(5)
        .all()
    )

    top_products = [
        {
            "nama": nama,
            "omzet": omzet_produk or 0,
            "terjual": jumlah or 0,
        }
        for nama, omzet_produk, jumlah in hasil_produk
    ]

    # Stok menipis
    cfg = Pengaturan.query.first()
    ambang = cfg.ambang_stok_menipis if cfg else 5

    stok_menipis = Produk.query.filter(
        Produk.aktif.is_(True),
        Produk.stok <= ambang
    ).order_by(Produk.stok.asc()).all()

    # Pengajuan pembatalan
    pengajuan_batal_count = Order.query.filter_by(
        status="pengajuan_batal"
    ).count()

    # Transaksi terbaru
    order_terbaru = Order.query.order_by(
        Order.waktu.desc()
    ).limit(10).all()

    return render_template(
        "dashboard/index.html",
        pengajuan_batal_count=pengajuan_batal_count,
        omzet_hari_ini=omzet_hari_ini,
        jumlah_order_hari_ini=jumlah_order_hari_ini,
        rata_rata_order=rata_rata_order,
        total_omzet_7_hari=total_omzet_7_hari,
        grafik_7_hari=grafik_7_hari,
        top_products=top_products,
        stok_menipis=stok_menipis,
        ambang=ambang,
        order_terbaru=order_terbaru,
    )


@dashboard_bp.app_template_filter("rupiah")
def rupiah(value):
    return "Rp {:,.0f}".format(value or 0).replace(",", ".")