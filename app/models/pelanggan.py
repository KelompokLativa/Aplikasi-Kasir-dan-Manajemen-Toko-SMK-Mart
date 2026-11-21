from app.extensions import db


class Pelanggan(db.Model):
    __tablename__ = "pelanggan"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20), nullable=True)
    bawaan = db.Column(db.Boolean, default=False, nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Pelanggan {self.nama}>"