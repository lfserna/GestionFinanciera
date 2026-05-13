from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SelectField, TextAreaField, DateTimeLocalField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('Nueva contraseña', validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cambiar contraseña')

class CuentaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    tipo_cuenta = SelectField('Tipo de cuenta', choices=[('efectivo','Efectivo'),('banco','Banco'),('billetera_movil','Billetera móvil'),('caja_ahorro','Caja de ahorro'),('otro','Otro')], validators=[DataRequired()])
    uso_cuenta = SelectField('Uso de cuenta', choices=[('diaria','Diaria'),('ahorro','Ahorro'),('inversion','Inversión'),('emergencia','Emergencia'),('otro','Otro')], validators=[DataRequired()])
    banco_nombre = StringField('Banco', validators=[Optional(), Length(max=120)])
    numero_cuenta = StringField('Número de cuenta', validators=[Optional(), Length(max=80)])
    moneda = StringField('Moneda', validators=[Optional(), Length(max=10)], default='BOB')
    saldo_inicial = DecimalField('Saldo inicial', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    submit = SubmitField('Guardar')

class MovimientoForm(FlaskForm):
    cuenta_id = SelectField('Cuenta', coerce=int, validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()])
    metodo_pago_id = SelectField('Método de pago', coerce=int, validators=[Optional()])
    monto = DecimalField('Monto', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    referencia = StringField('Referencia', validators=[Optional(), Length(max=120)])
    descripcion = StringField('Descripción', validators=[Optional(), Length(max=255)])
    fecha_movimiento = DateTimeLocalField('Fecha', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Guardar')

class SolicitudForm(FlaskForm):
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()])
    monto_solicitado = DecimalField('Monto solicitado', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    prioridad = SelectField('Prioridad', choices=[('baja','Baja'),('normal','Normal'),('alta','Alta'),('urgente','Urgente')], default='normal')
    referencia = StringField('Referencia', validators=[Optional(), Length(max=120)])
    comentario_asistida = TextAreaField('Comentario', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Solicitar')

class AlertaForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=150)])
    mensaje = TextAreaField('Mensaje', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('info','Info'),('advertencia','Advertencia'),('mantenimiento','Mantenimiento'),('urgente','Urgente')], validators=[DataRequired()])
    destino = SelectField('Destino', choices=[('global','Global'),('rol','Por rol'),('usuario','Por usuario')], validators=[DataRequired()])
    rol_id = SelectField('Rol', coerce=int, validators=[Optional()])
    usuario_id = SelectField('Usuario', coerce=int, validators=[Optional()])
    fecha_inicio = DateTimeLocalField('Fecha inicio', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    fecha_fin = DateTimeLocalField('Fecha fin', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    mostrar_cada_login = BooleanField('Mostrar cada login')
    estado = BooleanField('Activa', default=True)
    submit = SubmitField('Guardar')
