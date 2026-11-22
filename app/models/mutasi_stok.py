from datetime import datetime

from app.extensions import db


class MutasiStok(db.Model):
    __tablename__ = "mutasi_stok"

    id = db.Column(db.Integer, primary_key=True)

    produk_id = db.Column(
        db.Integer,
        db.ForeignKey("produk.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    waktu = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    tipe = db.Column(
        db.String(20),
        nullable=False
    )

    jumlah = db.Column(
        db.Integer,
        nullable=False
    )

    stok_sebelum = db.Column(
        db.Integer,
        nullable=False
    )

    stok_sesudah = db.Column(
        db.Integer,
        nullable=False
    )

    keterangan = db.Column(
        db.String(255)
    )

    produk = db.relationship(
        "Produk",
        backref=db.backref("mutasi_stok", lazy=True)
    )

    user = db.relationship(
        "User",
        backref=db.backref("mutasi_stok", lazy=True)
    )
