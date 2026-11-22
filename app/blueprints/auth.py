from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from app.models.user import User
from app.forms import LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("pos.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash("Username atau password salah.", "danger")
            return render_template(
                "auth/login.html",
                form=form,
                nama_toko="Aplikasi Kasir"
            )

        if not user.aktif:
            flash("Akun Anda tidak aktif. Hubungi Admin.", "danger")
            return render_template(
                "auth/login.html",
                form=form,
                nama_toko="Aplikasi Kasir"
            )

        login_user(user)

        if user.is_admin:
            return redirect(url_for("dashboard.index"))

        return redirect(url_for("pos.index"))

    return render_template(
        "auth/login.html",
        form=form,
        nama_toko="Aplikasi Kasir"
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Anda berhasil keluar.", "success")
    return redirect(url_for("auth.login"))
