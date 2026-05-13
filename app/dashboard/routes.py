from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Cuenta, Movimiento, SolicitudDinero, GastoAsistida, Usuario
from app.extensions import db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def home():
    return redirect(url_for('dashboard.index'))

@bp.route('/dashboard')
@login_required
def index():
    rol = current_user.rol.nombre
    if rol == 'superadmin':
        total_usuarios = Usuario.query.count()
        return render_template('dashboard/superadmin.html', total_usuarios=total_usuarios)
    if rol == 'admin_asistida':
        total_asistidos = Usuario.query.filter_by(admin_asistida_id=current_user.id).count()
        pendientes = SolicitudDinero.query.filter_by(admin_user_id=current_user.id, estado='pendiente').count()
        return render_template('dashboard/admin_asistida.html', total_asistidos=total_asistidos, pendientes=pendientes)
    if rol == 'asistida':
        solicitudes = SolicitudDinero.query.filter_by(asistida_user_id=current_user.id).order_by(SolicitudDinero.fecha_solicitud.desc()).limit(5).all()
        return render_template('dashboard/asistida.html', solicitudes=solicitudes)

    cuentas = Cuenta.query.filter_by(usuario_id=current_user.id, estado=True).all()
    saldo_total = sum(float(c.saldo_actual or 0) for c in cuentas)
    saldo_efectivo = sum(float(c.saldo_actual or 0) for c in cuentas if c.tipo_cuenta == 'efectivo')
    saldo_bancos = sum(float(c.saldo_actual or 0) for c in cuentas if c.tipo_cuenta in ['banco', 'billetera_movil', 'caja_ahorro'])
    saldo_diarias = sum(float(c.saldo_actual or 0) for c in cuentas if c.uso_cuenta == 'diaria')
    saldo_ahorro = sum(float(c.saldo_actual or 0) for c in cuentas if c.uso_cuenta == 'ahorro')
    ingresos = db.session.query(func.coalesce(func.sum(Movimiento.monto),0)).filter_by(usuario_id=current_user.id,tipo_movimiento='ingreso',estado='activo').scalar()
    gastos = db.session.query(func.coalesce(func.sum(Movimiento.monto),0)).filter_by(usuario_id=current_user.id,tipo_movimiento='salida',estado='activo').scalar()
    ultimos = Movimiento.query.filter_by(usuario_id=current_user.id).order_by(Movimiento.fecha_movimiento.desc()).limit(5).all()
    return render_template('dashboard/usuario.html', cuentas=cuentas, saldo_total=saldo_total, saldo_efectivo=saldo_efectivo, saldo_bancos=saldo_bancos, saldo_diarias=saldo_diarias, saldo_ahorro=saldo_ahorro, ingresos=ingresos, gastos=gastos, ultimos=ultimos)
