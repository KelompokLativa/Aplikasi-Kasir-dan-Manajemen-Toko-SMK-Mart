from app.extensions import db


class Produk(db.Model):
    __tablename__ = "produk"

    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(50), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    kategori = db.Column(db.String(100), nullable=False, default="Umum")
    harga = db.Column(db.Integer, nullable=False, default=0)
    stok = db.Column(db.Integer, nullable=False, default=0)
    aktif = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Produk {self.nama}>"