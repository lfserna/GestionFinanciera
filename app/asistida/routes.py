from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.forms import SolicitudForm
from app.models import Categoria, SolicitudDinero, EntregaAsistida, GastoAsistida, ExtraAsistida
from app.extensions import db
from app.utils import registrar_auditoria

bp = Blueprint('asistida', __name__, url_prefix='/asistida')

@bp.route('/solicitudes')
@login_required
@roles_required('asistida')
@password_change_required
def solicitudes():
    items = SolicitudDinero.query.filter_by(asistida_user_id=current_user.id).order_by(SolicitudDinero.fecha_solicitud.desc()).all()
    return render_template('asistida/solicitudes.html', solicitudes=items)

@bp.route('/solicitar', methods=['GET','POST'])
@login_required
@roles_required('asistida')
@password_change_required
def solicitar():
    form = SolicitudForm()
    form.categoria_id.choices = [(0,'Opcional')] + [(c.id,c.nombre) for c in Categoria.query.filter(Categoria.tipo=='solicitud', Categoria.estado==True, Categoria.modulo.in_(['asistida','ambos'])).all()]
    if form.validate_on_submit():
        if not current_user.admin_asistida_id:
            flash('No tienes un admin_asistida asignado.', 'danger')
        else:
            sol = SolicitudDinero(
                asistida_user_id=current_user.id,
                admin_user_id=current_user.admin_asistida_id,
                categoria_id=form.categoria_id.data or None,
                monto_solicitado=form.monto_solicitado.data,
                prioridad=form.prioridad.data,
                referencia=form.referencia.data or None,
                comentario_asistida=form.comentario_asistida.data,
                estado='pendiente',
            )
            db.session.add(sol)
            db.session.flush()
            registrar_auditoria('crear_solicitud_dinero', 'solicitudes_dinero', sol.id, valor_nuevo={
                'asistida_user_id': sol.asistida_user_id, 'admin_user_id': sol.admin_user_id,
                'categoria_id': sol.categoria_id, 'monto_solicitado': sol.monto_solicitado,
                'prioridad': sol.prioridad, 'referencia': sol.referencia, 'estado': sol.estado
            })
            db.session.commit()
            flash('Solicitud registrada correctamente.', 'success')
            return redirect(url_for('asistida.solicitudes'))
    return render_template('asistida/solicitar.html', form=form)

@bp.route('/gastos')
@login_required
@roles_required('asistida')
@password_change_required
def gastos():
    gastos = GastoAsistida.query.filter_by(asistida_user_id=current_user.id).order_by(GastoAsistida.fecha_gasto.desc()).all()
    return render_template('asistida/gastos.html', gastos=gastos)

@bp.route('/extras')
@login_required
@roles_required('asistida')
@password_change_required
def extras():
    extras = ExtraAsistida.query.filter_by(asistida_user_id=current_user.id).order_by(ExtraAsistida.fecha_extra.desc()).all()
    return render_template('asistida/extras.html', extras=extras)
