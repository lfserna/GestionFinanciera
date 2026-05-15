from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Cuenta, Movimiento, SolicitudDinero, GastoAsistida, Usuario
from app.extensions import db
from app.utils import now_local

bp = Blueprint('dashboard', __name__)


def _rango_periodo(periodo):
    """Devuelve (inicio, fin, periodo_normalizado). Por defecto usa mes."""
    now = now_local()
    periodo = (periodo or 'mes').lower()
    if periodo not in {'dia', 'semana', 'mes', 'trimestre', 'semestre', 'anio', 'ninguno'}:
        periodo = 'mes'
    if periodo == 'ninguno':
        return None, None, periodo
    if periodo == 'dia':
        inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semana':
        inicio = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'mes':
        inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'trimestre':
        mes_inicio = ((now.month - 1) // 3) * 3 + 1
        inicio = now.replace(month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semestre':
        mes_inicio = 1 if now.month <= 6 else 7
        inicio = now.replace(month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # anio
        inicio = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return inicio, now, periodo


def _resumen_usuario(periodo_actual='mes'):
    inicio, fin, periodo_actual = _rango_periodo(periodo_actual)

    cuentas = Cuenta.query.filter_by(usuario_id=current_user.id, estado=True).all()
    cuentas_diarias = [c for c in cuentas if c.uso_cuenta == 'diaria']
    saldo_general_con_ahorros = sum(float(c.saldo_actual or 0) for c in cuentas)
    saldo_efectivo = sum(float(c.saldo_actual or 0) for c in cuentas if c.tipo_cuenta == 'efectivo')
    saldo_bancos = sum(float(c.saldo_actual or 0) for c in cuentas if c.tipo_cuenta in ['banco', 'billetera_movil', 'caja_ahorro'])
    saldo_diarias = sum(float(c.saldo_actual or 0) for c in cuentas_diarias)
    saldo_ahorro = sum(float(c.saldo_actual or 0) for c in cuentas if c.uso_cuenta == 'ahorro')

    # Saldo disponible principal: dinero de cuentas diarias + efectivo.
    # Si una cuenta de efectivo también está marcada como diaria, no se duplica.
    efectivo_diario = sum(float(c.saldo_actual or 0) for c in cuentas if c.tipo_cuenta == 'efectivo' and c.uso_cuenta == 'diaria')
    saldo_disponible = saldo_diarias + saldo_efectivo - efectivo_diario

    base_movs = Movimiento.query.filter_by(usuario_id=current_user.id, estado='activo')
    if inicio is not None:
        base_movs = base_movs.filter(Movimiento.fecha_movimiento >= inicio, Movimiento.fecha_movimiento <= fin)

    filtros_fecha = [Movimiento.fecha_movimiento >= inicio, Movimiento.fecha_movimiento <= fin] if inicio is not None else []
    ingresos = db.session.query(func.coalesce(func.sum(Movimiento.monto), 0)).filter(
        Movimiento.usuario_id == current_user.id,
        Movimiento.tipo_movimiento == 'ingreso',
        Movimiento.estado == 'activo',
        *filtros_fecha
    ).scalar()
    gastos = db.session.query(func.coalesce(func.sum(Movimiento.monto), 0)).filter(
        Movimiento.usuario_id == current_user.id,
        Movimiento.tipo_movimiento == 'salida',
        Movimiento.estado == 'activo',
        *filtros_fecha
    ).scalar()
    ultimos = base_movs.order_by(Movimiento.fecha_movimiento.desc()).limit(5).all()

    return {
        'cuentas': cuentas,
        'cuentas_diarias': cuentas_diarias,
        'saldo_total': saldo_disponible,
        'saldo_disponible': saldo_disponible,
        'saldo_general_con_ahorros': saldo_general_con_ahorros,
        'saldo_efectivo': saldo_efectivo,
        'saldo_bancos': saldo_bancos,
        'saldo_diarias': saldo_diarias,
        'saldo_ahorro': saldo_ahorro,
        'ingresos': ingresos,
        'gastos': gastos,
        'ultimos': ultimos,
        'periodo_actual': periodo_actual,
        'filtro_inicio': inicio,
        'filtro_fin': fin,
    }


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
    if rol == 'asistida':
        solicitudes = SolicitudDinero.query.filter_by(asistida_user_id=current_user.id).order_by(SolicitudDinero.fecha_solicitud.desc()).limit(5).all()
        return render_template('dashboard/asistida.html', solicitudes=solicitudes)

    # Usuario común y admin_asistida comparten el mismo dashboard financiero.
    # El admin_asistida seguirá teniendo sus opciones de gestión asistida en el menú/rutas correspondientes,
    # pero en Inicio verá su propio saldo, gastos, efectivo y últimos movimientos.
    if rol in ['usuario', 'admin_asistida']:
        return render_template('dashboard/usuario.html', **_resumen_usuario('mes'))

    return redirect(url_for('auth.logout'))


@bp.route('/dashboard/grafica')
@login_required
def grafica():
    if current_user.rol.nombre not in ['usuario', 'admin_asistida']:
        return redirect(url_for('dashboard.index'))
    periodo_actual = request.args.get('periodo') or 'mes'
    periodos_grafica = [
        ('dia', 'Diario'), ('semana', 'Semana'), ('mes', 'Mensual'),
        ('trimestre', 'Trimestral'), ('semestre', 'Semestral'), ('anio', 'Anual')
    ]
    data = _resumen_usuario(periodo_actual)
    data['periodos_grafica'] = periodos_grafica
    return render_template('dashboard/grafica.html', **data)
