from flask import Flask
from .extensions import db, login_manager, csrf
from config import Config


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import Rol, MetodoPago, Categoria

    from .auth.routes import bp as auth_bp
    from .dashboard.routes import bp as dashboard_bp
    from .cuentas.routes import bp as cuentas_bp
    from .movimientos.routes import bp as movimientos_bp
    from .asistida.routes import bp as asistida_bp
    from .admin_asistida.routes import bp as admin_asistida_bp
    from .superadmin.routes import bp as superadmin_bp
    from .alertas.routes import bp as alertas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cuentas_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(asistida_bp)
    app.register_blueprint(admin_asistida_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(alertas_bp)

    @app.template_filter('money')
    def money_filter(value):
        from .utils import money
        return money(value)

    @app.template_filter('datetime_short')
    def datetime_short_filter(value):
        if not value:
            return ''
        try:
            return value.strftime('%d/%m/%Y %H:%M')
        except Exception:
            return str(value)

    @app.context_processor
    def global_template_context():
        """Datos pequeños disponibles en todos los templates."""
        try:
            from flask_login import current_user
            from .models import SolicitudDinero

            if current_user and current_user.is_authenticated and current_user.rol:
                rol_nombre = current_user.rol.nombre
                if rol_nombre == 'admin_asistida':
                    count = SolicitudDinero.query.filter_by(
                        admin_user_id=current_user.id,
                        estado='pendiente'
                    ).count()
                    return {
                        'solicitudes_badge_count': count,
                        'solicitudes_menu_url': 'admin_asistida.solicitudes',
                    }
                if rol_nombre == 'asistida':
                    count = SolicitudDinero.query.filter(
                        SolicitudDinero.asistida_user_id == current_user.id,
                        SolicitudDinero.estado.in_(['pendiente', 'aprobada'])
                    ).count()
                    return {
                        'solicitudes_badge_count': count,
                        'solicitudes_menu_url': 'asistida.solicitudes',
                    }
        except Exception:
            pass
        return {
            'solicitudes_badge_count': 0,
            'solicitudes_menu_url': None,
        }

    def _money_input_mask_script():
        return r"""
<script>
(function () {
  function moneyTargets() {
    return Array.from(document.querySelectorAll('input')).filter(function (input) {
      var name = (input.name || '').toLowerCase();
      return name.includes('monto') || name === 'saldo_inicial' || name === 'saldo_actual' || name === 'monto_limite' || name === 'monto_objetivo';
    });
  }
  function onlyDigits(value) {
    return String(value || '').replace(/\D/g, '');
  }
  function formatCentsFromDigits(digits) {
    digits = onlyDigits(digits).replace(/^0+(?=\d)/, '');
    if (!digits) digits = '0';
    var cents = parseInt(digits, 10);
    if (isNaN(cents)) cents = 0;
    return (cents / 100).toFixed(2);
  }
  function initMoneyInput(input) {
    if (input.dataset.moneyMaskReady === '1') return;
    input.dataset.moneyMaskReady = '1';
    input.setAttribute('inputmode', 'numeric');
    input.setAttribute('autocomplete', 'off');
    if (!input.placeholder) input.placeholder = '0.00';
    input.addEventListener('input', function () {
      var digits = onlyDigits(input.value);
      input.value = formatCentsFromDigits(digits);
      try { input.setSelectionRange(input.value.length, input.value.length); } catch (e) {}
    });
    input.addEventListener('focus', function () {
      if (!input.value) input.value = '0.00';
    });
  }
  function initAll() { moneyTargets().forEach(initMoneyInput); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initAll);
  else initAll();
})();
</script>
"""

    @app.after_request
    def inject_global_ui(response):
        try:
            content_type = response.headers.get('Content-Type', '')
            if response.status_code == 200 and 'text/html' in content_type:
                html = response.get_data(as_text=True)
                scripts = _money_input_mask_script()
                if '</body>' in html:
                    html = html.replace('</body>', scripts + '</body>')
                else:
                    html += scripts
                response.set_data(html)
                response.headers['Content-Length'] = str(len(response.get_data()))
        except Exception:
            pass
        return response

    @app.cli.command('init-db')
    def init_db_command():
        db.create_all()
        seed_data()
        print('Base de datos inicializada correctamente.')

    def seed_data():
        roles = [
            (1, 'superadmin', 'Acceso total'),
            (2, 'usuario', 'Usuario común'),
            (3, 'asistida', 'Usuario asistido'),
            (4, 'admin_asistida', 'Administrador de usuarios asistidos'),
        ]
        for rid, nombre, desc in roles:
            if not Rol.query.filter_by(nombre=nombre).first():
                db.session.add(Rol(id=rid, nombre=nombre, descripcion=desc, estado=True))

        for nombre in ['Efectivo','Tarjeta','QR','Transferencia','Cajero','Débito automático','Otro']:
            if not MetodoPago.query.filter_by(nombre=nombre).first():
                db.session.add(MetodoPago(nombre=nombre, estado=True))

        cats = []
        cats += [('Sueldo','ingreso','general'),('Extra','ingreso','general'),('Venta','ingreso','general'),('Reembolso','ingreso','general')]
        cats += [('Comida','gasto','general'),('Transporte','gasto','general'),('Hogar','gasto','general'),('Salud','gasto','general'),('Personal','gasto','general'),('Servicios','gasto','general'),('Entretenimiento','gasto','general'),('Inversión','gasto','general'),('Deudas','gasto','general'),('Otro gasto','gasto','general')]
        cats += [('Hogar','solicitud','asistida'),('Personal','solicitud','asistida'),('Transporte','solicitud','asistida'),('Salud','solicitud','asistida'),('Comida','solicitud','asistida'),('Invertir','solicitud','asistida'),('Emergencia','solicitud','asistida'),('Otro','solicitud','asistida')]
        cats += [('Extra recibido','extra','asistida'),('Regalo','extra','asistida'),('Ayuda externa','extra','asistida')]
        for nombre, tipo, modulo in cats:
            q = Categoria.query.filter_by(usuario_id=None, nombre=nombre, tipo=tipo, modulo=modulo).first()
            if not q:
                db.session.add(Categoria(nombre=nombre, tipo=tipo, modulo=modulo, estado=True))
        db.session.commit()

    return app

app = create_app()
