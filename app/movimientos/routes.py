from datetime import timedelta
from decimal import Decimal, InvalidOperation
import unicodedata

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.decorators import roles_required, password_change_required
from app.forms import MovimientoForm
from app.models import Cuenta, Categoria, MetodoPago, Movimiento, Transferencia, ItemSalida, MovimientoDetalle
from app.extensions import db
from app.utils import now_local, registrar_auditoria

bp = Blueprint('movimientos', __name__, url_prefix='/movimientos')


def _normalizar(texto):
    texto = (texto or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in texto if not unicodedata.combining(c))


def _decimal(value, default='0'):
    try:
        return Decimal(str(value if value not in [None, ''] else default)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return Decimal(default).quantize(Decimal('0.01'))


def _es_metodo(nombre, esperado):
    return _normalizar(nombre) == _normalizar(esperado)


def _rango_periodo(periodo):
    """Devuelve (inicio, fin, periodo_normalizado). Si viene vacío, no filtra."""
    now = now_local()
    periodo = (periodo or 'todos').lower()
    if periodo not in {'dia', 'semana', 'mes', 'trimestre', 'semestre', 'anio', 'todos'}:
        periodo = 'todos'
    if periodo == 'todos':
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
    else:
        inicio = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return inicio, now, periodo


def obtener_cuenta_efectivo():
    return (
        Cuenta.query
        .filter_by(usuario_id=current_user.id, estado=True, tipo_cuenta='efectivo')
        .order_by(Cuenta.id.asc())
        .first()
    )


def cargar_choices(form, tipo_movimiento):
    tipo_categoria = 'ingreso' if tipo_movimiento == 'ingreso' else 'gasto'
    cuentas = Cuenta.query.filter_by(usuario_id=current_user.id, estado=True).order_by(Cuenta.nombre.asc()).all()

    if tipo_movimiento == 'salida':
        form.cuenta_id.choices = [(0, 'Se elegirá automáticamente si es efectivo')] + [(c.id, c.nombre) for c in cuentas]
    else:
        form.cuenta_id.choices = [(c.id, c.nombre) for c in cuentas]

    cats = Categoria.query.filter(
        Categoria.estado == True,
        Categoria.tipo == tipo_categoria,
        Categoria.modulo.in_(['general','ambos']),
        ((Categoria.usuario_id == None) | (Categoria.usuario_id == current_user.id))
    ).all()
    form.categoria_id.choices = [(0, 'Opcional')] + [(c.id, c.nombre) for c in cats]
    form.metodo_pago_id.choices = [(0, 'Seleccionar método')] + [(m.id, m.nombre) for m in MetodoPago.query.filter_by(estado=True).order_by(MetodoPago.nombre.asc()).all()]


def _leer_detalles_salida():
    nombres = request.form.getlist('detalle_item_nombre[]')
    item_ids = request.form.getlist('detalle_item_id[]')
    cantidades = request.form.getlist('detalle_cantidad[]')
    precios = request.form.getlist('detalle_precio[]')
    observaciones = request.form.getlist('detalle_observacion[]')

    detalles = []
    max_len = max(len(nombres), len(item_ids), len(cantidades), len(precios), len(observaciones), 0)
    for i in range(max_len):
        nombre = (nombres[i] if i < len(nombres) else '').strip()
        if not nombre:
            continue
        cantidad = _decimal(cantidades[i] if i < len(cantidades) else '1', '1')
        precio = _decimal(precios[i] if i < len(precios) else '0', '0')
        if cantidad <= 0 or precio < 0:
            continue
        subtotal = (cantidad * precio).quantize(Decimal('0.01'))
        raw_item_id = item_ids[i] if i < len(item_ids) else ''
        try:
            item_id = int(raw_item_id) if raw_item_id else None
        except ValueError:
            item_id = None
        detalles.append({
            'item_id': item_id,
            'nombre': nombre,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': subtotal,
            'observacion': (observaciones[i] if i < len(observaciones) else '').strip() or None,
        })
    return detalles


def _guardar_detalles_salida(movimiento, detalles):
    creados = []
    for detalle in detalles:
        item = None
        if detalle['item_id']:
            item = ItemSalida.query.filter_by(id=detalle['item_id'], usuario_id=current_user.id).first()
        if not item:
            item = ItemSalida.query.filter(
                ItemSalida.usuario_id == current_user.id,
                ItemSalida.nombre == detalle['nombre']
            ).first()
        if not item:
            item = ItemSalida(
                usuario_id=current_user.id,
                nombre=detalle['nombre'],
                precio_referencia=detalle['precio'],
                estado=True,
            )
            db.session.add(item)
            db.session.flush()
        else:
            item.nombre = detalle['nombre']
            item.precio_referencia = detalle['precio']
            item.estado = True

        mov_detalle = MovimientoDetalle(
            movimiento_id=movimiento.id,
            item_id=item.id,
            item_nombre=detalle['nombre'],
            cantidad=detalle['cantidad'],
            precio_unitario=detalle['precio'],
            subtotal=detalle['subtotal'],
            observacion=detalle['observacion'],
        )
        db.session.add(mov_detalle)
        creados.append(mov_detalle)
    return creados


@bp.route('/')
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def index():
    periodo_actual = request.args.get('periodo') or 'todos'
    inicio, fin, periodo_actual = _rango_periodo(periodo_actual)
    query = Movimiento.query.filter_by(usuario_id=current_user.id)
    if inicio is not None:
        query = query.filter(Movimiento.fecha_movimiento >= inicio, Movimiento.fecha_movimiento <= fin)
    movimientos = query.order_by(Movimiento.fecha_movimiento.desc()).limit(300).all()
    periodos_movimientos = [
        ('todos', 'Todos'),
        ('dia', 'Diario'),
        ('semana', 'Semana'),
        ('mes', 'Mensual'),
        ('trimestre', 'Trimestral'),
        ('semestre', 'Semestral'),
        ('anio', 'Anual'),
    ]
    return render_template(
        'movimientos/index.html',
        movimientos=movimientos,
        periodo_actual=periodo_actual,
        periodos_movimientos=periodos_movimientos,
    )


@bp.route('/items/buscar')
@login_required
@roles_required('usuario','admin_asistida')
@password_change_required
def buscar_items():
    q = (request.args.get('q') or '').strip()
    query = ItemSalida.query.filter_by(usuario_id=current_user.id, estado=True)
    if q:
        query = query.filter(ItemSalida.nombre.ilike(f'%{q}%'))
    items = query.order_by(ItemSalida.nombre.asc()).limit(20).all()
    return jsonify([
        {
            'id': item.id,
            'nombre': item.nombre,
            'precio_referencia': str(item.precio_referencia or '0.00'),
        }
        for item in items
    ])


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
    items_salida = ItemSalida.query.filter_by(usuario_id=current_user.id, estado=True).order_by(ItemSalida.nombre.asc()).limit(200).all() if tipo == 'salida' else []

    if request.method == 'GET':
        form.fecha_movimiento.data = now_local()

    if form.validate_on_submit():
        monto = Decimal(form.monto.data)
        fecha_movimiento = form.fecha_movimiento.data or now_local()
        metodo = None
        metodo_nombre = ''

        if form.metodo_pago_id.data:
            metodo = MetodoPago.query.filter_by(id=form.metodo_pago_id.data, estado=True).first()
            metodo_nombre = metodo.nombre if metodo else ''

        if tipo == 'salida' and not metodo:
            flash('Primero debes seleccionar el método de pago.', 'danger')
            return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)

        cuenta = None

        if tipo == 'ingreso':
            cuenta = Cuenta.query.filter_by(id=form.cuenta_id.data, usuario_id=current_user.id, estado=True).first()
            if not cuenta:
                flash('Debes seleccionar la cuenta destino.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nuevo ingreso', items_salida=items_salida)

        elif _es_metodo(metodo_nombre, 'efectivo'):
            cuenta = obtener_cuenta_efectivo()
            if not cuenta:
                flash('Para registrar salidas en efectivo primero debes crear una cuenta tipo Efectivo activa.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)

        else:
            cuenta = Cuenta.query.filter_by(id=form.cuenta_id.data, usuario_id=current_user.id, estado=True).first()
            if not cuenta:
                flash('Debes seleccionar la cuenta de origen para este método de pago.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)

        saldo_actual = Decimal(cuenta.saldo_actual or 0)

        # Cajero no es gasto: es retiro desde banco/cuenta hacia efectivo.
        if tipo == 'salida' and _es_metodo(metodo_nombre, 'cajero'):
            cuenta_efectivo = obtener_cuenta_efectivo()
            if not cuenta_efectivo:
                flash('Para retirar por cajero primero debes crear una cuenta tipo Efectivo activa.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)
            if cuenta.id == cuenta_efectivo.id:
                flash('El retiro por cajero debe salir de una cuenta que no sea efectivo.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)
            if saldo_actual < monto:
                flash('No se permite saldo negativo en la cuenta de origen.', 'danger')
                return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)

            saldo_origen_anterior = Decimal(cuenta.saldo_actual or 0)
            saldo_efectivo_anterior = Decimal(cuenta_efectivo.saldo_actual or 0)
            cuenta.saldo_actual = saldo_origen_anterior - monto
            cuenta_efectivo.saldo_actual = saldo_efectivo_anterior + monto

            mov_salida = Movimiento(
                usuario_id=current_user.id,
                cuenta_id=cuenta.id,
                categoria_id=None,
                metodo_pago_id=metodo.id,
                tipo_movimiento='transferencia_salida',
                monto=monto,
                referencia=form.referencia.data or 'Retiro por cajero',
                descripcion=form.descripcion.data or 'Retiro por cajero hacia efectivo',
                fecha_movimiento=fecha_movimiento,
                estado='activo',
            )
            mov_entrada = Movimiento(
                usuario_id=current_user.id,
                cuenta_id=cuenta_efectivo.id,
                categoria_id=None,
                metodo_pago_id=metodo.id,
                tipo_movimiento='transferencia_entrada',
                monto=monto,
                referencia=form.referencia.data or 'Ingreso de efectivo por cajero',
                descripcion=form.descripcion.data or f'Retiro desde {cuenta.nombre}',
                fecha_movimiento=fecha_movimiento,
                estado='activo',
            )
            db.session.add_all([mov_salida, mov_entrada])
            db.session.flush()

            transferencia = Transferencia(
                usuario_id=current_user.id,
                cuenta_origen_id=cuenta.id,
                cuenta_destino_id=cuenta_efectivo.id,
                movimiento_salida_id=mov_salida.id,
                movimiento_entrada_id=mov_entrada.id,
                monto=monto,
                fecha_transferencia=fecha_movimiento,
                referencia=form.referencia.data or 'Retiro por cajero',
                descripcion=form.descripcion.data or 'Retiro por cajero hacia efectivo',
                estado='activa',
            )
            db.session.add(transferencia)
            db.session.flush()

            registrar_auditoria('retiro_cajero_a_efectivo', 'transferencias', transferencia.id, valor_nuevo={
                'cuenta_origen_id': cuenta.id,
                'cuenta_destino_id': cuenta_efectivo.id,
                'metodo_pago_id': metodo.id,
                'monto': monto,
                'saldo_origen_anterior': saldo_origen_anterior,
                'saldo_origen_nuevo': cuenta.saldo_actual,
                'saldo_efectivo_anterior': saldo_efectivo_anterior,
                'saldo_efectivo_nuevo': cuenta_efectivo.saldo_actual,
            })
            db.session.commit()
            flash('Retiro por cajero registrado como transferencia a efectivo. No se contó como gasto.', 'success')
            return redirect(url_for('movimientos.index'))

        if tipo == 'salida' and saldo_actual < monto:
            flash('No se permite saldo negativo.', 'danger')
            return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nueva salida', items_salida=items_salida)

        detalles_salida = _leer_detalles_salida() if tipo == 'salida' else []
        cuenta.saldo_actual = saldo_actual + monto if tipo == 'ingreso' else saldo_actual - monto
        mov = Movimiento(
            usuario_id=current_user.id,
            cuenta_id=cuenta.id,
            categoria_id=form.categoria_id.data or None,
            metodo_pago_id=metodo.id if metodo else None,
            tipo_movimiento=tipo,
            monto=monto,
            referencia=form.referencia.data or None,
            descripcion=form.descripcion.data or None,
            fecha_movimiento=fecha_movimiento,
            estado='activo',
        )
        db.session.add(mov)
        db.session.flush()

        detalles_creados = _guardar_detalles_salida(mov, detalles_salida) if tipo == 'salida' and detalles_salida else []
        detalle_total = sum((Decimal(d.subtotal or 0) for d in detalles_creados), Decimal('0.00'))

        registrar_auditoria('registrar_movimiento', 'movimientos', mov.id, valor_nuevo={
            'tipo_movimiento': mov.tipo_movimiento,
            'cuenta_id': mov.cuenta_id,
            'categoria_id': mov.categoria_id,
            'metodo_pago_id': mov.metodo_pago_id,
            'monto': mov.monto,
            'saldo_anterior': saldo_actual,
            'saldo_nuevo': cuenta.saldo_actual,
            'referencia': mov.referencia,
            'descripcion': mov.descripcion,
            'detalle_items': len(detalles_creados),
            'detalle_total': detalle_total,
        })
        db.session.commit()
        if detalles_creados:
            diferencia = (monto - detalle_total).quantize(Decimal('0.01'))
            if diferencia != Decimal('0.00'):
                flash(f'Movimiento registrado. Detalle: {detalle_total} Bs; diferencia con total: {diferencia} Bs.', 'warning')
            else:
                flash('Movimiento registrado correctamente con detalle de items.', 'success')
        else:
            flash('Movimiento registrado correctamente.', 'success')
        return redirect(url_for('movimientos.index'))

    return render_template('movimientos/form.html', form=form, tipo=tipo, titulo='Nuevo ingreso' if tipo=='ingreso' else 'Nueva salida', items_salida=items_salida)
