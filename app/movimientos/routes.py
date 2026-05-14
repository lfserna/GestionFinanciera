from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.forms import MovimientoForm
from app.models import Cuenta, Categoria, MetodoPago, Movimiento
from app.extensions import db
from app.utils import now_local, registrar_auditoria

bp = Blueprint('movimientos', __name__, url_prefix='/movimientos')

def cargar_choices(form, tipo_movimiento):
    tipo_categoria = 'ingreso' if tipo_movimiento == 'ingreso' else 'gasto'
    form.cuenta_id.choices = [(c.id, c.nombre) for c in Cuenta.query.filter_by(usuario_id=current_user.id, estado=True).all()]
    cats = Categoria.query.filter(
        Categoria.estado == True,
        Categoria.tipo == tipo_categoria,
        Categoria.modulo.in_(['general','ambos']),
        ((Categoria.usuario_id == None) | (Categoria.usuario_id == current_user.id))
    ).all()
    form.categoria_id.choices = [(0, 'Opcional')] + [(c.id, c.nombre) for c in cats]
    form.metodo_pago_id.choices = [(0, 'Opcional')] + [(m.id, m.nombre) for m in MetodoPago.query.filter_by(estado=True).all()]

@bp.route('/')
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def index():
    movimientos = Movimiento.query.filter_by(usuario_id=current_user.id).order_by(Movimiento.fecha_movimiento.desc()).limit(100).all()
    return render_template('movimientos/index.html', movimientos=movimientos)

@bp.route('/nuevo/<tipo>', methods=['GET','POST'])
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def nuevo(tipo):
    if tipo not in ['ingreso','salida']:
        flash('Tipo de movimiento inválido.', 'danger')
        return redirect(url_for('movimientos.index'))
    form = MovimientoForm()
    cargar_choices(form, tipo)
    if request.method == 'GET':
        form.fecha_movimiento.data = now_local()
    if form.validate_on_submit():
        cuenta = Cuenta.query.filter_by(id=form.cuenta_id.data, usuario_id=current_user.id).first_or_404()
        monto = Decimal(form.monto.data)
        saldo_actual = Decimal(cuenta.saldo_actual or 0)
        if tipo == 'salida' and saldo_actual < monto:
            flash('No se permite saldo negativo.', 'danger')
        else:
            cuenta.saldo_actual = saldo_actual + monto if tipo == 'ingreso' else saldo_actual - monto
            mov = Movimiento(
                usuario_id=current_user.id,
                cuenta_id=cuenta.id,
                categoria_id=form.categoria_id.data or None,
                metodo_pago_id=form.metodo_pago_id.data or None,
                tipo_movimiento=tipo,
                monto=monto,
                referencia=form.referencia.data or None,
                descripcion=form.descripcion.data or None,
                fecha_movimiento=form.fecha_movimiento.data or now_local(),
                estado='activo',
            )
            db.session.add(mov)
            db.session.flush()
            registrar_auditoria('registrar_movimiento', 'movimientos', mov.id, valor_nuevo={
                'tipo_movimiento': mov.tipo_movimiento, 'cuenta_id': mov.cuenta_id, 'categoria_id': mov.categoria_id,
                'metodo_pago_id': mov.metodo_pago_id, 'monto': mov.monto, 'saldo_anterior': saldo_actual,
                'saldo_nuevo': cuenta.saldo_actual, 'referencia': mov.referencia, 'descripcion': mov.descripcion
            })
            db.session.commit()
            flash('Movimiento registrado correctamente.', 'success')
            return redirect(url_for('movimientos.index'))
    return render_template('movimientos/form.html', form=form, titulo='Nuevo ingreso' if tipo=='ingreso' else 'Nueva salida')
