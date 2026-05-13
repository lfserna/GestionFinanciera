from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.rol is None or current_user.rol.nombre not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco


def password_change_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.must_change_password:
            flash('Debes cambiar tu contraseña temporal para usar el sistema.', 'warning')
            return redirect(url_for('dashboard.index'))
        return fn(*args, **kwargs)
    return wrapper
