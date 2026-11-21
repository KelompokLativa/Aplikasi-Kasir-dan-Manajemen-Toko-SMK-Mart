from app.extensions import db


class Pengaturan(db.Model):
    __tablename__ = "pengaturan"

    id = db.Column(db.Integer, primary_key=True)
    nama_toko = db.Column(db.String(100), nullable=False, default="SMK Mart")
    alamat_toko = db.Column(db.String(255), nullable=True)
    tarif_pajak = db.Column(db.Float, nullable=False, default=10)
    ambang_stok_menipis = db.Column(db.Integer, nullable=False, default=5)