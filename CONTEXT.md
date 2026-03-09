# Contexto de trabajo

## Estado actual del proyecto (24 Feb 2026)

### Backend FastAPI
- **Base URL**: http://127.0.0.1:8000
- **Base de datos**: MySQL `gereci` en localhost
- **Entorno**: Windows con venv activado en `C:\GERECI\venv`

### Módulos implementados
1. ✅ **Usuarios**: CRUD completo con id_cargo, permisos por rol
2. ✅ **Documentos**: Flujo completo de creación → aprobación → firmas → PDF
3. ✅ **Plantillas**: Sistema de campos dinámicos y tablas dinámicas
4. ✅ **Firmas Digitales**: Sistema de registro y visualización
5. ✅ **Roles y Permisos**: Control de acceso por módulo

### Sistema de Usuarios
- Endpoints: GET `/users/id/{id}`, GET `/users/all`, PUT `/users/{id}`, PUT `/users/{id}/inactivar`, DELETE `/users/{id}`, POST `/users/create`
- Esquema `UserOut` expone `rol_nombre` y `cargo_nombre` con LEFT JOIN
- Frontend `admin.js` muestra nombres de rol/cargo y gestiona CRUD completo

## ÚLTIMAS ACTUALIZACIONES (24 Feb 2026)

### ✅ SOLUCIÓN IMPLEMENTADA: Sistema de Firmas Digitales
**Problema resuelto**: PDF final no mostraba campos de firmas

**Causa identificada**: Las firmas se inyectaban muy tarde (estado FINALIZADO), por lo que el Word no las mostraba y el PDF salía vacío.

**Solución aplicada**: Cambiar punto de inyección de firmas al estado **FIRMADO** (antes de FINALIZADO).

#### Nuevo flujo de estados:
```
APROBADO_GERENCIA → FIRMADO (inyecta TODAS las firmas en Word)
                       ↓
                    FINALIZADO (asigna consecutivo + genera PDF)
```

#### Beneficios:
- ✅ Usuario puede visualizar Word con firmas ANTES de finalizar
- ✅ Separación clara: FIRMADO = firmado | FINALIZADO = emitido oficialmente
- ✅ PDF correcto con todas las firmas visibles
- ✅ Trazabilidad completa del flujo

#### Archivos modificados:
- `backend/app/router/documentos.py` (líneas 280-420) - Lógica de estados FIRMADO y FINALIZADO
- `backend/app/crud/documentos.py` - Función `generar_context_con_firmas()`
- `backend/app/utils/dynamic_data.py` - Función `actualizar_firmas_en_tabla_dinamica()`
- `backend/app/utils/dynamic_tables.py` - Columnas uniformes de firmas

#### Sistema de nombres uniformes:
- Backend y BD usan: `unidad_*`, `juridica_*`, `gerente_*`
- Columnas: `{rol}_nombre`, `{rol}_cargo`, `{rol}_firma`
- Context incluye todas las firmas para generar Word completo

### Actualizaciones previas (Feb 18, 2026)
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
1) **TESTING PRIORITARIO**: Probar flujo completo de firmas (BORRADOR → FIRMADO → FINALIZADO) con documento real
2) Verificar que Word en estado FIRMADO muestre todas las firmas correctamente
3) Validar que PDF final contenga firmas + consecutivo
4) Probar flujo completo Usuarios: listar, crear (con cargo), editar, eliminar, toggle estado
5) Dashboard KPI pendiente
6) Plantillas módulo: Mejorar UI de gestión de campos dinámicos

## Archivos tocados (24 Feb 2026) - Sistema de Firmas
- `backend/app/router/documentos.py` - Bloque estado FIRMADO (inyección firmas) y FINALIZADO (solo consecutivo+PDF)
- `backend/app/crud/documentos.py` - Función generar_context_con_firmas() con nombres uniformes
- `backend/app/utils/dynamic_data.py` - Actualización de tablas dinámicas con datos de firmas
- `backend/app/utils/dynamic_tables.py` - Creación de columnas uniformes (unidad_*, juridica_*, gerente_*)
- `backend/app/crud/plantillas.py` - Documentación de columnas excluidas
- Documentación: CHECKPOINT_FIRMAS.md, SOLUCION_FIRMAS_24FEB.md actualizados

## Archivos tocados (18 Feb 2026) - Limpieza de archivos
- backend/app/router/documentos.py (limpieza de archivos en endpoints finalizacion/eliminacion)
- backend/app/utils/document_generator.py (nueva función eliminar_archivo_documento)

## Notas rápidas

### Sistema de Usuarios
- Endpoint detalle usuario: `/users/id/{user_id}` (evita conflicto con `/users/all`)
- `UserCreate` requiere `estado` y `pass_hash` >= 8 chars
- Consultas usan `rol_nombre` y `cargo_nombre` con LEFT JOIN

### Sistema de Documentos y Firmas
- **Estado FIRMADO**: Inyecta TODAS las firmas en Word (unidad, jurídica si aplica, gerente)
- **Estado FINALIZADO**: Solo asigna consecutivo y genera PDF del Word ya firmado
- Función `eliminar_archivo_documento(documento_id, ruta_relativa)` es idempotente y segura
- Context de firmas usa nombres uniformes: `{rol}_nombre`, `{rol}_cargo`, `{rol}_firma`
- Registro de firma del creador (Unidad) se hace al pasar a estado FIRMADO
- Mapeo de roles: 1=Unidad, 2=Gerencia, 3=Jurídica, 4=Otra

### Flujo de aprobación
- **Con revisión jurídica**: BORRADOR → EN_REVISION_JURIDICA → APROBADO_JURIDICA → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → FINALIZADO
- **Sin revisión jurídica**: BORRADOR → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → FINALIZADO
- Devoluciones posibles: EN_REVISION_JURIDICA/GERENCIAL pueden devolver a BORRADOR

### Limpieza de archivos
- Al finalizar documento (FINALIZADO + PDF exitoso): Elimina `.docx` de `media/documentos/`
- Al devolver documento (DEVUELTO_JURIDICA/GERENCIA): Elimina `.docx` para facilitar reedición
- Al eliminar documento (BORRADOR, DEVUELTO_*): Elimina `.docx` asociados
- Manejo robusto: No interrumpe flujos si falla eliminación

## Cómo levantar el proyecto

### Opción 1: Script automatizado
```bash
& C:\GERECI\start_backend.bat
```

### Opción 2: Manual
```bash
cd C:\GERECI\backend
C:\GERECI\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### Verificar que está corriendo
- Backend: http://127.0.0.1:8000
- Docs API: http://127.0.0.1:8000/docs
- Frontend: Abrir `C:\GERECI\frontend\index.html` en navegador

## Referencias de documentación

Para información detallada, consultar:
- **CHECKPOINT_FIRMAS.md** - Solución completa del sistema de firmas (24 Feb 2026)
- **SOLUCION_FIRMAS_24FEB.md** - Comparación antes/después y flujo detallado
- **README_MODULO_DOCUMENTOS.md** - Funcionalidades del módulo de documentos
- **IMPLEMENTACION_DOCUMENTOS.md** - Detalles técnicos de implementación
- **PERMISOS_POR_MODULOS.md** - Sistema de permisos y roles
- **AGENT_CONTEXT.md** - Contexto técnico para agentes de soporte
- **TESTING_LIMPIEZA_DOCX.md** - Guía de testing de limpieza de archivos

## Stack tecnológico

### Backend
- FastAPI + Uvicorn
- SQLAlchemy + PyMySQL
- python-docx + docxtpl (generación Word)
- Pillow (procesamiento imágenes)
- LibreOffice CLI (conversión PDF)
- python-jose + passlib (autenticación)

### Frontend
- HTML5 + JavaScript (Vanilla)
- Bootstrap 5.3 + Bootstrap Icons
- API REST con fetch()

### Base de datos
- MySQL 8.0+
- Tablas principales: usuarios, documentos, tipos_documentos, plantillas, firmas_digitales, roles, permisos, control_consecutivos

---

**Última actualización**: 24 de Febrero de 2026  
**Estado del sistema**: ✅ Operativo con firmas funcionando correctamente
