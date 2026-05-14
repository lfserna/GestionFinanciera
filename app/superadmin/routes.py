from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.models import Usuario, Rol, Auditoria
from app.extensions import db
from app.utils import now_local

bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

HASH_HOLA123 = 'scrypt:32768:8:1$fPtDkmNvzdrDcBwI$4b58c951bc4815fcfb122dc42ae542ebc38373faac101c7138a43984d49d9de7655ac54e97f59d01a528c7af25eecf69884788f2cb7aae86604a7eb0a04e6e0a'

@bp.route('/usuarios')
@login_required
@roles_required('superadmin')
@password_change_required
def usuarios():
    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()
    roles = Rol.query.all()
    admins = Usuario.query.join(Rol).filter(Rol.nombre=='admin_asistida').all()
    return render_template('superadmin/usuarios.html', usuarios=usuarios, roles=roles, admins=admins)

@bp.route('/usuarios/crear', methods=['POST'])
@login_required
@roles_required('superadmin')
@password_change_required
def crear_usuario():
    now = now_local()
    u = Usuario(
        nombre=request.form['nombre'].strip(),
        apellido=request.form['apellido'].strip(),
        email=request.form['email'].lower().strip(),
        telefono=(request.form.get('telefono') or '').strip() or None,
        rol_id=int(request.form['rol_id']),
        admin_asistida_id=request.form.get('admin_asistida_id') or None,
        password_hash=HASH_HOLA123,
        must_change_password=True,
        estado=True,
        created_at=now,
    )
    db.session.add(u); db.session.commit()
    flash('Usuario creado con contraseña temporal hola123.', 'success')
    return redirect(url_for('superadmin.usuarios'))

@bp.route('/usuarios/<int:id>/toggle')
@login_required
@roles_required('superadmin')
@password_change_required
def toggle_usuario(id):
    u = Usuario.query.get_or_404(id)
    u.estado = not u.estado
    db.session.commit()
    flash('Estado actualizado.', 'success')
    return redirect(url_for('superadmin.usuarios'))

@bp.route('/auditoria')
@login_required
@roles_required('superadmin')
@password_change_required
def auditoria():
    items = Auditoria.query.order_by(Auditoria.created_at.desc()).limit(200).all()
    return render_template('superadmin/auditoria.html', items=items)
