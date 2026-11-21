
from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(50), unique=True, nullable=False)
    waktu = db.Column(db.DateTime, nullable=False)

    kasir_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    pelanggan_id = db.Column(
        db.Integer, db.ForeignKey("pelanggan.id"), nullable=False
    )
    metode_bayar_id = db.Column(
        db.Integer, db.ForeignKey("metode_bayar.id"), nullable=False
    )

    subtotal = db.Column(db.Integer, nullable=False, default=0)
    tarif_pajak = db.Column(db.Float, nullable=False, default=0)
    pajak = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    uang_diterima = db.Column(db.Integer, nullable=True)
    kembalian = db.Column(db.Integer, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="selesai")

    kasir = db.relationship("User", backref="orders")
    pelanggan = db.relationship("Pelanggan", backref="orders")
    metode_bayar = db.relationship("MetodeBayar", backref="orders")

    items = db.relationship(
        "OrderItem",
        backref="order",
        cascade="all, delete-orphan"
    )


from app.models.order_item import OrderItem
