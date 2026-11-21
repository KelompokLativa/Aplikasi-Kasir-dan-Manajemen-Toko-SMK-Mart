
import csv
import io

from flask import Blueprint, Response, render_template_string

from app.decorators import admin_required
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
    order_list = (
        Order.query
        .order_by(Order.waktu.desc())
        .all()
    )

    total_omzet = sum(
        order.total
        for order in order_list
        if order.status == "selesai"
    )

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan Keuangan & Penjualan</title>
    </head>
    <body>
        <h1>Laporan Keuangan & Penjualan</h1>

        <h2>Total Omzet Bersih</h2>
        <p>Rp {{ omzet }}</p>

        <a href="/laporan/penjualan/ekspor">
            Ekspor ke Excel (CSV)
        </a>

        <hr>

        <h3>Data Penjualan</h3>

        <table border="1" cellpadding="8">
            <thead>
                <tr>
                    <th>No. Order</th>
                    <th>Waktu</th>
                    <th>Kasir</th>
                    <th>Pelanggan</th>
                    <th>Subtotal</th>
                    <th>Total</th>
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
        html,
        orders=order_list,
        omzet=format_rupiah(total_omzet),
        format=format_rupiah,
    )


@laporan_bp.route("/laporan/penjualan/ekspor")
@admin_required
def ekspor_penjualan():
    order_list = (
        Order.query
        .order_by(Order.waktu.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "No. Order",
        "Tanggal",
        "Kasir",
        "Pelanggan",
        "Pajak (Rp)",
        "Subtotal (Rp)",
        "Total (Rp)",
        "Metode Pembayaran",
        "Status",
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
            order.status,
        ])

    response = Response(
        output.getvalue(),
        content_type="text/csv; charset=utf-8",
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=laporan_penjualan.csv"
    )

    return response


@laporan_bp.route("/laporan/kartu-stok")
@admin_required
def kartu_stok():
    mutasi_list = (
        MutasiStok.query
        .order_by(MutasiStok.waktu.desc())
        .all()
    )

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kartu Stok & Log Mutasi</title>
    </head>
    <body>
        <h1>Kartu Stok & Log Mutasi</h1>

        <a href="/laporan/kartu-stok/ekspor">
            Ekspor Kartu Stok (CSV)
        </a>

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
        html,
        mutasi_list=mutasi_list,
    )


@laporan_bp.route("/laporan/kartu-stok/ekspor")
@admin_required
def ekspor_kartu_stok():
    mutasi_list = (
        MutasiStok.query
        .order_by(MutasiStok.waktu.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "ID Mutasi",
        "Kode Produk",
        "Nama Produk",
        "Tipe",
        "Jumlah",
        "Stok Sebelum",
        "Stok Sesudah",
        "Keterangan",
        "Waktu",
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
            mutasi.waktu.strftime("%d-%m-%Y %H:%M"),
        ])

    response = Response(
        output.getvalue(),
        content_type="text/csv; charset=utf-8",
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=kartu_stok.csv"
    )

    return response
