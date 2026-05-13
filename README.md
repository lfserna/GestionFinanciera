# Gestión Financiera - Flask + MySQL

Sistema Flask + MySQL responsive, mobile-first, preparado para ejecución local con Waitress y para Docker con Nginx como reverse proxy.

## 1. Crear entorno virtual

```bash
python -m venv venv
```

## 2. Activar entorno virtual

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4. Configurar `.env`

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

En local normalmente usa:

```env
DB_HOST=localhost
APP_HOST=0.0.0.0
APP_PORT=5050
TIMEZONE=America/La_Paz
```

Para Docker, usa:

```env
DB_HOST=db
```

## 5. Crear tablas y datos iniciales

Con la base `gestion_financiera` ya creada, ejecuta:

```bash
flask --app app init-db
```

Esto crea tablas SQLAlchemy e inserta roles, métodos de pago y categorías globales sin duplicar datos.

## 6. Generar hash de `hola123`

```bash
python scripts/generar_hash.py
```

También puedes generar otro hash:

```bash
python scripts/generar_hash.py MiPassword123
```

## 7. Crear superadmin inicial

Abre `scripts/crear_superadmin.sql`, reemplaza `AQUI_VA_HASH_GENERADO` por el hash generado y ejecuta el SQL en MySQL.

Usuario sugerido:

```text
admin@sistema.com
```

Contraseña temporal:

```text
hola123
```

Al iniciar sesión, el sistema exigirá cambiar la contraseña si `must_change_password = 1`.

## 8. Ejecutar localmente recomendado

```bash
python run.py
```

También puedes ejecutar:

```bash
python app.py
```

El sistema escucha por defecto en:

```text
http://0.0.0.0:5050
```

Desde otro dispositivo de la red entra con:

```text
http://IP_DE_TU_PC:5050
```

Ejemplo:

```text
http://192.168.1.50:5050
```

## 9. Ejecutar con Docker Compose

Crea `.env`, asegúrate de poner `DB_HOST=db`, y ejecuta:

```bash
docker compose up --build
```

Nginx expondrá el sistema por:

```text
http://localhost
```

## 10. Zona horaria

El sistema usa `America/La_Paz` / UTC-4 para fechas por defecto.

## 11. Puerto por defecto

El puerto por defecto es `5050`, configurable en `.env` con `APP_PORT=5050`.
