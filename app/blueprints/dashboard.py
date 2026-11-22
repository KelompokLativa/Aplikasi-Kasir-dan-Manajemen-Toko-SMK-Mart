
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import (
    Order,
    OrderItem,
    Produk,
    Pengaturan,
)

dashboard_bp = Blueprint("dashboard", __name__)

WIB = timezone(timedelta(hours=7))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    if not current_user.is_admin:
        abort(403)

    sekarang = datetime.now(WIB)
    hari_ini = sekarang.date()

    # Pengaturan toko
    pengaturan = Pengaturan.query.first()
    ambang = pengaturan.ambang_stok_menipis if pengaturan else 5

    # Awal dan akhir hari WIB dikonversi ke UTC
    awal_hari = datetime.combine(
        hari_ini, datetime.min.time()
    ).replace(tzinfo=WIB).astimezone(timezone.utc).replace(tzinfo=None)

    akhir_hari = awal_hari + timedelta(days=1)

    # Transaksi hari ini, kecuali yang dibatalkan
    order_hari_ini = Order.query.filter(
        Order.waktu >= awal_hari,
        Order.waktu < akhir_hari,
        Order.status != "dibatalkan"
    ).all()

    omzet_hari_ini = sum(o.total for o in order_hari_ini)
    jumlah_order_hari_ini = len(order_hari_ini)

    rata_rata_order = (
        omzet_hari_ini / jumlah_order_hari_ini
        if jumlah_order_hari_ini else 0
    )

    # Grafik omzet 7 hari terakhir
    grafik_7_hari = []
    total_omzet_7_hari = 0

    for mundur in range(6, -1, -1):
        tanggal = hari_ini - timedelta(days=mundur)

        awal = datetime.combine(
            tanggal, datetime.min.time()
        ).replace(tzinfo=WIB).astimezone(timezone.utc).replace(tzinfo=None)

        akhir = awal + timedelta(days=1)

        omzet = db.session.query(
            func.coalesce(func.sum(Order.total), 0)
        ).filter(
            Order.waktu >= awal,
            Order.waktu < akhir,
            Order.status != "dibatalkan"
        ).scalar()

        omzet = int(omzet or 0)
        total_omzet_7_hari += omzet

        grafik_7_hari.append({
            "label": tanggal.strftime("%d/%m"),
            "omzet": omzet,
            "is_today": mundur == 0,
            "height_pct": 0,
        })

    nilai_maksimum = max(
        (g["omzet"] for g in grafik_7_hari),
        default=0
    )

    for grafik in grafik_7_hari:
        grafik["height_pct"] = (
            grafik["omzet"] / nilai_maksimum * 100
            if nilai_maksimum else 0
        )

    # 5 produk terlaris dalam 30 hari terakhir
    batas_30_hari = (
        sekarang - timedelta(days=30)
    ).astimezone(timezone.utc).replace(tzinfo=None)

    top_products = db.session.query(
        OrderItem.nama_produk.label("nama"),
        func.sum(OrderItem.jumlah).label("terjual"),
        func.sum(OrderItem.subtotal).label("omzet"),
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.waktu >= batas_30_hari,
        Order.status != "dibatalkan"
    ).group_by(
        OrderItem.nama_produk
    ).order_by(
        func.sum(OrderItem.jumlah).desc()
    ).limit(5).all()

    # Produk aktif dengan stok menipis
    stok_menipis = Produk.query.filter(
        Produk.aktif.is_(True),
        Produk.stok <= ambang
    ).order_by(Produk.stok.asc()).all()

    # Pengajuan pembatalan menunggu persetujuan
    pengajuan_batal_count = Order.query.filter_by(
        status="pengajuan_batal"
    ).count()

    # 5 transaksi terbaru
    order_terbaru = Order.query.order_by(
        Order.waktu.desc()
    ).limit(5).all()

    return render_template(
        "dashboard/index.html",
        nama_toko=(
            pengaturan.nama_toko
            if pengaturan else "SMK Mart POS"
        ),
        omzet_hari_ini=omzet_hari_ini,
        jumlah_order_hari_ini=jumlah_order_hari_ini,
        rata_rata_order=rata_rata_order,
        grafik_7_hari=grafik_7_hari,
        total_omzet_7_hari=total_omzet_7_hari,
        top_products=top_products,
        stok_menipis=stok_menipis,
        ambang=ambang,
        pengajuan_batal_count=pengajuan_batal_count,
        order_terbaru=order_terbaru,
    )
