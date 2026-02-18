# Contexto de trabajo

## Estado actual
- Backend: CRUD de usuarios ahora incluye `id_cargo` en creación, endpoints: GET `/users/id/{id}`, GET `/users/all`, PUT `/users/{id}`, PUT `/users/{id}/inactivar`, DELETE `/users/{id}`, POST `/users/create`. Esquema `UserOut` expone `rol_nombre` y `cargo_nombre`. Consultas de usuarios hacen LEFT JOIN con roles y cargos.
- Frontend: `admin.js` muestra en Usuarios los nombres de rol/cargo; crear/editar envía `id_cargo` y `id_rol`; crear usa POST `/users/create`; eliminar usa DELETE `/users/{id}`; toggle estado usa PUT `/users/{id}/inactivar`.
- Problema resuelto: no guardaba cargo en creación (ahora insert incluye `id_cargo`). Problema resuelto: DELETE daba “Method Not Allowed” (ahora endpoint implementado).

## ÚLTIMAS ACTUALIZACIONES (Feb 18, 2026)
- ✅ Limpieza automática de `.docx`: Función `eliminar_archivo_documento()` agregada a `document_generator.py`
- ✅ Al finalizar documento (FINALIZADO + PDF exitoso): Elimina `.docx` de `media/documentos/`
- ✅ Al devolver documento (DEVUELTO_JURIDICA/GERENCIA): Elimina `.docx` para facilitar reedición
- ✅ **MEJORA:** Ahora permite eliminar documentos en estados DEVUELTO_JURIDICA y DEVUELTO_GERENCIA
- ✅ Al eliminar documento (BORRADOR, DEVUELTO_JURIDICA, DEVUELTO_GERENCIA): Elimina `.docx` asociados
- ✅ Manejo robusto: No interrumpe flujos si falla eliminación de archivos
- ✅ Logging: Registra intentos de eliminación (info si éxito, warning si falla)
- ✅ Archivo TESTING_LIMPIEZA_DOCX.md con flujos testeables y checklist completo
- ✅ Filtrado por asunto en tiempo real: Búsqueda clientside sin hacer requests
- ✅ Removido botón "Filtrar" innecesario: Filtrados completamente automáticos
- ✅ **SEGURIDAD:** Token expirado (401) redirige a login en lugar de mostrar error

## Pendientes / próximos pasos
1) Probar flujo completo Usuarios: listar, crear (con cargo), editar, eliminar, toggle estado. Revisar consola/red por errores.
2) Verificar permisos en backend según rol del usuario logueado (borrar/actualizar/seleccionar/insertar módulo 4).
3) Plantillas módulo: UI y endpoints pendientes.
4) Dashboard KPI pendiente.
5) **TESTING:** Validar que `.docx` se eliminen al finalizar/borrar documentos sin interrumpir flujos.

## Archivos tocados hoy (Feb 18)
- backend/app/router/documentos.py (limpieza de archivos en endpoints finalizacion/eliminacion)
- backend/app/utils/document_generator.py (nueva función eliminar_archivo_documento)

## Notas rápidas
- Endpoint detalle usuario ahora es `/users/id/{user_id}` para evitar conflicto con `/users/all`.
- `UserCreate` requiere `estado` y `pass_hash` >= 8 chars.
- Consultas usan `rol_nombre` y `cargo_nombre`; la tabla Usuarios los muestra.
- Nueva función `eliminar_archivo_documento(documento_id, ruta_relativa)` en utils es idempotente y segura para llamar múltiples veces.
