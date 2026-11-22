from app.extensions import db


class MetodeBayar(db.Model):
    __tablename__ = "metode_bayar"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    jenis = db.Column(db.String(20), nullable=False, default="tunai")
    aktif = db.Column(db.Boolean, nullable=False, default=True)
