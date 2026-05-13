from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.forms import CuentaForm
from app.models import Cuenta
from app.extensions import db

bp = Blueprint('cuentas', __name__, url_prefix='/cuentas')

@bp.route('/')
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def index():
    cuentas = Cuenta.query.filter_by(usuario_id=current_user.id).order_by(Cuenta.id.desc()).all()
    return render_template('cuentas/index.html', cuentas=cuentas)

@bp.route('/nueva', methods=['GET','POST'])
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def nueva():
    form = CuentaForm()
    if form.validate_on_submit():
        saldo = form.saldo_inicial.data or 0
        cuenta = Cuenta(
            usuario_id=current_user.id,
            nombre=form.nombre.data,
            tipo_cuenta=form.tipo_cuenta.data,
            uso_cuenta=form.uso_cuenta.data,
            banco_nombre=form.banco_nombre.data or None,
            numero_cuenta=form.numero_cuenta.data or None,
            moneda=form.moneda.data or 'BOB',
            saldo_inicial=saldo,
            saldo_actual=saldo,
            estado=True,
        )
        db.session.add(cuenta); db.session.commit()
        flash('Cuenta creada correctamente.', 'success')
        return redirect(url_for('cuentas.index'))
    return render_template('cuentas/form.html', form=form, titulo='Nueva cuenta')
