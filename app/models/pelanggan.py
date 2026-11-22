from app.extensions import db


class Pelanggan(db.Model):
    __tablename__ = "pelanggan"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    telepon = db.Column(db.String(30), nullable=True)
    bawaan = db.Column(db.Boolean, nullable=False, default=False)
