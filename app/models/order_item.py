
from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    produk_id = db.Column(
        db.Integer,
        db.ForeignKey("produk.id"),
        nullable=False
    )

    nama_produk = db.Column(db.String(150), nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False, default=0)
    jumlah = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Integer, nullable=False, default=0)

    order = db.relationship("Order", back_populates="items")
    produk = db.relationship("Produk")