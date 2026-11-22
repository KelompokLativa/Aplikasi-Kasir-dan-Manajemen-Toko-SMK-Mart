
from functools import wraps

from flask import session, redirect, url_for, abort

from app.models.user import User


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("auth.login"))

        user = User.query.get(user_id)

        if not user or not user.aktif:
            session.clear()
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("auth.login"))

        user = User.query.get(user_id)

        if not user or not user.aktif:
            session.clear()
            return redirect(url_for("auth.login"))

        if not user.is_admin:
            abort(403)

        return view(*args, **kwargs)

    return wrapped_view