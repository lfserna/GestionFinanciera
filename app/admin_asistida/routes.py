from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.models import Usuario, SolicitudDinero, EntregaAsistida, GastoAsistida, ExtraAsistida
from app.extensions import db
from app.utils import now_local, registrar_auditoria

bp = Blueprint('admin_asistida', __name__, url_prefix='/admin-asistida')

@bp.route('/usuarios')
@login_required
@roles_required('admin_asistida')
@password_change_required
def usuarios():
    usuarios = Usuario.query.filter_by(admin_asistida_id=current_user.id).all()
    return render_template('admin_asistida/usuarios.html', usuarios=usuarios)

@bp.route('/solicitudes')
@login_required
@roles_required('admin_asistida')
@password_change_required
def solicitudes():
    solicitudes = SolicitudDinero.query.filter_by(admin_user_id=current_user.id).order_by(SolicitudDinero.fecha_solicitud.desc()).all()
    return render_template('admin_asistida/solicitudes.html', solicitudes=solicitudes)

@bp.route('/solicitudes/<int:id>/<accion>')
@login_required
@roles_required('admin_asistida')
@password_change_required
def responder(id, accion):
    sol = SolicitudDinero.query.filter_by(id=id, admin_user_id=current_user.id).first_or_404()
    if accion in ['aprobar','rechazar'] and sol.estado == 'pendiente':
        estado_anterior = sol.estado
        monto_aprobado_anterior = sol.monto_aprobado
        sol.estado = 'aprobada' if accion == 'aprobar' else 'rechazada'
        sol.fecha_respuesta = now_local()
        if accion == 'aprobar':
            sol.monto_aprobado = sol.monto_solicitado
        registrar_auditoria('responder_solicitud_dinero', 'solicitudes_dinero', sol.id, valor_anterior={
            'estado': estado_anterior, 'monto_aprobado': monto_aprobado_anterior
        }, valor_nuevo={
            'estado': sol.estado, 'monto_aprobado': sol.monto_aprobado, 'accion': accion
        })
        db.session.commit()
        flash('Solicitud actualizada.', 'success')
    return redirect(url_for('admin_asistida.solicitudes'))

@bp.route('/gastos')
@login_required
@roles_required('admin_asistida')
@password_change_required
def gastos():
    asistidos = [u.id for u in Usuario.query.filter_by(admin_asistida_id=current_user.id).all()]
    gastos = GastoAsistida.query.filter(GastoAsistida.asistida_user_id.in_(asistidos)).order_by(GastoAsistida.fecha_gasto.desc()).all() if asistidos else []
    return render_template('admin_asistida/gastos.html', gastos=gastos)
