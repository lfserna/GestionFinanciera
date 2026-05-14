from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.forms import LoginForm, ChangePasswordForm
from app.models import Usuario
from app.extensions import db
from app.utils import now_local, registrar_auditoria

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.estado and user.check_password(form.password.data):
            user.ultimo_login = now_local()
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard.index'))
        flash('Credenciales inválidas o usuario inactivo.', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/cambiar-password', methods=['POST'])
@login_required
def cambiar_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.password.data == 'hola123':
            flash('La nueva contraseña no puede ser hola123.', 'danger')
        else:
            current_user.set_password(form.password.data)
            current_user.must_change_password = False
            registrar_auditoria('cambiar_password', 'usuarios', current_user.id, valor_nuevo={'must_change_password': False})
            db.session.commit()
            flash('Contraseña actualizada correctamente.', 'success')
    else:
        flash('La contraseña debe tener mínimo 8 caracteres y coincidir.', 'danger')
    return redirect(url_for('dashboard.index'))
