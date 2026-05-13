from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db, login_manager
from .utils import now_local


class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(150))
    estado = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    admin_asistida_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)
    must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    estado = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    rol = db.relationship('Rol')
    admin_asistida = db.relationship('Usuario', remote_side=[id], backref='asistidos')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido or ''}".strip()


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Cuenta(db.Model):
    __tablename__ = 'cuentas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    tipo_cuenta = db.Column(db.String(40), nullable=False, default='efectivo')
    uso_cuenta = db.Column(db.String(40), nullable=False, default='diaria')
    banco_nombre = db.Column(db.String(120))
    numero_cuenta = db.Column(db.String(80))
    moneda = db.Column(db.String(10), default='BOB')
    saldo_inicial = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    saldo_actual = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    estado = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    usuario = db.relationship('Usuario', backref='cuentas')


class MetodoPago(db.Model):
    __tablename__ = 'metodos_pago'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    descripcion = db.Column(db.String(150))
    estado = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    nombre = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    modulo = db.Column(db.String(40), nullable=False, default='general')
    color = db.Column(db.String(30))
    icono = db.Column(db.String(50))
    estado = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    usuario = db.relationship('Usuario', backref='categorias')


class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    metodo_pago_id = db.Column(db.Integer, db.ForeignKey('metodos_pago.id'))
    tipo_movimiento = db.Column(db.String(40), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_movimiento = db.Column(db.DateTime, default=now_local, nullable=False)
    referencia = db.Column(db.String(120))
    descripcion = db.Column(db.String(255))
    comprobante_path = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activo', nullable=False)
    motivo_anulacion = db.Column(db.String(255))
    anulado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_anulacion = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    cuenta = db.relationship('Cuenta')
    categoria = db.relationship('Categoria')
    metodo_pago = db.relationship('MetodoPago')


class Transferencia(db.Model):
    __tablename__ = 'transferencias'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cuenta_origen_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=False)
    cuenta_destino_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=False)
    movimiento_salida_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'))
    movimiento_entrada_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'))
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_transferencia = db.Column(db.DateTime, default=now_local, nullable=False)
    referencia = db.Column(db.String(120))
    descripcion = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='activa', nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    cuenta_origen = db.relationship('Cuenta', foreign_keys=[cuenta_origen_id])
    cuenta_destino = db.relationship('Cuenta', foreign_keys=[cuenta_destino_id])


class SolicitudDinero(db.Model):
    __tablename__ = 'solicitudes_dinero'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asistida_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    monto_solicitado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_aprobado = db.Column(db.Numeric(12, 2))
    fecha_solicitud = db.Column(db.DateTime, default=now_local, nullable=False)
    fecha_respuesta = db.Column(db.DateTime)
    fecha_entrega = db.Column(db.DateTime)
    prioridad = db.Column(db.String(20), default='normal', nullable=False)
    referencia = db.Column(db.String(120))
    comentario_asistida = db.Column(db.String(255))
    comentario_admin = db.Column(db.String(255))
    estado = db.Column(db.String(30), default='pendiente', nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    asistida = db.relationship('Usuario', foreign_keys=[asistida_user_id])
    admin = db.relationship('Usuario', foreign_keys=[admin_user_id])
    categoria = db.relationship('Categoria')


class EntregaAsistida(db.Model):
    __tablename__ = 'entregas_asistida'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey('solicitudes_dinero.id'))
    asistida_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cuenta_origen_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'))
    movimiento_id = db.Column(db.Integer, db.ForeignKey('movimientos.id'))
    metodo_pago_id = db.Column(db.Integer, db.ForeignKey('metodos_pago.id'))
    monto_entregado = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_entrega = db.Column(db.DateTime, default=now_local, nullable=False)
    referencia = db.Column(db.String(120))
    observacion = db.Column(db.String(255))
    estado = db.Column(db.String(30), default='activa', nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    solicitud = db.relationship('SolicitudDinero')
    asistida = db.relationship('Usuario', foreign_keys=[asistida_user_id])
    admin = db.relationship('Usuario', foreign_keys=[admin_user_id])
    cuenta_origen = db.relationship('Cuenta')


class GastoAsistida(db.Model):
    __tablename__ = 'gastos_asistida'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asistida_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_asistida.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_gasto = db.Column(db.DateTime, default=now_local, nullable=False)
    referencia = db.Column(db.String(120))
    descripcion = db.Column(db.String(255), nullable=False)
    comprobante_path = db.Column(db.String(255))
    estado_revision = db.Column(db.String(30), default='pendiente', nullable=False)
    observacion_admin = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    asistida = db.relationship('Usuario')
    entrega = db.relationship('EntregaAsistida')
    categoria = db.relationship('Categoria')


class ExtraAsistida(db.Model):
    __tablename__ = 'extras_asistida'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asistida_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_extra = db.Column(db.DateTime, default=now_local, nullable=False)
    referencia = db.Column(db.String(120))
    descripcion = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    asistida = db.relationship('Usuario')


class ArqueoAsistida(db.Model):
    __tablename__ = 'arqueos_asistida'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asistida_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    entrega_id = db.Column(db.Integer, db.ForeignKey('entregas_asistida.id'), nullable=False)
    fecha_arqueo = db.Column(db.DateTime, default=now_local, nullable=False)
    monto_entregado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_gastado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_restante_esperado = db.Column(db.Numeric(12, 2), nullable=False)
    monto_restante_declarado = db.Column(db.Numeric(12, 2), nullable=False)
    diferencia = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.String(40), default='abierto', nullable=False)
    observacion = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class MetaAhorro(db.Model):
    __tablename__ = 'metas_ahorro'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas.id'), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    monto_objetivo = db.Column(db.Numeric(12, 2), nullable=False)
    monto_actual = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    fecha_inicio = db.Column(db.Date)
    fecha_objetivo = db.Column(db.Date)
    estado = db.Column(db.String(20), default='activa', nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Presupuesto(db.Model):
    __tablename__ = 'presupuestos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    monto_limite = db.Column(db.Numeric(12, 2), nullable=False)
    periodo = db.Column(db.String(20), default='mensual', nullable=False)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Alerta(db.Model):
    __tablename__ = 'alertas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(150), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(30), default='info', nullable=False)
    estado = db.Column(db.Boolean, default=True, nullable=False)
    mostrar_cada_login = db.Column(db.Boolean, default=False, nullable=False)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    destinatarios = db.relationship('AlertaDestinatario', backref='alerta', cascade='all, delete-orphan')


class AlertaDestinatario(db.Model):
    __tablename__ = 'alerta_destinatarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey('alertas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    es_global = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    rol = db.relationship('Rol', foreign_keys=[rol_id])

    @property
    def destino_texto(self):
        if self.es_global:
            return 'Global'
        if self.rol_id:
            return f"Rol: {self.rol.nombre if self.rol else self.rol_id}"
        if self.usuario_id:
            return f"Usuario: {self.usuario.nombre_completo if self.usuario else self.usuario_id}"
        return 'Sin destino'


class AlertaVista(db.Model):
    __tablename__ = 'alertas_vistas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey('alertas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    visto = db.Column(db.Boolean, default=True, nullable=False)
    fecha_visto = db.Column(db.DateTime, default=now_local)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Auditoria(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    accion = db.Column(db.String(120), nullable=False)
    tabla_afectada = db.Column(db.String(120))
    registro_id = db.Column(db.Integer)
    valor_anterior = db.Column(db.Text)
    valor_nuevo = db.Column(db.Text)
    ip = db.Column(db.String(80))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)
