from datetime import datetime
from zoneinfo import ZoneInfo
from flask import current_app


def now_local():
    tz = ZoneInfo(current_app.config.get('TIMEZONE', 'America/La_Paz'))
    return datetime.now(tz).replace(tzinfo=None)


def money(value):
    try:
        return f"Bs {float(value or 0):,.2f}"
    except Exception:
        return 'Bs 0.00'


def audit(db, Auditoria, accion, tabla_afectada=None, registro_id=None, usuario_id=None, valor_anterior=None, valor_nuevo=None, ip=None, user_agent=None):
    db.session.add(Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        ip=ip,
        user_agent=user_agent,
        created_at=now_local(),
    ))


def get_local_ip():
    """Detecta la IP local principal para acceder desde otros dispositivos de la red."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            return ip or "127.0.0.1"
    except Exception:
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
    return "127.0.0.1"


def print_startup_banner(port):
    local_ip = get_local_ip()
    print("==================================================")
    print(" Sistema Gestion Financiera iniciado")
    print("==================================================")
    print(" Local:")
    print(f" http://127.0.0.1:{port}")
    print()
    print(" Red local:")
    print(f" http://{local_ip}:{port}")
    print("==================================================")
