
import os
from types import SimpleNamespace

from flask import Flask, session
from app.extensions import db, csrf


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name == "testing":
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["WTF_CSRF_ENABLED"] = False
    else:
        app.config["SECRET_KEY"] = os.environ.get(
            "SECRET_KEY", "dev-secret-key"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "sqlite:///smk_mart.db"
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    csrf.init_app(app)

    # Memuat model
    from app import models
    from app.models.user import User

    # Memuat perintah seed
    from app.commands.seed import register_commands

    # Memuat seluruh routes
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.pos import pos_bp
    from app.routes.order import order_bp
    from app.routes.pengguna import pengguna_bp
    from app.routes.produk import produk_bp
    from app.routes.pelanggan import pelanggan_bp
    from app.routes.laporan import laporan_bp
    from app.routes.metode_bayar import metode_bayar_bp
    from app.routes.pengaturan import pengaturan_bp

    # Mendaftarkan seluruh blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(pengguna_bp)
    app.register_blueprint(produk_bp)
    app.register_blueprint(pelanggan_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(metode_bayar_bp)
    app.register_blueprint(pengaturan_bp)

    # Data pengguna untuk template
    @app.context_processor
    def inject_user():
        user_id = session.get("user_id")
        user = User.query.get(user_id) if user_id else None

        if user and user.aktif:
            current_user = user
            current_user.is_authenticated = True
        else:
            current_user = SimpleNamespace(
                is_authenticated=False,
                is_admin=False,
                is_kasir=False,
                nama="",
                peran="",
            )

        return {"current_user": current_user}

    # Filter rupiah
    @app.template_filter("rupiah")
    def rupiah(value):
        try:
            value = float(value or 0)
            return "Rp {:,.0f}".format(value).replace(",", ".")
        except (ValueError, TypeError):
            return "Rp 0"

    # Filter waktu
    @app.template_filter("waktu_wib")
    def waktu_wib(value):
        if not value:
            return "-"
        return value.strftime("%d-%m-%Y %H:%M")

    # Error 403
    @app.errorhandler(403)
    def forbidden(error):
        return "Anda tidak punya akses ke halaman ini.", 403

    # Error 404
    @app.errorhandler(404)
    def not_found(error):
        return "Halaman tidak ditemukan.", 404

    # Error 500
    @app.errorhandler(500)
    def internal_error(error):
        return "Terjadi kesalahan pada server.", 500

    # Seed database
    register_commands(app)

    return app