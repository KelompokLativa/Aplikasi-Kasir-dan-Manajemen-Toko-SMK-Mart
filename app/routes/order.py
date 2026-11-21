
from flask import (
    Blueprint, jsonify, request, session,
    render_template_string, abort
)
from app.decorators import login_required, admin_required
from app.extensions import db
from app.models.order import Order
from app.models.mutasi_stok import MutasiStok
from app.models.user import User

order_bp = Blueprint("order", __name__)


TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Riwayat Order - SMK Mart</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            margin: 25px;
            color: #222;
        }
        .container {
            max-width: 1200px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
        }
        h1 { color: #1e3a5f; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 11px;
            border-bottom: 1px solid #ddd;
            text-align: left;
            font-size: 14px;
        }
        th { background: #1e3a5f; color: white; }
        .status {
            padding: 5px 8px;
            border-radius: 5px;
            background: #eee;
            display: inline-block;
        }
        button, .link {
            padding: 7px 10px;
            border: 0;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            background: #1e3a5f;
            color: white;
        }
        .detail {
            background: #f7f9fc;
            padding: 15px;
            margin: 8px 0;
            border-radius: 6px;
        }
        .kosong { padding: 25px; text-align: center; color: #777; }
        .uang { white-space: nowrap; }
    </style>
</head>
<body>
<div class="container">
    <h1>Riwayat Order</h1>
    <p>Daftar transaksi penjualan SMK Mart.</p>

    <a class="link" href="/dashboard">Kembali ke Dashboard</a>

    {% if orders %}
    <table>
        <thead>
            <tr>
                <th>No.</th>
                <th>Nomor Order</th>
                <th>Waktu</th>
                <th>Kasir</th>
                <th>Pelanggan</th>
                <th>Metode Bayar</th>
                <th>Total</th>
                <th>Status</th>
                <th>Detail</th>
            </tr>
        </thead>
        <tbody>
        {% for order in orders %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ order.nomor }}</td>
                <td>{{ order.waktu.strftime('%d-%m-%Y %H:%M') }}</td>
                <td>{{ order.kasir.nama if order.kasir else '-' }}</td>
                <td>{{ order.pelanggan.nama if order.pelanggan else '-' }}</td>
                <td>{{ order.metode_bayar.nama if order.metode_bayar else '-' }}</td>
                <td class="uang">Rp {{ "{:,.0f}".format(order.total).replace(",", ".") }}</td>
                <td><span class="status">{{ order.status }}</span></td>
                <td>
                    <button type="button"
                        onclick="document.getElementById('detail-{{ order.id }}').hidden = !document.getElementById('detail-{{ order.id }}').hidden">
                        Lihat
                    </button>
                </td>
            </tr>
            <tr>
                <td colspan="9">
                    <div class="detail" id="detail-{{ order.id }}" hidden>
                        <strong>Rincian Barang</strong>
                        <ul>
                        {% for item in order.items %}
                            <li>
                                {{ item.nama_produk }} —
                                {{ item.jumlah }} x
                                Rp {{ "{:,.0f}".format(item.harga_satuan).replace(",", ".") }}
                                = Rp {{ "{:,.0f}".format(item.subtotal).replace(",", ".") }}
                            </li>
                        {% endfor %}
                        </ul>
                        <p>Subtotal: Rp {{ "{:,.0f}".format(order.subtotal).replace(",", ".") }}</p>
                        <p>Pajak ({{ order.tarif_pajak }}%):
                           Rp {{ "{:,.0f}".format(order.pajak).replace(",", ".") }}</p>
                        <strong>Total: Rp {{ "{:,.0f}".format(order.total).replace(",", ".") }}</strong>

                        {% if order.status == 'selesai' %}
                            {% if is_admin %}
                            <p>Pengajuan pembatalan dilakukan oleh kasir.</p>
                            {% else %}
                            <form onsubmit="ajukanBatal(event, {{ order.id }})">
                                <label>Alasan pembatalan:</label><br>
                                <input name="alasan" required
                                    style="padding:8px;width:80%;margin:8px 0">
                                <button type="submit">Ajukan Pembatalan</button>
                            </form>
                            {% endif %}
                        {% elif order.status == 'pengajuan_batal' and is_admin %}
                            <p><strong>Perhatian:</strong> Periksa fisik barang sebelum menyetujui pembatalan.</p>
                            <label>
                                <input type="checkbox" id="cek-{{ order.id }}">
                                Saya sudah memeriksa fisik barang.
                            </label>
                            <br><br>
                            <button type="button" onclick="konfirmasiBatal({{ order.id }})">
                                Konfirmasi Pembatalan
                            </button>
                        {% endif %}
                    </div>
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% else %}
        <div class="kosong">Belum ada transaksi.</div>
    {% endif %}
</div>

<script>
async function ajukanBatal(event, id) {
    event.preventDefault();
    const form = event.target;
    const alasan = form.querySelector('[name="alasan"]').value;

    if (!confirm("Ajukan pembatalan transaksi ini?")) return;

    const response = await fetch(`/order/${id}/ajukan-batal`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({alasan})
    });

    const result = await response.json();
    alert(result.message);
    if (result.success) location.reload();
}

async function konfirmasiBatal(id) {
    const cek = document.getElementById(`cek-${id}`);

    if (!cek.checked) {
        alert("Centang konfirmasi pemeriksaan fisik barang terlebih dahulu.");
        return;
    }

    if (!confirm("Yakin mengonfirmasi pembatalan transaksi ini?")) return;

    const response = await fetch(`/order/${id}/konfirmasi-batal`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({cek_fisik: true})
    });

    const result = await response.json();
    alert(result.message);
    if (result.success) location.reload();
}
</script>
</body>
</html>
"""


@order_bp.route("/order")
@login_required
def index():
    user = db.session.get(User, session.get("user_id"))

    if user is None:
        abort(403)

    query = Order.query

    if user.peran != "admin":
        query = query.filter_by(kasir_id=user.id)

    orders = query.order_by(Order.waktu.desc()).all()

    return render_template_string(
        TEMPLATE,
        orders=orders,
        is_admin=(user.peran == "admin")
    )


@order_bp.route("/order/<int:id>/ajukan-batal", methods=["POST"])
@login_required
def ajukan_batal(id):
    order = db.session.get(Order, id)

    if order is None:
        return jsonify(success=False, message="Order tidak ditemukan."), 404

    user = db.session.get(User, session.get("user_id"))

    if user is None:
        return jsonify(success=False, message="Pengguna tidak ditemukan."), 403

    if user.peran != "admin" and order.kasir_id != user.id:
        return jsonify(success=False, message="Anda tidak memiliki akses ke order ini."), 403

    if order.status != "selesai":
        return jsonify(success=False, message="Order tidak dapat diajukan untuk pembatalan."), 400

    data = request.get_json(silent=True) or {}
    alasan = str(data.get("alasan", "")).strip()

    if not alasan:
        return jsonify(success=False, message="Alasan pembatalan harus diisi."), 400

    order.status = "pengajuan_batal"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(success=False, message="Pengajuan pembatalan gagal disimpan."), 500

    return jsonify(success=True, message="Pengajuan pembatalan berhasil."), 200


@order_bp.route("/order/<int:id>/konfirmasi-batal", methods=["POST"])
@admin_required
def konfirmasi_batal(id):
    order = db.session.get(Order, id)

    if order is None:
        return jsonify(success=False, message="Order tidak ditemukan."), 404

    if order.status != "pengajuan_batal":
        return jsonify(success=False, message="Order belum memiliki pengajuan pembatalan."), 400

    data = request.get_json(silent=True) or {}

    if data.get("cek_fisik") is not True:
        return jsonify(success=False, message="Pemeriksaan fisik barang harus dikonfirmasi."), 400

    try:
        for item in order.items:
            produk = item.produk

            if produk is None:
                raise ValueError("Produk transaksi tidak ditemukan.")

            stok_sebelum = produk.stok
            stok_sesudah = stok_sebelum + item.jumlah
            produk.stok = stok_sesudah

            db.session.add(
                MutasiStok(
                    produk_id=produk.id,
                    tipe="batal",
                    jumlah=item.jumlah,
                    stok_sebelum=stok_sebelum,
                    stok_sesudah=stok_sesudah,
                    keterangan=f"Pembatalan order {order.nomor}",
                )
            )

        order.status = "dibatalkan"
        db.session.commit()

    except Exception:
        db.session.rollback()
        return jsonify(success=False, message="Pembatalan transaksi gagal diproses."), 500

    return jsonify(success=True, message="Pembatalan transaksi berhasil dikonfirmasi."), 200
