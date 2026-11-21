
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import (
    Blueprint,
    render_template,
    render_template_string,
    jsonify,
    request,
    session,
    url_for,
)

from app.decorators import login_required
from app.extensions import db
from app.models.user import User
from app.models.produk import Produk
from app.models.pelanggan import Pelanggan
from app.models.metode_bayar import MetodeBayar
from app.models.pengaturan import Pengaturan
from app.models.order import Order, OrderItem
from app.models.mutasi_stok import MutasiStok


pos_bp = Blueprint("pos", __name__)


def hitung_pajak_dan_total(subtotal, tarif_pajak):
    subtotal = int(subtotal)
    tarif = Decimal(str(tarif_pajak or 0))

    pajak = (
        Decimal(subtotal) * tarif / Decimal("100")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    pajak = int(pajak)
    total = subtotal + pajak

    return pajak, total


@pos_bp.route("/pos")
@login_required
def index():
    current_user = db.session.get(User, session.get("user_id"))

    if current_user is None:
        return "Pengguna tidak ditemukan.", 403

    produk_list = Produk.query.filter_by(aktif=True).all()
    pelanggan_list = Pelanggan.query.filter_by(aktif=True).all()
    metode_list = MetodeBayar.query.filter_by(aktif=True).all()

    pengaturan = Pengaturan.query.first()

    if pengaturan is None:
        pengaturan = Pengaturan()
        db.session.add(pengaturan)
        db.session.commit()

    kategori_list = sorted(
        set(
            produk.kategori
            for produk in produk_list
            if produk.kategori
        )
    )

    return render_template(
        "pos/index.html",
        current_user=current_user,
        produk_list=produk_list,
        kategori_list=kategori_list,
        pelanggan_list=pelanggan_list,
        metode_list=metode_list,
        pengaturan=pengaturan,
    )


@pos_bp.route("/pos/checkout", methods=["POST"])
@login_required
def checkout():
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])

    if not isinstance(items, list) or not items:
        return jsonify(
            success=False,
            message="Keranjang masih kosong."
        ), 400

    jumlah_produk = {}

    for item in items:
        if not isinstance(item, dict):
            return jsonify(
                success=False,
                message="Data produk tidak valid."
            ), 400

        produk_id = item.get("produk_id")
        jumlah = item.get("jumlah")

        if (
            isinstance(jumlah, bool)
            or not isinstance(jumlah, int)
            or jumlah <= 0
        ):
            return jsonify(
                success=False,
                message="Jumlah produk tidak valid."
            ), 400

        try:
            produk_id = int(produk_id)
        except (TypeError, ValueError):
            return jsonify(
                success=False,
                message="Produk tidak valid."
            ), 400

        jumlah_produk[produk_id] = (
            jumlah_produk.get(produk_id, 0) + jumlah
        )

    produk_data = []
    subtotal = 0

    for produk_id, jumlah in jumlah_produk.items():
        produk = db.session.get(Produk, produk_id)

        if produk is None or not produk.aktif:
            return jsonify(
                success=False,
                message="Produk tidak ditemukan atau tidak aktif."
            ), 400

        if produk.stok <= 0:
            return jsonify(
                success=False,
                message=f"Stok {produk.nama} habis."
            ), 400

        if jumlah > produk.stok:
            return jsonify(
                success=False,
                message=f"Stok {produk.nama} hanya {produk.stok}."
            ), 400

        subtotal_item = produk.harga * jumlah
        subtotal += subtotal_item

        produk_data.append(
            (produk, jumlah, subtotal_item)
        )

    pengaturan = Pengaturan.query.first()

    tarif_pajak = (
        pengaturan.tarif_pajak
        if pengaturan
        else 0
    )

    pajak, total = hitung_pajak_dan_total(
        subtotal,
        tarif_pajak,
    )

    metode_id = data.get("metode_bayar_id")

    try:
        metode_id = int(metode_id)
    except (TypeError, ValueError):
        metode_id = None

    metode = (
        db.session.get(MetodeBayar, metode_id)
        if metode_id
        else None
    )

    if metode is None or not metode.aktif:
        return jsonify(
            success=False,
            message="Metode pembayaran tidak valid."
        ), 400

    pelanggan_id = data.get("pelanggan_id")

    try:
        pelanggan_id = int(pelanggan_id) if pelanggan_id else None
    except (TypeError, ValueError):
        pelanggan_id = None

    pelanggan = (
        db.session.get(Pelanggan, pelanggan_id)
        if pelanggan_id
        else None
    )

    if pelanggan_id and (
        pelanggan is None or not pelanggan.aktif
    ):
        return jsonify(
            success=False,
            message="Pelanggan tidak valid."
        ), 400

    if pelanggan is None:
        pelanggan = Pelanggan.query.filter_by(
            bawaan=True,
            aktif=True,
        ).first()

        if pelanggan is None:
            pelanggan = Pelanggan.query.filter_by(
                nama="Umum",
                aktif=True,
            ).first()

        if pelanggan is None:
            return jsonify(
                success=False,
                message="Pelanggan Umum belum tersedia."
            ), 400

    uang_diterima = data.get("uang_diterima")
    kembalian = None

    if metode.jenis == "tunai":
        try:
            uang_diterima = int(uang_diterima)
        except (TypeError, ValueError):
            uang_diterima = 0

        if uang_diterima < total:
            selisih = total - uang_diterima

            return jsonify(
                success=False,
                message=(
                    "Uang diterima kurang Rp "
                    f"{selisih:,}".replace(",", ".")
                )
            ), 400

        kembalian = uang_diterima - total

    else:
        uang_diterima = None
        kembalian = None

    kasir = db.session.get(
        User,
        session.get("user_id")
    )

    if kasir is None or not kasir.aktif:
        return jsonify(
            success=False,
            message="Kasir tidak ditemukan atau tidak aktif."
        ), 403

    waktu = datetime.now()
    tanggal = waktu.strftime("%Y%m%d")
    prefix = f"POS-{tanggal}-"

    nomor_terakhir = (
        Order.query.filter(
            Order.nomor.like(prefix + "%")
        ).count()
    )

    nomor = f"{prefix}{nomor_terakhir + 1:04d}"

    order = Order(
        nomor=nomor,
        waktu=waktu,
        kasir_id=kasir.id,
        pelanggan_id=pelanggan.id,
        metode_bayar_id=metode.id,
        subtotal=subtotal,
        tarif_pajak=tarif_pajak,
        pajak=pajak,
        total=total,
        uang_diterima=uang_diterima,
        kembalian=kembalian,
        status="selesai",
    )

    try:
        db.session.add(order)
        db.session.flush()

        for produk, jumlah, subtotal_item in produk_data:
            stok_sebelum = produk.stok
            stok_sesudah = stok_sebelum - jumlah

            produk.stok = stok_sesudah

            item_order = OrderItem(
                order_id=order.id,
                produk_id=produk.id,
                nama_produk=produk.nama,
                harga_satuan=produk.harga,
                jumlah=jumlah,
                subtotal=subtotal_item,
            )

            mutasi = MutasiStok(
                produk_id=produk.id,
                tipe="keluar",
                jumlah=jumlah,
                stok_sebelum=stok_sebelum,
                stok_sesudah=stok_sesudah,
                keterangan=f"Penjualan {nomor}",
            )

            db.session.add(item_order)
            db.session.add(mutasi)

        db.session.commit()

        redirect_url = url_for(
            "pos.struk",
            id=order.id
        )

        return jsonify(
            success=True,
            message="Transaksi berhasil.",
            order_id=order.id,
            nomor=order.nomor,
            subtotal=order.subtotal,
            pajak=order.pajak,
            total=order.total,
            kembalian=order.kembalian,
            redirect_url=redirect_url,
        ), 201

    except Exception:
        db.session.rollback()

        return jsonify(
            success=False,
            message="Transaksi gagal disimpan."
        ), 500


@pos_bp.route(
    "/pos/pelanggan-cepat",
    methods=["POST"]
)
@pos_bp.route(
    "/pos/tambah-pelanggan-cepat",
    methods=["POST"]
)
@login_required
def tambah_pelanggan_cepat():
    data = request.get_json(silent=True) or {}

    nama = str(data.get("nama", "")).strip()
    telepon = str(data.get("telepon", "")).strip() or None

    if not nama:
        return jsonify(
            success=False,
            message="Nama pelanggan harus diisi."
        ), 400

    pelanggan = Pelanggan(
        nama=nama,
        telepon=telepon,
        bawaan=False,
    )

    db.session.add(pelanggan)

    try:
        db.session.commit()

        return jsonify(
            success=True,
            message="Pelanggan berhasil ditambahkan.",
            id=pelanggan.id,
            nama=pelanggan.nama,
            telepon=pelanggan.telepon,
        ), 201

    except Exception:
        db.session.rollback()

        return jsonify(
            success=False,
            message="Pelanggan gagal disimpan."
        ), 500


@pos_bp.route("/pos/struk/<int:id>")
@login_required
def struk(id):
    order = db.session.get(Order, id)

    if order is None:
        return "Order tidak ditemukan.", 404

    user = db.session.get(User, session.get("user_id"))

    if user is None:
        return "Anda tidak punya akses ke halaman ini.", 403

    if user.peran != "admin" and order.kasir_id != user.id:
        return "Anda tidak punya akses ke halaman ini.", 403

    pengaturan = Pengaturan.query.first()

    nama_toko = (
        pengaturan.nama_toko
        if pengaturan
        else "SMK Mart"
    )

    alamat_toko = (
        pengaturan.alamat_toko
        if pengaturan
        else None
    )

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Struk {{ order.nomor }}</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 380px;
                margin: 30px auto;
                padding: 15px;
                color: #222;
            }
            h2, h3, p { text-align: center; }
            .garis {
                border-top: 1px dashed #555;
                margin: 12px 0;
            }
            .baris {
                display: flex;
                justify-content: space-between;
                margin: 7px 0;
                font-size: 14px;
            }
            .produk { margin: 8px 0; font-size: 14px; }
            .tombol {
                display: block;
                width: 100%;
                padding: 12px;
                margin-top: 15px;
                background: #1e3a5f;
                color: white;
                border: 0;
                border-radius: 6px;
                cursor: pointer;
            }
            @media print {
                .tombol { display: none; }
            }
        </style>
    </head>
    <body>
        <h2>{{ nama_toko }}</h2>
        {% if alamat_toko %}
        <p>{{ alamat_toko }}</p>
        {% endif %}
        <h3>STRUK TRANSAKSI</h3>

        <div class="garis"></div>

        <p>{{ order.nomor }}</p>
        <p>{{ order.waktu.strftime('%d-%m-%Y %H:%M') }}</p>
        <p>Kasir: {{ order.kasir.nama }}</p>
        <p>Pelanggan: {{ order.pelanggan.nama }}</p>

        <div class="garis"></div>

        {% for item in order.items %}
        <div class="produk">
            <strong>{{ item.nama_produk }}</strong><br>
            {{ item.jumlah }} x
            {{ '{:,.0f}'.format(item.harga_satuan).replace(',', '.') }}
            <span style="float:right">
                {{ '{:,.0f}'.format(item.subtotal).replace(',', '.') }}
            </span>
        </div>
        {% endfor %}

        <div class="garis"></div>

        <div class="baris">
            <span>Subtotal</span>
            <span>{{ '{:,.0f}'.format(order.subtotal).replace(',', '.') }}</span>
        </div>

        <div class="baris">
            <span>Pajak ({{ order.tarif_pajak }}%)</span>
            <span>{{ '{:,.0f}'.format(order.pajak).replace(',', '.') }}</span>
        </div>

        <div class="baris">
            <strong>TOTAL</strong>
            <strong>{{ '{:,.0f}'.format(order.total).replace(',', '.') }}</strong>
        </div>

        <div class="baris">
            <span>Metode pembayaran</span>
            <span>{{ order.metode_bayar.nama }}</span>
        </div>

        {% if order.uang_diterima is not none %}
        <div class="baris">
            <span>Uang diterima</span>
            <span>{{ '{:,.0f}'.format(order.uang_diterima).replace(',', '.') }}</span>
        </div>
        <div class="baris">
            <span>Kembalian</span>
            <span>{{ '{:,.0f}'.format(order.kembalian).replace(',', '.') }}</span>
        </div>
        {% endif %}

        <div class="garis"></div>
        <p>Terima kasih telah berbelanja.</p>

        <button class="tombol" onclick="window.print()">
            Cetak Struk
        </button>

        <button class="tombol" onclick="location.href='/order'">
            Lihat Riwayat Order
        </button>
    </body>
    </html>
    """

    return render_template_string(
        html,
        order=order,
        nama_toko=nama_toko,
        alamat_toko=alamat_toko,
    )
