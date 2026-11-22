from flask import Blueprint, request, redirect, url_for, flash, render_template_string
from app.decorators import admin_required
from app.extensions import db
from app.models.produk import Produk
from app.models.mutasi_stok import MutasiStok
from app.models.pengaturan import Pengaturan

produk_bp = Blueprint("produk", __name__)

TEMPLATE = """
<!DOCTYPE html>
<html><head><title>Master Produk</title></head>
<body>
<h1>Master Produk</h1>
{% for m in messages %}<p>{{ m }}</p>{% endfor %}
<form method="get">
<input name="q" value="{{ q }}" placeholder="Cari produk">
<input name="kategori" value="{{ kategori }}" placeholder="Kategori">
<button type="submit">Cari</button>
</form>
<p>Ambang stok menipis: {{ ambang }}</p>
<table border="1">
<tr><th>Kode</th><th>Nama</th><th>Kategori</th><th>Harga</th><th>Stok</th><th>Status</th></tr>
{% for p in produk %}
<tr>
<td>{{ p.kode }}</td><td>{{ p.nama }}</td><td>{{ p.kategori }}</td>
<td>{{ p.harga }}</td><td>{{ p.stok }}</td>
<td>{% if p.stok <= ambang %}Menipis: {{ p.stok }}{% else %}Aman{% endif %}</td>
</tr>
{% endfor %}
</table>
<a href="/produk/tambah">Tambah Produk</a>
</body></html>
"""

FORM = """
<!DOCTYPE html><html><body><h1>Tambah Produk</h1>
{% for m in messages %}<p>{{ m }}</p>{% endfor %}
<form method="post">
<input name="kode" placeholder="Kode">
<input name="nama" placeholder="Nama">
<input name="kategori" placeholder="Kategori">
<input name="harga" placeholder="Harga">
<input name="stok" placeholder="Stok">
<input type="checkbox" name="aktif" value="y" checked>
<button type="submit">Simpan</button>
</form></body></html>
"""


def ambang_stok():
    cfg = Pengaturan.query.first()
    return cfg.ambang_stok_menipis if cfg else 5


@produk_bp.route("/produk")
@produk_bp.route("/produk/")
@admin_required
def index():
    q = request.args.get("q", "").strip()
    kategori = request.args.get("kategori", "").strip()
    query = Produk.query

    if q:
        query = query.filter(
            db.or_(Produk.nama.ilike(f"%{q}%"), Produk.kode.ilike(f"%{q}%"))
        )
    if kategori:
        query = query.filter(Produk.kategori == kategori)

    produk = query.order_by(Produk.nama.asc()).all()
    messages = []
    return render_template_string(
        TEMPLATE, produk=produk, q=q, kategori=kategori,
        ambang=ambang_stok(), messages=messages
    )


@produk_bp.route("/produk/tambah", methods=["GET", "POST"])
@admin_required
def tambah():
    if request.method == "POST":
        kode = request.form.get("kode", "").strip()
        nama = request.form.get("nama", "").strip()
        kategori = request.form.get("kategori", "Umum").strip() or "Umum"

        try:
            harga = int(request.form.get("harga", ""))
        except (ValueError, TypeError):
            harga = -1

        try:
            stok = int(request.form.get("stok", ""))
        except (ValueError, TypeError):
            stok = -1

        if not kode or not nama:
            flash("Kode dan nama produk wajib diisi.")
        elif Produk.query.filter_by(kode=kode).first():
            flash(f"Kode {kode} sudah dipakai produk lain.")
        else:
            if harga < 0:
                flash("Harga harus berupa angka dan minimal 0.")
            if stok < 0:
                flash("Stok harus berupa angka dan minimal 0.")
            if harga >= 0 and stok >= 0:
                p = Produk(
                    kode=kode, nama=nama, kategori=kategori,
                    harga=harga, stok=stok,
                    aktif=bool(request.form.get("aktif"))
                )
                db.session.add(p)
                db.session.commit()
                flash(f"Produk {nama} tersimpan.")
                return redirect(url_for("produk.index"))

        return render_template_string(FORM, messages=[m for m in []])

    return render_template_string(FORM, messages=[])


@produk_bp.route("/produk/<int:id>/ubah", methods=["GET", "POST"])
@admin_required
def ubah(id):
    p = db.session.get(Produk, id)
    if p is None:
        return "Produk tidak ditemukan.", 404

    if request.method == "POST":
        kode = request.form.get("kode", p.kode).strip()
        nama = request.form.get("nama", p.nama).strip()
        kategori = request.form.get("kategori", p.kategori).strip() or "Umum"

        duplicate = Produk.query.filter(Produk.kode == kode, Produk.id != id).first()
        if duplicate:
            flash(f"Kode {kode} sudah dipakai produk lain.")
        else:
            try:
                harga = int(request.form.get("harga", p.harga))
            except (ValueError, TypeError):
                harga = -1
            try:
                stok = int(request.form.get("stok", p.stok))
            except (ValueError, TypeError):
                stok = -1

            if harga < 0:
                flash("Harga harus berupa angka dan minimal 0.")
            if stok < 0:
                flash("Stok harus berupa angka dan minimal 0.")
            if harga >= 0 and stok >= 0:
                p.kode = kode
                p.nama = nama
                p.kategori = kategori
                p.harga = harga
                p.stok = stok
                p.aktif = bool(request.form.get("aktif"))
                db.session.commit()
                return redirect(url_for("produk.index"))

    return render_template_string(FORM, messages=[])


@produk_bp.route("/produk/<int:id>/tambah-stok", methods=["POST"])
@admin_required
def tambah_stok(id):
    produk = db.session.get(Produk, id)
    if produk is None:
        return {"success": False, "message": "Produk tidak ditemukan."}, 404

    data = request.get_json(silent=True) or {}
    jumlah = data.get("jumlah")
    keterangan = data.get("keterangan", "Penambahan stok")

    if isinstance(jumlah, bool) or not isinstance(jumlah, int) or jumlah <= 0:
        return {"success": False, "message": "Jumlah stok harus berupa angka positif."}, 400

    stok_sebelum = produk.stok
    stok_sesudah = stok_sebelum + jumlah
    produk.stok = stok_sesudah
    db.session.add(MutasiStok(
        produk_id=produk.id, tipe="masuk", jumlah=jumlah,
        stok_sebelum=stok_sebelum, stok_sesudah=stok_sesudah,
        keterangan=keterangan
    ))
    db.session.commit()
    return {"success": True, "message": "Stok berhasil ditambahkan.", "stok_baru": stok_sesudah}, 200
