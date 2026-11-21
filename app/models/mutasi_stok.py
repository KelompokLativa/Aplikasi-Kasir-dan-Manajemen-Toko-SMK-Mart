from app.extensions import db
from datetime import datetime


class MutasiStok(db.Model):
    __tablename__ = "mutasi_stok"

    id = db.Column(db.Integer, primary_key=True)

    produk_id = db.Column(
        db.Integer, db.ForeignKey("produk.id"), nullable=False
    )

    tipe = db.Column(db.String(20), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    stok_sebelum = db.Column(db.Integer, nullable=False)
    stok_sesudah = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    waktu = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    produk = db.relationship("Produk", backref="mutasi_stok")

    def __repr__(self):
        return f"<MutasiStok {self.tipe} {self.jumlah}>"