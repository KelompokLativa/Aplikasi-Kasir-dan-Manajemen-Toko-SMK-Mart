from types import SimpleNamespace

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.models.user import User


auth_bp = Blueprint("auth", __name__)


def buat_form(username=""):
    return SimpleNamespace(
        username=SimpleNamespace(data=username, errors=[]),
        password=SimpleNamespace(errors=[]),
        hidden_tag=lambda: "",
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Username atau password salah.", "danger")
            return render_template(
                "auth/login.html",
                form=buat_form(username),
                nama_toko="SMK Mart",
            )

        if not user.aktif:
            flash("Akun Anda tidak aktif. Hubungi Admin.", "danger")
            return render_template(
                "auth/login.html",
                form=buat_form(username),
                nama_toko="SMK Mart",
            )

        session.clear()
        session["user_id"] = user.id

        if user.is_admin:
            flash(f"Selamat datang, {user.nama}.", "success")
            return redirect(url_for("dashboard.index"))

        if user.is_kasir:
            flash(f"Selamat datang, {user.nama}.", "success")
            return redirect(url_for("pos.index"))

        flash("Anda tidak punya akses ke halaman ini.", "danger")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/login.html",
        form=buat_form(),
        nama_toko="SMK Mart",
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Anda berhasil logout.", "success")
    return redirect(url_for("auth.login"))