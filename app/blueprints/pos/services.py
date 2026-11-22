from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func

from app.extensions import db
from app.models import (
    Order,
    OrderItem,
    Produk,
    Pelanggan,
    MetodeBayar,
    Pengaturan,
    MutasiStok,
)


def hitung_pajak_dan_total(subtotal, tarif_pajak):
    subtotal = int(subtotal or 0)
    tarif = Decimal(str(tarif_pajak or 0))
    nilai_pajak = Decimal(subtotal) * tarif / Decimal("100")

    pajak = int(
        nilai_pajak.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )
    )

    return pajak, subtotal + pajak


def proses_checkout(payload, kasir):
    items = payload.get("items") or []

    if not items:
        raise ValueError("Keranjang masih kosong.")

    metode = db.session.get(
        MetodeBayar,
        payload.get("metode_bayar_id")
    )

    if not metode or not metode.aktif:
        raise ValueError("Metode pembayaran tidak valid.")

    pengaturan = Pengaturan.query.first()
    tarif = pengaturan.tarif_pajak if pengaturan else 0

    pelanggan_id = payload.get("pelanggan_id")

    if pelanggan_id:
        pelanggan = db.session.get(Pelanggan, pelanggan_id)
        if not pelanggan:
            raise ValueError("Pelanggan tidak ditemukan.")
    else:
        pelanggan = Pelanggan.query.filter_by(bawaan=True).first()
        if not pelanggan:
            raise ValueError("Pelanggan umum belum tersedia.")

    daftar_item = []
    subtotal = 0

    for item in items:
        try:
            produk_id = int(item.get("produk_id"))
            jumlah = int(item.get("jumlah"))
        except (ValueError, TypeError):
            raise ValueError("Data produk atau jumlah tidak valid.")

        if jumlah <= 0:
            raise ValueError("Jumlah produk harus lebih dari 0.")

        produk = db.session.execute(
            db.select(Produk)
            .where(Produk.id == produk_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not produk or not produk.aktif or produk.stok <= 0:
            raise ValueError("Produk tidak tersedia atau stok habis.")

        if jumlah > produk.stok:
            raise ValueError(
                f"Stok {produk.nama} hanya {produk.stok}."
            )

        nilai = produk.harga * jumlah
        subtotal += nilai
        daftar_item.append((produk, jumlah, nilai))

    pajak, total = hitung_pajak_dan_total(subtotal, tarif)

    tunai = metode.jenis == "tunai"
    uang = payload.get("uang_diterima")

    if tunai:
        try:
            uang = int(uang)
        except (ValueError, TypeError):
            raise ValueError("Uang diterima wajib diisi.")

        if uang < total:
            selisih = total - uang
            raise ValueError(
                f"Uang diterima kurang Rp {selisih:,}".replace(",", ".") + "."
            )

        kembalian = uang - total
    else:
        uang = None
        kembalian = None

    tanggal = datetime.now()
    awal_hari = tanggal.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    jumlah_hari_ini = Order.query.filter(
        Order.waktu >= awal_hari
    ).count()

    nomor = f"POS-{tanggal:%Y%m%d}-{jumlah_hari_ini + 1:04d}"

    try:
        order = Order(
            nomor=nomor,
            waktu=tanggal,
            kasir_id=kasir.id,
            pelanggan_id=pelanggan.id,
            metode_bayar_id=metode.id,
            subtotal=subtotal,
            tarif_pajak=tarif,
            pajak=pajak,
            total=total,
            uang_diterima=uang,
            kembalian=kembalian,
            status="selesai",
        )

        db.session.add(order)
        db.session.flush()

        for produk, jumlah, nilai in daftar_item:
            stok_sebelum = produk.stok
            produk.stok -= jumlah
            stok_sesudah = produk.stok

            db.session.add(OrderItem(
                order_id=order.id,
                produk_id=produk.id,
                nama_produk=produk.nama,
                harga_satuan=produk.harga,
                jumlah=jumlah,
                subtotal=nilai,
            ))

            db.session.add(MutasiStok(
                produk_id=produk.id,
                user_id=kasir.id,
                waktu=tanggal,
                tipe="keluar",
                jumlah=jumlah,
                stok_sebelum=stok_sebelum,
                stok_sesudah=stok_sesudah,
                keterangan=f"Penjualan {nomor}",
            ))

        db.session.commit()

        return order

    except Exception:
        db.session.rollback()
        raise


def buat_pelanggan_cepat(nama, telepon=None):
    nama = (nama or "").strip()

    if not nama:
        raise ValueError("Nama pelanggan wajib diisi.")

    pelanggan = Pelanggan(
        nama=nama,
        telepon=(telepon or "").strip() or None,
        bawaan=False,
    )

    db.session.add(pelanggan)
    db.session.commit()

    return pelanggan
