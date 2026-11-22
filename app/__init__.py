
import os
from datetime import datetime, timedelta, timezone

from flask import Flask

from app.extensions import db, login_manager, csrf
from config import config


def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=True)

    # Memuat konfigurasi aplikasi
    app.config.from_object(
        config.get(config_name, config["development"])
    )

    # Membuat folder instance jika belum tersedia
    os.makedirs(app.instance_path, exist_ok=True)

    # Inisialisasi ekstensi
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Pengaturan login
    login_manager.login_view = "auth.login"

    # Zona waktu WIB (UTC+7)
    WIB = timezone(timedelta(hours=7))

    # Filter format Rupiah
    @app.template_filter("rupiah")
    def format_rupiah(nilai):
        try:
            nilai = float(nilai or 0)
        except (TypeError, ValueError):
            nilai = 0

        return "Rp {:,.0f}".format(nilai).replace(",", ".")

    # Filter format tanggal dan waktu WIB
    @app.template_filter("waktu_wib")
    def format_waktu_wib(nilai):
        if nilai is None:
            return "-"

        if isinstance(nilai, str):
            try:
                nilai = datetime.fromisoformat(nilai)
            except ValueError:
                return nilai

        if not isinstance(nilai, datetime):
            return str(nilai)

        # Waktu tanpa zona dianggap sudah menggunakan waktu WIB
        if nilai.tzinfo is None:
            nilai = nilai.replace(tzinfo=WIB)
        else:
            nilai = nilai.astimezone(WIB)

        return nilai.strftime("%d/%m/%Y %H:%M") + " WIB"

    # Memuat model User
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Memuat Blueprint
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.laporan import laporan_bp
    from app.blueprints.metode_bayar import metode_bayar_bp
    from app.blueprints.order import order_bp
    from app.blueprints.pelanggan import pelanggan_bp
    from app.blueprints.pengaturan import pengaturan_bp
    from app.blueprints.pengguna import pengguna_bp
    from app.blueprints.pos import pos_bp
    from app.blueprints.produk import produk_bp

    # Mendaftarkan Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(metode_bayar_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(pelanggan_bp)
    app.register_blueprint(pengaturan_bp)
    app.register_blueprint(pengguna_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(produk_bp)

    # Membuat tabel yang belum tersedia
    # Tidak menghapus data yang sudah ada
    with app.app_context():
        db.create_all()

    return app
