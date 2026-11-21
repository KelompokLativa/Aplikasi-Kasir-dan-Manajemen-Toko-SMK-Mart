from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False
    )
    produk_id = db.Column(
        db.Integer, db.ForeignKey("produk.id"), nullable=False
    )

    nama_produk = db.Column(db.String(100), nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

    produk = db.relationship("Produk", backref="order_items")