from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.decorators import roles_required, password_change_required
from app.forms import AlertaForm
from app.models import Alerta, AlertaDestinatario, AlertaVista, Rol, Usuario
from app.extensions import db
from app.utils import now_local, registrar_auditoria

bp = Blueprint('alertas', __name__, url_prefix='/alertas')


def alertas_para_usuario(usuario):
    now = now_local()
    q = (
        Alerta.query
        .join(AlertaDestinatario, AlertaDestinatario.alerta_id == Alerta.id)
        .outerjoin(AlertaVista, (AlertaVista.alerta_id == Alerta.id) & (AlertaVista.usuario_id == usuario.id))
        .filter(
            Alerta.estado == True,
            or_(Alerta.fecha_inicio == None, Alerta.fecha_inicio <= now),
            or_(Alerta.fecha_fin == None, Alerta.fecha_fin >= now),
            or_(
                AlertaDestinatario.es_global == True,
                AlertaDestinatario.rol_id == usuario.rol_id,
                AlertaDestinatario.usuario_id == usuario.id,
            ),
            or_(Alerta.mostrar_cada_login == True, AlertaVista.id == None, AlertaVista.visto == False),
        )
        .order_by(Alerta.id.desc())
        .distinct()
    )
    return q.all()


def _cargar_choices(form):
    form.rol_id.choices = [(0, 'Seleccione rol')] + [(r.id, r.nombre) for r in Rol.query.filter_by(estado=True).order_by(Rol.nombre).all()]
    form.usuario_id.choices = [(0, 'Seleccione usuario')] + [(u.id, u.nombre_completo) for u in Usuario.query.filter_by(estado=True).order_by(Usuario.nombre, Usuario.apellido).all()]


def _guardar_destinatario(alerta, form):
    AlertaDestinatario.query.filter_by(alerta_id=alerta.id).delete()
    if form.destino.data == 'rol' and form.rol_id.data and form.rol_id.data != 0:
        db.session.add(AlertaDestinatario(alerta_id=alerta.id, rol_id=form.rol_id.data, usuario_id=None, es_global=False, created_at=now_local(), updated_at=now_local()))
    elif form.destino.data == 'usuario' and form.usuario_id.data and form.usuario_id.data != 0:
        db.session.add(AlertaDestinatario(alerta_id=alerta.id, usuario_id=form.usuario_id.data, rol_id=None, es_global=False, created_at=now_local(), updated_at=now_local()))
    else:
        db.session.add(AlertaDestinatario(alerta_id=alerta.id, usuario_id=None, rol_id=None, es_global=True, created_at=now_local(), updated_at=now_local()))


def _destino_actual(alerta):
    d = alerta.destinatarios[0] if alerta.destinatarios else None
    if not d or d.es_global:
        return 'global', 0, 0
    if d.rol_id:
        return 'rol', d.rol_id, 0
    if d.usuario_id:
        return 'usuario', 0, d.usuario_id
    return 'global', 0, 0


@bp.route('/')
@login_required
@password_change_required
def index():
    if current_user.rol.nombre == 'superadmin':
        alertas = Alerta.query.order_by(Alerta.id.desc()).all()
    else:
        alertas = alertas_para_usuario(current_user)
    return render_template('alertas/index.html', alertas=alertas)


@bp.route('/nueva', methods=['GET','POST'])
@login_required
@roles_required('superadmin')
@password_change_required
def nueva():
    form = AlertaForm()
    _cargar_choices(form)
    if form.validate_on_submit():
        now = now_local()
        alerta = Alerta(
            titulo=form.titulo.data.strip(),
            mensaje=form.mensaje.data.strip(),
            tipo=form.tipo.data,
            mostrar_cada_login=form.mostrar_cada_login.data,
            estado=form.estado.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            created_by=current_user.id,
            created_at=now,
            updated_at=now,
        )
        db.session.add(alerta)
        db.session.flush()
        _guardar_destinatario(alerta, form)
        registrar_auditoria('crear_alerta', 'alertas', alerta.id, valor_nuevo={
            'titulo': alerta.titulo, 'tipo': alerta.tipo, 'estado': bool(alerta.estado),
            'mostrar_cada_login': bool(alerta.mostrar_cada_login), 'destino': form.destino.data
        })
        db.session.commit()
        flash('Alerta creada.', 'success')
        return redirect(url_for('alertas.index'))
    return render_template('alertas/form.html', form=form, titulo='Nueva alerta')


@bp.route('/<int:id>/editar', methods=['GET','POST'])
@login_required
@roles_required('superadmin')
@password_change_required
def editar(id):
    alerta = Alerta.query.get_or_404(id)
    form = AlertaForm(obj=alerta)
    _cargar_choices(form)
    if form.validate_on_submit():
        alerta.titulo = form.titulo.data.strip()
        alerta.mensaje = form.mensaje.data.strip()
        alerta.tipo = form.tipo.data
        alerta.estado = form.estado.data
        alerta.mostrar_cada_login = form.mostrar_cada_login.data
        alerta.fecha_inicio = form.fecha_inicio.data
        alerta.fecha_fin = form.fecha_fin.data
        alerta.updated_at = now_local()
        _guardar_destinatario(alerta, form)
        registrar_auditoria('editar_alerta', 'alertas', alerta.id, valor_nuevo={
            'titulo': alerta.titulo, 'tipo': alerta.tipo, 'estado': bool(alerta.estado),
            'mostrar_cada_login': bool(alerta.mostrar_cada_login), 'destino': form.destino.data
        })
        db.session.commit()
        flash('Alerta actualizada.', 'success')
        return redirect(url_for('alertas.index'))
    if not form.is_submitted():
        destino, rol_id, usuario_id = _destino_actual(alerta)
        form.destino.data = destino
        form.rol_id.data = rol_id
        form.usuario_id.data = usuario_id
    return render_template('alertas/form.html', form=form, titulo='Editar alerta')
