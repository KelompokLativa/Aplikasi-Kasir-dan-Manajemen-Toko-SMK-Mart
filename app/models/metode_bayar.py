from app.extensions import db


class MetodeBayar(db.Model):
    __tablename__ = "metode_bayar"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), unique=True, nullable=False)
    jenis = db.Column(db.String(20), nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<MetodeBayar {self.nama}>"