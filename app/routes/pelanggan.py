from flask import (
    Blueprint, request, redirect, url_for, flash,
    render_template_string
)
from app.decorators import login_required
from app.extensions import db
from app.models.pelanggan import Pelanggan

pelanggan_bp = Blueprint("pelanggan", __name__)

HTML = """
<html><body>
<h1>Daftar Pelanggan</h1>
{% for m in messages %}<p>{{ m }}</p>{% endfor %}
<form method="get">
    <input name="q" value="{{ q }}" placeholder="Cari pelanggan">
    <button>Cari</button>
</form>
<table border="1">
<tr><th>Nama</th><th>Telepon</th></tr>
{% for p in data %}
<tr><td>{{ p.nama }}</td><td>{{ p.telepon or '' }}</td></tr>
{% endfor %}
</table>
<a href="/pelanggan/tambah">Tambah Pelanggan</a>
</body></html>
"""

FORM = """
<html><body>
<h1>Form Pelanggan</h1>
{% for m in messages %}<p>{{ m }}</p>{% endfor %}
<form method="post">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<input name="nama" placeholder="Nama" value="{{ nama or '' }}">
<input name="telepon" placeholder="Telepon" value="{{ telepon or '' }}">
<input name="alamat" placeholder="Alamat" value="{{ alamat or '' }}">
<button>Simpan</button>
</form>
<a href="/pelanggan">Kembali</a>
</body></html>
"""


@pelanggan_bp.route("/pelanggan")
@pelanggan_bp.route("/pelanggan/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Pelanggan.query

    if q:
        query = query.filter(Pelanggan.nama.ilike(f"%{q}%"))

    data = query.order_by(Pelanggan.nama).all()

    return render_template_string(
        HTML, data=data, q=q, messages=[]
    )


@pelanggan_bp.route("/pelanggan/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        telepon = request.form.get("telepon", "").strip()
        alamat = request.form.get("alamat", "").strip()

        if not nama:
            flash("Nama pelanggan wajib diisi.")
        elif telepon and not all(
            c.isdigit() or c == "+" for c in telepon
        ):
            flash("Nomor telepon hanya boleh angka dan tanda +.")
        else:
            p = Pelanggan(
                nama=nama,
                telepon=telepon or None
            )

            if hasattr(p, "alamat"):
                p.alamat = alamat

            db.session.add(p)
            db.session.commit()

            flash(f"Pelanggan {nama} tersimpan.")
            return redirect(url_for("pelanggan.index"))

        return render_template_string(
            FORM,
            messages=[],
            nama=nama,
            telepon=telepon,
            alamat=alamat
        )

    return render_template_string(
        FORM,
        messages=[],
        nama="",
        telepon="",
        alamat=""
    )


@pelanggan_bp.route(
    "/pelanggan/<int:id>/ubah", methods=["GET", "POST"]
)
@pelanggan_bp.route(
    "/pelanggan/ubah/<int:id>", methods=["GET", "POST"]
)
@login_required
def ubah(id):
    p = db.session.get(Pelanggan, id)

    if p is None:
        return "Pelanggan tidak ditemukan.", 404

    if p.bawaan:
        flash("Pelanggan Umum tidak bisa diubah atau dihapus.")
        return redirect(url_for("pelanggan.index"))

    if request.method == "POST":
        nama = request.form.get("nama", p.nama).strip()
        telepon = request.form.get("telepon", "").strip()
        alamat = request.form.get("alamat", "").strip()

        if not nama:
            flash("Nama pelanggan wajib diisi.")
        elif telepon and not all(
            c.isdigit() or c == "+" for c in telepon
        ):
            flash("Nomor telepon hanya boleh angka dan tanda +.")
        else:
            p.nama = nama
            p.telepon = telepon or None

            if hasattr(p, "alamat"):
                p.alamat = alamat

            db.session.commit()
            flash(f"Pelanggan {nama} tersimpan.")
            return redirect(url_for("pelanggan.index"))

        return render_template_string(
            FORM,
            messages=[],
            nama=nama,
            telepon=telepon,
            alamat=alamat
        )

    return render_template_string(
        FORM,
        messages=[],
        nama=p.nama,
        telepon=p.telepon or "",
        alamat=getattr(p, "alamat", "") or ""
    )


@pelanggan_bp.route(
    "/pelanggan/<int:id>/hapus", methods=["POST"]
)
@login_required
def hapus(id):
    p = db.session.get(Pelanggan, id)

    if p is None:
        return "Pelanggan tidak ditemukan.", 404

    if p.bawaan:
        flash("Pelanggan Umum tidak bisa diubah atau dihapus.")
        return redirect(url_for("pelanggan.index"))

    if p.orders:
        flash(
            f"Pelanggan {p.nama} tidak bisa dihapus "
            "karena sudah punya order."
        )
        return redirect(url_for("pelanggan.index"))

    if not session_admin():
        return "Anda tidak memiliki akses.", 403

    nama = p.nama
    db.session.delete(p)
    db.session.commit()

    flash(f"Pelanggan {nama} dihapus.")
    return redirect(url_for("pelanggan.index"))


def session_admin():
    from flask import session
    from app.models.user import User

    user = db.session.get(User, session.get("user_id"))
    return bool(user and user.is_admin)