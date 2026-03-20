# CONTEXTO UNIFICADO GERECI

## Fecha de corte
- 19 de marzo de 2026

## Fuente de verdad
- Este archivo reemplaza los contextos y bitacoras previas del directorio raiz.
- Cualquier nuevo cambio funcional o tecnico debe actualizarse aqui.

## Snapshot tecnico
- Backend: FastAPI + SQLAlchemy (consultas SQL textuales)
- Frontend: HTML + JavaScript vanilla + Bootstrap
- Base de datos: MySQL (schema gereci)
- Generacion documental: docxtpl + python-docx + Pillow + LibreOffice CLI
- Auth: JWT (python-jose) + passlib (bcrypt)

## Rutas y componentes principales
- App principal: backend/main.py
- Auth y dependencias: backend/app/api/auth.py, backend/app/api/dependencies.py
- Flujo de documentos: backend/app/router/documentos.py, backend/app/crud/documentos.py
- Generacion Word/PDF y limpieza: backend/app/utils/document_generator.py
- Firmas digitales: backend/app/crud/firmas_digitales.py, backend/app/router/firmas_digitales.py
- Datos/tablas dinamicas de plantillas: backend/app/utils/dynamic_tables.py, backend/app/utils/dynamic_data.py
- Frontend documentos: frontend/documentos.html, frontend/js/documentos.js
- Frontend admin (usuarios, plantillas, carga firma): frontend/admin.html, frontend/js/admin.js
- Cliente API frontend: frontend/js/api.js

## Estado funcional actual

### 1) Usuarios
- CRUD operativo con joins de rol/cargo para visualizacion.
- Carga de firma de usuario implementada en POST /users/{user_id}/firma.
- Restricciones de firma: PNG/JPEG/WebP y maximo 100 KB.

### 2) Documentos
- Creacion de documento: POST /documentos/create.
- Generacion de Word: POST /documentos/{id}/generar-word.
- Cambio de estado (flujo principal): PUT /documentos/{id}/estado.
- Consulta de transiciones validas: GET /documentos/{id}/transiciones.
- Generacion PDF final: POST /documentos/{id}/generar-pdf (tambien se gatilla en finalizacion segun flujo).

### 3) Firmas en documentos
- Las firmas visibles se consolidan en estado FIRMADO (no en FINALIZADO).
- Se usa contexto uniforme por rol:
   - unidad_nombre, unidad_cargo, unidad_firma
   - juridica_nombre, juridica_cargo, juridica_firma
   - gerente_nombre, gerente_cargo, gerente_firma
- En generacion de Word, las rutas de firma se convierten a InlineImage para insertar imagen real.

### 4) Consecutivos y finalizacion
- El consecutivo se asigna por trigger SQL al pasar a FINALIZADO.
- Unicidad por tipo y consecutivo: (id_tipo, consecutivo).
- Se genera PDF desde el Word final y luego se registra ruta_pdf_final.

### 5) Limpieza de archivos
- Al finalizar con PDF exitoso se intenta eliminar docx temporales.
- Al devolver y al eliminar documento (BORRADOR/DEVUELTO_*) se intenta eliminar docx asociados.
- La limpieza es tolerante a fallos (warning en logs, sin romper flujo principal).

### 6) Dashboard operativo y KPIs
- Dashboard actualizado para consumir datos reales desde frontend/js/dashboard.js.
- KPIs activos:
   - Documentos totales
   - Pendientes de firma (derivados de tareas de revision por rol)
   - Tareas del area (pendientes por accion)
   - Observaciones (conteo API y fallback por devoluciones del creador)
- Paneles operativos activos:
   - Distribucion por estado
   - Mi foco hoy (priorizacion por tipo de accion)
   - Ultimos documentos con metadata clave
- Boton de actualizacion manual del dashboard habilitado.
- Logica de tareas pendiente del dashboard alineada con el modelo de Mis Tareas para consistencia funcional.
- Ultimo ajuste de UI aplicado: rediseño del boton "Ver todos" en el bloque de ultimos documentos.
- Archivos involucrados:
   - frontend/dashboard.html
   - frontend/js/dashboard.js
   - frontend/css/custom.css

## Flujo de estados vigente

### Con revision juridica (ej. Resolucion)
BORRADOR -> EN_REVISION_JURIDICA -> APROBADO_JURIDICA -> EN_REVISION_GERENCIAL -> APROBADO_GERENCIA -> FIRMADO -> FINALIZADO

### Sin revision juridica (ej. Circular)
BORRADOR -> EN_REVISION_GERENCIAL -> APROBADO_GERENCIA -> FIRMADO -> FINALIZADO

### Devoluciones
- EN_REVISION_JURIDICA -> DEVUELTO_JURIDICA -> EN_REVISION_JURIDICA
- EN_REVISION_GERENCIAL -> DEVUELTO_GERENCIA -> (EN_REVISION_JURIDICA o EN_REVISION_GERENCIAL segun tipo)

### Reglas importantes
- Solo el creador del documento puede llevarlo a FINALIZADO.
- Las transiciones se validan en backend segun el tipo documental.
- APROBADO_JURIDICA avanza automatico a EN_REVISION_GERENCIAL.
- APROBADO_GERENCIA avanza automatico a FIRMADO.

## Seguridad y permisos
- Autenticacion por /auth/token.
- Si token expira o es invalido, frontend redirige a index.html y limpia token.
- Si usuario esta inactivo (403 especifico), frontend tambien redirige a index.html.
- Permisos por modulo/accion via verify_permissions(db, id_rol, id_modulo, accion).
- Acciones base: insertar, seleccionar, actualizar, borrar.

## Hallazgos tecnicos pendientes (deuda real detectada)

### A) Endpoint legacy de firma
- Existe endpoint POST /documentos/{id}/firmar que conserva logica vieja.
- Ese flujo invoca asignar_consecutivo en CRUD, funcion no presente actualmente.
- Riesgo: error si ese camino se usa para finalizar.

### B) Endpoint /documentos/{id}/datos desalineado
- Intenta acceder campos como si recibiera objeto ORM (id_documento, fecha_finalizacion, etc.).
- El CRUD actual retorna dict con claves id, fecha_emision, etc.
- Riesgo: respuesta rota o excepciones en runtime.

### C) Consulta de firmas con columna incorrecta
- En verificacion de firmas se usa join por d.id_tipo_documento.
- La tabla documentos maneja id_tipo.
- Riesgo: consulta incorrecta en ciertas rutas de verificacion.

### D) Limpieza incompleta de nombre firmado
- La limpieza intenta patron {id}_borrador_firmado.docx.
- El archivo firmado principal se genera como {id}_firmado.docx.
- Riesgo: residuos de archivos .docx.

### E) Drift documental/SQL historico
- Hay guias antiguas con endpoints y secuencias ya superadas.
- El dump base y scripts de alter muestran evolucion de enum de estados.
- Falta script SQL explicito en carpeta database para crear plantillas_tablas_dinamicas,
   aunque el backend depende de esa tabla.

## Prioridades recomendadas (ordenadas)
1. Unificar y desactivar definitivamente rutas legacy de /documentos/{id}/firmar.
2. Corregir endpoint /documentos/{id}/datos al shape real del CRUD.
3. Corregir join de id_tipo_documento -> id_tipo en verificacion de firmas.
4. Ajustar limpieza para contemplar {id}_firmado.docx.
5. Consolidar scripts SQL faltantes para instalacion limpia desde cero.
6. Ejecutar prueba integral del flujo BORRADOR -> FIRMADO -> FINALIZADO con evidencia.

## Pendiente inmediato para retomar
1. Validacion runtime del dashboard con datos reales en navegador (no solo validacion estatica).
2. Validacion multi-rol (superadmin, juridica, gerencia, unidad) para confirmar conteos KPI y foco operativo.
3. Revisar semantica final de KPI "observaciones" y "pendientes de firma" con criterio de negocio.
4. Evaluar endpoint backend dedicado de resumen dashboard si se busca mayor rendimiento/consistencia.

## Registro de cambios recientes (19 de marzo de 2026)

### Cambio 1
- Fecha: 19-03-2026
- Cambio: Implementacion de dashboard operativo con KPIs reales y paneles de distribucion/foco.
- Impacto: Se elimino estado placeholder del dashboard y se incorporo visibilidad operativa basada en datos de documentos y tareas por rol.
- Estado: COMPLETADO (sin errores en validacion estatica de frontend/dashboard.html, frontend/js/dashboard.js y frontend/css/custom.css).

### Cambio 2
- Fecha: 19-03-2026
- Cambio: Rediseño visual del boton "Ver todos" en dashboard.
- Impacto: Mejora de jerarquia visual y usabilidad (hover/focus/feedback).
- Estado: COMPLETADO.

## Comandos operativos

### Arranque rapido
```
start_backend.bat
```

### Arranque manual
```
cd backend
C:\GERECI\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### URLs
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Frontend login: frontend/index.html

## Checklist corto de validacion funcional
1. Crear documento y generar Word.
2. Mover por transiciones validas segun tipo (con/sin juridica).
3. Confirmar Word en FIRMADO con imagenes de firma visibles.
4. Finalizar y verificar consecutivo + PDF.
5. Validar limpieza de docx al devolver/finalizar/eliminar.
6. Simular token expirado y confirmar redireccion a login.

## Regla de mantenimiento de este archivo
- Mantener secciones estables y versionadas por fecha de corte.
- Agregar cambios en formato: Fecha -> Cambio -> Impacto -> Estado.
- Evitar crear nuevos archivos de contexto paralelos.
