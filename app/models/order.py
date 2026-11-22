from datetime import datetime

from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(50), nullable=False, unique=True)
    waktu = db.Column(db.DateTime, nullable=False, default=datetime.now)

    kasir_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    pelanggan_id = db.Column(db.Integer, db.ForeignKey("pelanggan.id"), nullable=True)
    metode_bayar_id = db.Column(db.Integer, db.ForeignKey("metode_bayar.id"), nullable=True)

    subtotal = db.Column(db.Integer, nullable=False, default=0)
    tarif_pajak = db.Column(db.Float, nullable=False, default=0)
    pajak = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    uang_diterima = db.Column(db.Integer, nullable=False, default=0)
    kembalian = db.Column(db.Integer, nullable=False, default=0)

    status = db.Column(db.String(30), nullable=False, default="selesai")
    alasan_batal = db.Column(db.Text, nullable=True)

    diajukan_oleh_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    dikonfirmasi_oleh_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    waktu_batal = db.Column(db.DateTime, nullable=True)

    kasir = db.relationship("User", foreign_keys=[kasir_id])
    pelanggan = db.relationship("Pelanggan")
    metode_bayar = db.relationship("MetodeBayar")

    diajukan_oleh = db.relationship("User", foreign_keys=[diajukan_oleh_id])
    dikonfirmasi_oleh = db.relationship("User", foreign_keys=[dikonfirmasi_oleh_id])

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )
