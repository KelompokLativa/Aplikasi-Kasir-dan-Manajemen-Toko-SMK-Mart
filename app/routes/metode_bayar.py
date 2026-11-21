from flask import (
    Blueprint, request, redirect, url_for,
    render_template_string, flash
)
from app.decorators import admin_required
from app.extensions import db
from app.models.metode_bayar import MetodeBayar

metode_bayar_bp = Blueprint("metode_bayar", __name__)


TEMPLATE_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Metode Pembayaran</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 30px;
            background: #f4f6f9;
            color: #222;
        }
        .container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            max-width: 1000px;
            margin: auto;
        }
        h1 { color: #1e3a5f; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th { background: #1e3a5f; color: white; }
        a, button {
            padding: 8px 12px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            cursor: pointer;
        }
        .tambah { background: #198754; color: white; }
        .ubah { background: #ffc107; color: black; }
        .status { background: #0d6efd; color: white; border: none; }
        .pesan { padding: 10px; background: #e9f5e9; margin: 10px 0; }
        form { display: inline; }
    </style>
</head>
<body>
<div class="container">
    <h1>Metode Pembayaran</h1>

    {% for pesan in messages %}
        <div class="pesan">{{ pesan }}</div>
    {% endfor %}

    <p>
        <a class="tambah" href="{{ url_for('metode_bayar.tambah') }}">
            + Tambah Metode Pembayaran
        </a>
    </p>

    <table>
        <thead>
            <tr>
                <th>No</th>
                <th>Nama Metode</th>
                <th>Jenis</th>
                <th>Status</th>
                <th>Aksi</th>
            </tr>
        </thead>
        <tbody>
        {% for m in daftar %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ m.nama }}</td>
                <td>{{ m.jenis }}</td>
                <td>{{ "Aktif" if m.aktif else "Nonaktif" }}</td>
                <td>
                    <a class="ubah"
                       href="{{ url_for('metode_bayar.ubah', id=m.id) }}">
                       Ubah
                    </a>

                    <form method="post"
                          action="{{ url_for('metode_bayar.status', id=m.id) }}">
                        <input type="hidden" name="csrf_token"
                               value="{{ csrf_token() }}">
                        <button class="status" type="submit">
                            {{ "Nonaktifkan" if m.aktif else "Aktifkan" }}
                        </button>
                    </form>
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="5">Belum ada metode pembayaran.</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <p><a href="/dashboard">Kembali ke Dashboard</a></p>
</div>
</body>
</html>
"""


TEMPLATE_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ judul }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            margin: 30px;
        }
        .container {
            max-width: 500px;
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin: auto;
        }
        input, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0 15px;
            box-sizing: border-box;
        }
        button {
            padding: 10px 15px;
            background: #198754;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        .pesan { color: #b00020; }
    </style>
</head>
<body>
<div class="container">
    <h1>{{ judul }}</h1>

    {% for pesan in messages %}
        <p class="pesan">{{ pesan }}</p>
    {% endfor %}

    <form method="post">
        <input type="hidden" name="csrf_token"
               value="{{ csrf_token() }}">

        <label>Nama Metode Pembayaran</label>
        <input name="nama" required maxlength="50"
               value="{{ metode.nama if metode else '' }}"
               placeholder="Contoh: Tunai">

        <label>Jenis</label>
        <select name="jenis" required>
            {% for pilihan in jenis_list %}
                <option value="{{ pilihan }}"
                    {% if metode and metode.jenis == pilihan %}
                        selected
                    {% endif %}>
                    {{ pilihan }}
                </option>
            {% endfor %}
        </select>

        {% if metode %}
        <label>Status</label>
        <select name="aktif">
            <option value="1" {% if metode.aktif %}selected{% endif %}>
                Aktif
            </option>
            <option value="0" {% if not metode.aktif %}selected{% endif %}>
                Nonaktif
            </option>
        </select>
        {% endif %}

        <button type="submit">Simpan</button>
    </form>

    <p><a href="{{ url_for('metode_bayar.index') }}">Kembali</a></p>
</div>
</body>
</html>
"""


JENIS_LIST = ["Tunai", "Transfer", "QRIS", "Debit", "Kredit", "Lainnya"]


@metode_bayar_bp.route("/metode-bayar")
@admin_required
def index():
    daftar = MetodeBayar.query.order_by(MetodeBayar.nama.asc()).all()

    messages = []
    return render_template_string(
        TEMPLATE_INDEX, daftar=daftar, messages=messages
    )


@metode_bayar_bp.route("/metode-bayar/tambah", methods=["GET", "POST"])
@admin_required
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        jenis = request.form.get("jenis", "").strip()

        if not nama:
            return render_template_string(
                TEMPLATE_FORM,
                judul="Tambah Metode Pembayaran",
                metode=None,
                jenis_list=JENIS_LIST,
                messages=["Nama metode pembayaran wajib diisi."]
            )

        if jenis not in JENIS_LIST:
            return render_template_string(
                TEMPLATE_FORM,
                judul="Tambah Metode Pembayaran",
                metode=None,
                jenis_list=JENIS_LIST,
                messages=["Jenis metode pembayaran tidak valid."]
            )

        if MetodeBayar.query.filter_by(nama=nama).first():
            return render_template_string(
                TEMPLATE_FORM,
                judul="Tambah Metode Pembayaran",
                metode=None,
                jenis_list=JENIS_LIST,
                messages=["Nama metode pembayaran sudah ada."]
            )

        metode = MetodeBayar(
            nama=nama,
            jenis=jenis,
            aktif=True
        )
        db.session.add(metode)
        db.session.commit()

        return redirect(url_for("metode_bayar.index"))

    return render_template_string(
        TEMPLATE_FORM,
        judul="Tambah Metode Pembayaran",
        metode=None,
        jenis_list=JENIS_LIST,
        messages=[]
    )


@metode_bayar_bp.route("/metode-bayar/ubah/<int:id>", methods=["GET", "POST"])
@admin_required
def ubah(id):
    metode = db.session.get(MetodeBayar, id)

    if metode is None:
        return "Metode pembayaran tidak ditemukan.", 404

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        jenis = request.form.get("jenis", "").strip()
        aktif = request.form.get("aktif", "1") == "1"

        duplicate = MetodeBayar.query.filter(
            MetodeBayar.nama == nama,
            MetodeBayar.id != id
        ).first()

        if not nama:
            pesan = ["Nama metode pembayaran wajib diisi."]
        elif duplicate:
            pesan = ["Nama metode pembayaran sudah digunakan."]
        elif jenis not in JENIS_LIST:
            pesan = ["Jenis metode pembayaran tidak valid."]
        else:
            metode.nama = nama
            metode.jenis = jenis
            metode.aktif = aktif
            db.session.commit()
            return redirect(url_for("metode_bayar.index"))

        return render_template_string(
            TEMPLATE_FORM,
            judul="Ubah Metode Pembayaran",
            metode=metode,
            jenis_list=JENIS_LIST,
            messages=pesan
        )

    return render_template_string(
        TEMPLATE_FORM,
        judul="Ubah Metode Pembayaran",
        metode=metode,
        jenis_list=JENIS_LIST,
        messages=[]
    )


@metode_bayar_bp.route("/metode-bayar/status/<int:id>", methods=["POST"])
@admin_required
def status(id):
    metode = db.session.get(MetodeBayar, id)

    if metode is None:
        return "Metode pembayaran tidak ditemukan.", 404

    metode.aktif = not metode.aktif
    db.session.commit()

    return redirect(url_for("metode_bayar.index"))