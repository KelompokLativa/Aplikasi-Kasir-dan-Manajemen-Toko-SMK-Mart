import os
import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import (
    User,
    Produk,
    Pelanggan,
    MetodeBayar,
    Pengaturan,
)


@click.command("seed")
@with_appcontext
def seed():
    admin_password = os.environ.get("ADMIN_PASSWORD")
    kasir_password = os.environ.get("KASIR_PASSWORD")

    if not admin_password or not kasir_password:
        raise click.ClickException(
            "ADMIN_PASSWORD dan KASIR_PASSWORD wajib diatur"
        )

    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    kasir_username = os.environ.get("KASIR_USERNAME", "kasir1")

    if not User.query.filter_by(username=admin_username).first():
        admin = User(
            nama="Pak Guru",
            username=admin_username,
            peran="admin",
            aktif=True,
        )
        admin.set_password(admin_password)
        db.session.add(admin)

    if not User.query.filter_by(username=kasir_username).first():
        kasir = User(
            nama="Siti Kasir",
            username=kasir_username,
            peran="kasir",
            aktif=True,
        )
        kasir.set_password(kasir_password)
        db.session.add(kasir)

    metode_list = [
        ("Tunai", "tunai"),
        ("Transfer", "transfer"),
        ("QRIS", "digital"),
    ]

    for nama, jenis in metode_list:
        if not MetodeBayar.query.filter_by(nama=nama).first():
            db.session.add(
                MetodeBayar(
                    nama=nama,
                    jenis=jenis,
                    aktif=True,
                )
            )

    if not Pelanggan.query.filter_by(nama="Umum").first():
        db.session.add(
            Pelanggan(
                nama="Umum",
                telepon=None,
                bawaan=True,
                aktif=True,
            )
        )

    if not Pengaturan.query.first():
        db.session.add(
            Pengaturan(
                nama_toko="SMK Mart",
                tarif_pajak=10,
                ambang_stok_menipis=5,
            )
        )

    daftar_produk = [
        ("MK001", "Air Mineral", "Minuman", 3000, 50),
        ("MK002", "Teh Botol", "Minuman", 5000, 30),
        ("MK003", "Kopi Sachet", "Minuman", 2000, 40),
        ("MK004", "Mie Instan", "Makanan", 3500, 50),
        ("MK005", "Roti", "Makanan", 5000, 20),
        ("MK006", "Biskuit", "Makanan", 4000, 30),
        ("MK007", "Keripik", "Makanan", 5000, 25),
        ("MK008", "Permen", "Makanan", 1000, 50),
        ("MK009", "Cokelat", "Makanan", 6000, 20),
        ("MK010", "Pulpen", "ATK", 3000, 30),
        ("MK011", "Pensil", "ATK", 2000, 30),
        ("MK012", "Buku Tulis", "ATK", 5000, 20),
        ("MK013", "Penghapus", "ATK", 2000, 20),
        ("MK014", "Tisu", "Kebutuhan", 3000, 20),
        ("MK015", "Sabun", "Kebutuhan", 5000, 20),
    ]

    for kode, nama, kategori, harga, stok in daftar_produk:
        if not Produk.query.filter_by(kode=kode).first():
            db.session.add(
                Produk(
                    kode=kode,
                    nama=nama,
                    kategori=kategori,
                    harga=harga,
                    stok=stok,
                    aktif=True,
                )
            )

    db.session.commit()

    click.echo("Data awal (seed) berhasil disimpan")


def register_commands(app):
    app.cli.add_command(seed)
