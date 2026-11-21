
from flask import (
    Blueprint, request, redirect, url_for,
    render_template_string, session
)
from app.decorators import admin_required
from app.extensions import db
from app.models.user import User

pengguna_bp = Blueprint("pengguna", __name__)

JENIS_PERAN = ["admin", "kasir"]

TEMPLATE_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Manajemen Pengguna</title>
    <style>
        body { font-family: Arial; background: #f4f6f9; margin: 30px; }
        .container { background: white; padding: 25px; border-radius: 10px; }
        h1 { color: #1e3a5f; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background: #1e3a5f; color: white; }
        a, button {
            padding: 8px 12px; border: 0; border-radius: 5px;
            text-decoration: none; cursor: pointer;
        }
        .tambah { background: #198754; color: white; }
        .ubah { background: #ffc107; color: black; }
        .status { background: #0d6efd; color: white; }
        .pesan { padding: 10px; background: #e9f5e9; margin: 10px 0; }
        form { display: inline; }
    </style>
</head>
<body>
<div class="container">
    <h1>Manajemen Pengguna</h1>

    {% for pesan in messages %}
        <div class="pesan">{{ pesan }}</div>
    {% endfor %}

    <p>
        <a class="tambah" href="{{ url_for('pengguna.tambah') }}">
            + Tambah Pengguna
        </a>
    </p>

    <table>
        <thead>
            <tr>
                <th>No</th>
                <th>Nama</th>
                <th>Username</th>
                <th>Peran</th>
                <th>Status</th>
                <th>Aksi</th>
            </tr>
        </thead>
        <tbody>
        {% for user in daftar %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ user.nama }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.peran }}</td>
                <td>{{ "Aktif" if user.aktif else "Nonaktif" }}</td>
                <td>
                    <a class="ubah"
                       href="{{ url_for('pengguna.ubah', id=user.id) }}">
                       Ubah
                    </a>

                    {% if user.id != current_id %}
                    <form method="post"
                          action="{{ url_for('pengguna.hapus', id=user.id) }}">
                        <input type="hidden" name="csrf_token"
                               value="{{ csrf_token() }}">
                        <button class="status" type="submit">
                            {{ "Nonaktifkan" if user.aktif else "Aktifkan" }}
                        </button>
                    </form>
                    {% else %}
                        <small>Akun Anda</small>
                    {% endif %}
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="6">Belum ada pengguna.</td>
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
        body { font-family: Arial; background: #f4f6f9; margin: 30px; }
        .container {
            max-width: 500px; background: white; padding: 25px;
            border-radius: 10px; margin: auto;
        }
        input, select {
            width: 100%; padding: 10px; margin: 8px 0 15px;
            box-sizing: border-box;
        }
        button {
            padding: 10px 15px; background: #198754;
            color: white; border: 0; border-radius: 5px;
            cursor: pointer;
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

        <label>Nama Lengkap</label>
        <input name="nama" required maxlength="100"
               value="{{ user.nama if user else '' }}">

        <label>Username</label>
        <input name="username" required maxlength="50"
               value="{{ user.username if user else '' }}">

        <label>Password {% if user %}(kosongkan jika tidak diubah){% endif %}</label>
        <input type="password" name="password"
               {% if not user %}required{% endif %}>

        <label>Peran</label>
        <select name="peran" required>
            {% for peran in jenis_peran %}
                <option value="{{ peran }}"
                    {% if user and user.peran == peran %}
                        selected
                    {% endif %}>
                    {{ peran|capitalize }}
                </option>
            {% endfor %}
        </select>

        {% if user %}
        <label>Status Akun</label>
        <select name="aktif">
            <option value="1" {% if user.aktif %}selected{% endif %}>
                Aktif
            </option>
            <option value="0" {% if not user.aktif %}selected{% endif %}>
                Nonaktif
            </option>
        </select>
        {% endif %}

        <button type="submit">Simpan</button>
    </form>

    <p><a href="{{ url_for('pengguna.index') }}">Kembali</a></p>
</div>
</body>
</html>
"""


def jumlah_admin_aktif():
    return User.query.filter_by(peran="admin", aktif=True).count()


@pengguna_bp.route("/pengguna")
@admin_required
def index():
    daftar = User.query.order_by(User.nama.asc()).all()

    return render_template_string(
        TEMPLATE_INDEX,
        daftar=daftar,
        messages=[],
        current_id=session.get("user_id")
    )


@pengguna_bp.route("/pengguna/tambah", methods=["GET", "POST"])
@admin_required
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        peran = request.form.get("peran", "").strip()

        pesan = []

        if not nama or not username or not password:
            pesan.append("Semua data wajib diisi.")
        elif len(password) < 6:
            pesan.append("Password minimal 6 karakter.")
        elif peran not in JENIS_PERAN:
            pesan.append("Peran pengguna tidak valid.")
        elif User.query.filter_by(username=username).first():
            pesan.append("Username sudah digunakan.")

        if pesan:
            return render_template_string(
                TEMPLATE_FORM,
                judul="Tambah Pengguna",
                user=None,
                jenis_peran=JENIS_PERAN,
                messages=pesan
            )

        user = User(
            nama=nama,
            username=username,
            peran=peran,
            aktif=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("pengguna.index"))

    return render_template_string(
        TEMPLATE_FORM,
        judul="Tambah Pengguna",
        user=None,
        jenis_peran=JENIS_PERAN,
        messages=[]
    )


@pengguna_bp.route("/pengguna/ubah/<int:id>", methods=["GET", "POST"])
@admin_required
def ubah(id):
    user = db.session.get(User, id)

    if user is None:
        return "Pengguna tidak ditemukan.", 404

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        peran = request.form.get("peran", "").strip()
        aktif = request.form.get("aktif", "1") == "1"

        pesan = []

        duplicate = User.query.filter(
            User.username == username,
            User.id != id
        ).first()

        if not nama or not username:
            pesan.append("Nama dan username wajib diisi.")
        elif duplicate:
            pesan.append("Username sudah digunakan.")
        elif peran not in JENIS_PERAN:
            pesan.append("Peran pengguna tidak valid.")
        elif password and len(password) < 6:
            pesan.append("Password minimal 6 karakter.")

        if id == session.get("user_id"):
            if peran != "admin" or not aktif:
                pesan.append("Anda tidak boleh menonaktifkan atau mengubah peran akun sendiri.")

        if user.peran == "admin" and user.aktif:
            if (peran != "admin" or not aktif) and jumlah_admin_aktif() <= 1:
                pesan.append("Tidak boleh menonaktifkan admin aktif terakhir.")

        if pesan:
            return render_template_string(
                TEMPLATE_FORM,
                judul="Ubah Pengguna",
                user=user,
                jenis_peran=JENIS_PERAN,
                messages=pesan
            )

        user.nama = nama
        user.username = username
        user.peran = peran
        user.aktif = aktif

        if password:
            user.set_password(password)

        db.session.commit()
        return redirect(url_for("pengguna.index"))

    return render_template_string(
        TEMPLATE_FORM,
        judul="Ubah Pengguna",
        user=user,
        jenis_peran=JENIS_PERAN,
        messages=[]
    )


@pengguna_bp.route("/pengguna/hapus/<int:id>", methods=["POST"])
@admin_required
def hapus(id):
    user = db.session.get(User, id)

    if user is None:
        return "Pengguna tidak ditemukan.", 404

    if user.id == session.get("user_id"):
        return "Anda tidak dapat menonaktifkan akun sendiri.", 400

    if user.peran == "admin" and user.aktif and jumlah_admin_aktif() <= 1:
        return "Admin aktif terakhir tidak boleh dinonaktifkan.", 400

    user.aktif = not user.aktif
    db.session.commit()

    return redirect(url_for("pengguna.index"))
