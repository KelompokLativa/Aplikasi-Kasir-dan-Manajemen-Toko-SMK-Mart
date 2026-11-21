
from flask import (
    Blueprint, request, redirect,
    url_for, render_template_string
)
from app.decorators import admin_required
from app.extensions import db
from app.models.pengaturan import Pengaturan

pengaturan_bp = Blueprint("pengaturan", __name__)


TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pengaturan Toko</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            margin: 30px;
            color: #222;
        }
        .container {
            max-width: 650px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        h1 { color: #1e3a5f; }
        label {
            display: block;
            margin-top: 18px;
            font-weight: bold;
        }
        input, textarea {
            width: 100%;
            padding: 11px;
            margin-top: 7px;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        button {
            margin-top: 25px;
            padding: 12px 20px;
            background: #198754;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover { background: #146c43; }
        .pesan {
            padding: 12px;
            background: #e9f5e9;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        .keterangan {
            color: #666;
            font-size: 13px;
        }
        a { color: #1e3a5f; }
    </style>
</head>
<body>
<div class="container">
    <h1>Pengaturan Toko</h1>
    <p>Atur identitas dan ketentuan operasional toko.</p>

    {% for pesan in messages %}
        <div class="pesan">{{ pesan }}</div>
    {% endfor %}

    <form method="post">
        <input type="hidden" name="csrf_token"
               value="{{ csrf_token() }}">

        <label>Nama Toko</label>
        <input type="text" name="nama_toko"
               maxlength="100" required
               value="{{ pengaturan.nama_toko }}">

        <label>Alamat Toko</label>
        <textarea name="alamat_toko" rows="3"
                  maxlength="255">{{ pengaturan.alamat_toko or '' }}</textarea>

        <label>Tarif Pajak (%)</label>
        <input type="number" name="tarif_pajak"
               min="0" max="100" step="0.01" required
               value="{{ pengaturan.tarif_pajak }}">
        <p class="keterangan">
            Masukkan persentase pajak, misalnya 10 untuk 10%.
        </p>

        <label>Ambang Stok Menipis</label>
        <input type="number" name="ambang_stok_menipis"
               min="0" required
               value="{{ pengaturan.ambang_stok_menipis }}">
        <p class="keterangan">
            Produk akan dianggap menipis jika stok sama dengan
            atau di bawah angka ini.
        </p>

        <button type="submit">Simpan Pengaturan</button>
    </form>

    <hr>
    <a href="/dashboard">Kembali ke Dashboard</a>
</div>
</body>
</html>
"""


@pengaturan_bp.route("/pengaturan", methods=["GET", "POST"])
@admin_required
def index():
    pengaturan = Pengaturan.query.first()

    if pengaturan is None:
        pengaturan = Pengaturan()
        db.session.add(pengaturan)
        db.session.commit()

    messages = []

    if request.method == "POST":
        nama_toko = request.form.get("nama_toko", "").strip()
        alamat_toko = request.form.get("alamat_toko", "").strip()

        try:
            tarif_pajak = float(request.form.get("tarif_pajak", ""))
            ambang = int(request.form.get("ambang_stok_menipis", ""))
        except (ValueError, TypeError):
            tarif_pajak = -1
            ambang = -1

        if not nama_toko:
            messages.append("Nama toko wajib diisi.")
        elif tarif_pajak < 0 or tarif_pajak > 100:
            messages.append("Tarif pajak harus antara 0 sampai 100.")
        elif ambang < 0:
            messages.append("Ambang stok tidak boleh negatif.")

        if messages:
            return render_template_string(
                TEMPLATE,
                pengaturan=pengaturan,
                messages=messages
            )

        pengaturan.nama_toko = nama_toko
        pengaturan.alamat_toko = alamat_toko or None
        pengaturan.tarif_pajak = tarif_pajak
        pengaturan.ambang_stok_menipis = ambang

        db.session.commit()

        return redirect(url_for("pengaturan.index", tersimpan=1))

    if request.args.get("tersimpan") == "1":
        messages.append("Pengaturan toko berhasil disimpan.")

    return render_template_string(
        TEMPLATE,
        pengaturan=pengaturan,
        messages=messages
    )
