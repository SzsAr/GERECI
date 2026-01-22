# Contexto de trabajo

## Estado actual
- Backend: CRUD de usuarios ahora incluye `id_cargo` en creación, endpoints: GET `/users/id/{id}`, GET `/users/all`, PUT `/users/{id}`, PUT `/users/{id}/inactivar`, DELETE `/users/{id}`, POST `/users/create`. Esquema `UserOut` expone `rol_nombre` y `cargo_nombre`. Consultas de usuarios hacen LEFT JOIN con roles y cargos.
- Frontend: `admin.js` muestra en Usuarios los nombres de rol/cargo; crear/editar envía `id_cargo` y `id_rol`; crear usa POST `/users/create`; eliminar usa DELETE `/users/{id}`; toggle estado usa PUT `/users/{id}/inactivar`.
- Problema resuelto: no guardaba cargo en creación (ahora insert incluye `id_cargo`). Problema resuelto: DELETE daba “Method Not Allowed” (ahora endpoint implementado).

## Pendientes / próximos pasos
1) Probar flujo completo Usuarios: listar, crear (con cargo), editar, eliminar, toggle estado. Revisar consola/red por errores.
2) Verificar permisos en backend según rol del usuario logueado (borrar/actualizar/seleccionar/insertar módulo 4).
3) Plantillas módulo: UI y endpoints pendientes.
4) Dashboard KPI pendiente.

## Archivos tocados hoy
- backend/app/router/users.py
- backend/app/crud/users.py
- backend/app/schemas/users.py
- frontend/js/admin.js

## Notas rápidas
- Endpoint detalle usuario ahora es `/users/id/{user_id}` para evitar conflicto con `/users/all`.
- `UserCreate` requiere `estado` y `pass_hash` >= 8 chars.
- Consultas usan `rol_nombre` y `cargo_nombre`; la tabla Usuarios los muestra.
