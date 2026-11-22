
import csv
import io
from datetime import datetime

from flask import Blueprint, Response, render_template_string, request, redirect, url_for
from app.decorators import admin_required
from app.extensions import db
from app.models.order import Order
from app.models.produk import Produk
from app.models.mutasi_stok import MutasiStok


laporan_bp = Blueprint("laporan", __name__)


def format_rupiah(nilai):
    return f"{nilai:,.0f}".replace(",", ".")


@laporan_bp.route("/laporan")
@laporan_bp.route("/laporan/")
@admin_required
def index():
    order_list = Order.query.order_by(Order.waktu.desc()).all()

    total_omzet = sum(
        order.total for order in order_list if order.status == "selesai"
    )

    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Laporan Keuangan & Penjualan</title></head>
    <body>
        <h1>Laporan Keuangan & Penjualan</h1>
        <h2>Total Omzet Bersih</h2>
        <p>Rp {{ omzet }}</p>
        <a href="/laporan/penjualan/ekspor">Ekspor ke Excel (CSV)</a>
        <hr>
        <h3>Data Penjualan</h3>
        <table border="1" cellpadding="8">
            <thead>
                <tr>
                    <th>No. Order</th><th>Waktu</th><th>Kasir</th>
                    <th>Pelanggan</th><th>Subtotal</th><th>Total</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for order in orders %}
                <tr>
                    <td>{{ order.nomor }}</td>
                    <td>{{ order.waktu }}</td>
                    <td>{{ order.kasir.nama }}</td>
                    <td>{{ order.pelanggan.nama }}</td>
                    <td>Rp {{ format(order.subtotal) }}</td>
                    <td>Rp {{ format(order.total) }}</td>
                    <td>{{ order.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """

    return render_template_string(
        html, orders=order_list, omzet=format_rupiah(total_omzet),
        format=format_rupiah
    )


@laporan_bp.route("/laporan/penjualan/ekspor")
@admin_required
def ekspor_penjualan():
    order_list = Order.query.order_by(Order.waktu.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "No. Order", "Tanggal", "Kasir", "Pelanggan",
        "Pajak (Rp)", "Subtotal (Rp)", "Total (Rp)",
        "Metode Pembayaran", "Status"
    ])

    for order in order_list:
        writer.writerow([
            order.nomor,
            order.waktu.strftime("%d-%m-%Y %H:%M"),
            order.kasir.nama,
            order.pelanggan.nama,
            order.pajak,
            order.subtotal,
            order.total,
            order.metode_bayar.nama,
            order.status
        ])

    response = Response(
        output.getvalue(),
        content_type="text/csv; charset=utf-8"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=laporan_penjualan.csv"
    )
    return response


@laporan_bp.route("/laporan/kartu-stok")
@admin_required
def kartu_stok():
    mutasi_list = MutasiStok.query.order_by(MutasiStok.waktu.desc()).all()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kartu Stok & Log Mutasi</title>
    </head>
    <body>
        <h1>Kartu Stok & Log Mutasi</h1>

        {% for pesan in pesan_list %}
        <p>{{ pesan }}</p>
        {% endfor %}

        <a href="/laporan/kartu-stok/ekspor">Ekspor Kartu Stok (CSV)</a>

        <h2>Impor Kartu Stok CSV</h2>
        <form method="post" action="/laporan/kartu-stok/impor"
              enctype="multipart/form-data">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="file" name="file" accept=".csv" required>
            <button type="submit">Impor CSV</button>
        </form>

        <p>Format CSV menggunakan pemisah titik koma (;).</p>

        <hr>

        <table border="1" cellpadding="8">
            <thead>
                <tr>
                    <th>ID Mutasi</th>
                    <th>Kode Produk</th>
                    <th>Nama Produk</th>
                    <th>Tipe</th>
                    <th>Jumlah</th>
                    <th>Stok Sebelum</th>
                    <th>Stok Sesudah</th>
                    <th>Keterangan</th>
                    <th>Waktu</th>
                </tr>
            </thead>
            <tbody>
                {% for mutasi in mutasi_list %}
                <tr>
                    <td>{{ mutasi.id }}</td>
                    <td>{{ mutasi.produk.kode }}</td>
                    <td>{{ mutasi.produk.nama }}</td>
                    <td>{{ mutasi.tipe }}</td>
                    <td>{{ mutasi.jumlah }}</td>
                    <td>{{ mutasi.stok_sebelum }}</td>
                    <td>{{ mutasi.stok_sesudah }}</td>
                    <td>{{ mutasi.keterangan or '-' }}</td>
                    <td>{{ mutasi.waktu }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """

    return render_template_string(
        html, mutasi_list=mutasi_list, pesan_list=[]
    )


@laporan_bp.route("/laporan/kartu-stok/impor", methods=["POST"])
@admin_required
def impor_kartu_stok():
    file = request.files.get("file")

    if not file or not file.filename:
        return "File CSV belum dipilih.", 400

    if not file.filename.lower().endswith(".csv"):
        return "File harus berformat CSV.", 400

    try:
        isi = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(isi), delimiter=";")

        kolom_wajib = [
            "ID Mutasi", "Kode Produk", "Nama Produk", "Tipe",
            "Jumlah", "Stok Sebelum", "Stok Sesudah",
            "Keterangan", "Waktu"
        ]

        if not reader.fieldnames or not all(
            kolom in reader.fieldnames for kolom in kolom_wajib
        ):
            return "Format kolom CSV tidak sesuai.", 400

        baris = list(reader)

        if not baris:
            return "CSV tidak memiliki data.", 400

        perubahan = []
        stok_simulasi = {}
        produk_cache = {}

        for nomor, row in enumerate(baris, start=2):
            kode = (row.get("Kode Produk") or "").strip()
            tipe = (row.get("Tipe") or "").strip().lower()

            if not kode:
                raise ValueError(f"Baris {nomor}: kode produk kosong.")

            produk = Produk.query.filter_by(kode=kode).first()

            if produk is None:
                raise ValueError(
                    f"Baris {nomor}: produk dengan kode {kode} tidak ditemukan."
                )

            if tipe not in ("masuk", "keluar"):
                raise ValueError(
                    f"Baris {nomor}: tipe harus masuk atau keluar."
                )

            try:
                jumlah = int(row["Jumlah"])
                stok_sebelum_csv = int(row["Stok Sebelum"])
                stok_sesudah_csv = int(row["Stok Sesudah"])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Baris {nomor}: jumlah dan stok harus berupa angka."
                )

            if jumlah <= 0:
                raise ValueError(
                    f"Baris {nomor}: jumlah harus lebih dari 0."
                )

            if produk.id not in stok_simulasi:
                stok_simulasi[produk.id] = produk.stok
                produk_cache[produk.id] = produk

            stok_sebelum = stok_simulasi[produk.id]

            if stok_sebelum_csv != stok_sebelum:
                raise ValueError(
                    f"Baris {nomor}: stok sebelum CSV ({stok_sebelum_csv}) "
                    f"tidak sama dengan stok aplikasi ({stok_sebelum})."
                )

            if tipe == "masuk":
                stok_sesudah = stok_sebelum + jumlah
            else:
                stok_sesudah = stok_sebelum - jumlah

                if stok_sesudah < 0:
                    raise ValueError(
                        f"Baris {nomor}: stok tidak mencukupi."
                    )

            if stok_sesudah_csv != stok_sesudah:
                raise ValueError(
                    f"Baris {nomor}: perhitungan stok sesudah tidak sesuai."
                )

            waktu_text = (row.get("Waktu") or "").strip()
            waktu = None

            for fmt in (
                "%d-%m-%Y %H:%M",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d %H:%M",
                "%d-%m-%Y",
            ):
                if waktu_text:
                    try:
                        waktu = datetime.strptime(waktu_text, fmt)
                        break
                    except ValueError:
                        pass

            if waktu is None:
                if waktu_text:
                    raise ValueError(
                        f"Baris {nomor}: format waktu tidak sesuai."
                    )
                waktu = datetime.utcnow()

            perubahan.append({
                "produk": produk,
                "tipe": tipe,
                "jumlah": jumlah,
                "sebelum": stok_sebelum,
                "sesudah": stok_sesudah,
                "keterangan": (row.get("Keterangan") or "").strip(),
                "waktu": waktu,
            })

            stok_simulasi[produk.id] = stok_sesudah

        for item in perubahan:
            item["produk"].stok = item["sesudah"]

            db.session.add(MutasiStok(
                produk_id=item["produk"].id,
                tipe=item["tipe"],
                jumlah=item["jumlah"],
                stok_sebelum=item["sebelum"],
                stok_sesudah=item["sesudah"],
                keterangan=item["keterangan"],
                waktu=item["waktu"],
            ))

        db.session.commit()

        return (
            f"Impor berhasil! {len(perubahan)} data mutasi telah diproses. "
            '<a href="/laporan/kartu-stok">Kembali ke Kartu Stok</a>'
        )

    except Exception as e:
        db.session.rollback()
        return (
            f"Impor gagal: {e} "
            '<a href="/laporan/kartu-stok">Kembali</a>'
        ), 400


@laporan_bp.route("/laporan/kartu-stok/ekspor")
@admin_required
def ekspor_kartu_stok():
    mutasi_list = MutasiStok.query.order_by(MutasiStok.waktu.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "ID Mutasi", "Kode Produk", "Nama Produk", "Tipe",
        "Jumlah", "Stok Sebelum", "Stok Sesudah",
        "Keterangan", "Waktu"
    ])

    for mutasi in mutasi_list:
        writer.writerow([
            mutasi.id,
            mutasi.produk.kode,
            mutasi.produk.nama,
            mutasi.tipe,
            mutasi.jumlah,
            mutasi.stok_sebelum,
            mutasi.stok_sesudah,
            mutasi.keterangan or "-",
            mutasi.waktu.strftime("%d-%m-%Y %H:%M")
        ])

    response = Response(
        output.getvalue(),
        content_type="text/csv; charset=utf-8"
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=kartu_stok.csv"
    )
    return response
