import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "kunci-rahasia-pos-sekolah"
    )

    SQLALCHEMY_DATABASE_URI = database_url or (
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "pos.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"


config = {
    "development": Config,
    "testing": TestingConfig,
}
