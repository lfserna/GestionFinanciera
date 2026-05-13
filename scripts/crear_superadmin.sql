-- 1) Ejecuta: python scripts/generar_hash.py
-- 2) Copia el hash generado y reemplaza AQUI_VA_HASH_GENERADO.
-- 3) Ejecuta este INSERT en la base gestion_financiera.

INSERT INTO usuarios
(rol_id, admin_asistida_id, nombre, apellido, email, telefono, password_hash, must_change_password, estado)
VALUES
(
    1,
    NULL,
    'Superadmin',
    NULL,
    'admin@sistema.com',
    NULL,
    'AQUI_VA_HASH_GENERADO',
    1,
    1
);
