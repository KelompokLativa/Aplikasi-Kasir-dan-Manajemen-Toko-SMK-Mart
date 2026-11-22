from app.extensions import db


class Produk(db.Model):
    __tablename__ = "produk"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(50), nullable=False, unique=True)
    nama = db.Column(db.String(150), nullable=False)
    kategori = db.Column(db.String(100), nullable=True)
    harga = db.Column(db.Integer, nullable=False, default=0)
    stok = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True)
