from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    peran = db.Column(db.String(20), nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def is_active(self):
        return True if self.aktif is None else self.aktif

    @property
    def is_admin(self):
        return self.peran == "admin"

    @property
    def is_kasir(self):
        return self.peran == "kasir"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)