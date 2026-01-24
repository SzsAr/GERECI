# Implementación del Módulo Documentos - GERECI

## Resumen de cambios

### 1. Backend - Librerías instaladas
- **docxtpl**: Para renderizar plantillas Word con placeholders {{campo}}
- **python-docx**: Para manipular documentos .docx (incrustar firmas)
- **Pillow**: Para procesar imágenes de firmas

### 2. Backend - Schemas actualizados
**Archivo: `backend/app/schemas/documentos.py`**
- `DocumentoCreate`: Ahora incluye `valores_campos` (Dict con datos de campos)
- `DocumentoUpdate`: Ahora incluye `valores_campos`
- `DocumentoOut`: Incluye campos adicionales `tipo_nombre`, `plantilla_nombre`, `usuario_nombre` (para JOINs)

### 3. Backend - CRUD mejorado
**Archivo: `backend/app/crud/documentos.py`**

#### Nuevas funciones:
- **`obtener_transiciones_validas(db, documento_id, estado_actual)`**: Valida transiciones según si el tipo requiere revisión jurídica
  - Si requiere jurídica: BORRADOR → EN_REVISION_JURIDICA → APROBADO_JURIDICA → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → PENDIENTE_FINALIZACION → FINALIZADO
  - Si NO requiere jurídica: BORRADOR → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → PENDIENTE_FINALIZACION → FINALIZADO
  - Devolvencias: EN_REVISION_JURIDICA/GERENCIAL pueden devolver a BORRADOR

#### Funciones mejoradas:
- **`get_documento_by_id()`**: Incluye JOINs con tipos_documentos, plantillas y usuarios
- **`get_all_documentos()`**: Incluye JOINs, filtra por estado y usuario
- **`cambiar_estado_documento()`**: Valida transiciones antes de cambiar
- **`asignar_consecutivo()`**: Se llama automáticamente al llegar a FINALIZADO

### 4. Backend - Utilidades de generación de documentos
**Archivo: `backend/app/utils/document_generator.py`** (NUEVO)

#### Funciones principales:
- **`generar_word_desde_plantilla(plantilla_path, documento_id, valores_campos)`**
  - Usa docxtpl para reemplazar placeholders {{campo}} en el Word
  - Guarda el documento generado en `/media/documentos/{id}_borrador.docx`
  - Retorna ruta relativa `/static/documentos/...`

- **`incrustar_firma(documento_path, documento_id, usuario_nombre, usuario_cargo, firma_imagen_path)`**
  - Abre el documento Word
  - Añade párrafo con imagen de firma (si existe)
  - Añade nombre del usuario en negrita
  - Añade cargo del usuario en gris
  - Guarda como `/media/documentos/{id}_firmado.docx`

- **`convertir_word_a_pdf(documento_word_path, documento_id)`**
  - Usa LibreOffice CLI para convertir Word a PDF
  - Soporta Windows, macOS, Linux (detecta automáticamente)
  - Guarda como `/media/documentos/{id}_final.pdf`
  - Retorna ruta relativa para descargar

- **`guardar_firma_usuario(usuario_id, imagen_bytes)`**
  - Guarda imagen de firma de usuario en `/media/firmas/firma_usuario_{id}.png`

### 5. Backend - Router mejorado
**Archivo: `backend/app/router/documentos.py`**

#### Endpoints mejorados:
- **`GET /documentos/`**: Ahora retorna JOINs con nombres de tipo, plantilla y usuario

#### Nuevos endpoints:
- **`POST /documentos/{id}/generar`**
  - Genera documento Word desde la plantilla
  - Reemplaza placeholders con valores_campos
  - Guarda ruta en `ruta_word_generado`

- **`POST /documentos/{id}/firmar`**
  - Incrustra firma, nombre y cargo del usuario actual
  - Cambia estado del documento (valida transición)
  - Si llega a FINALIZADO: genera PDF, asigna consecutivo, actualiza fecha_emision
  - Retorna ruta del Word firmado y PDF (si aplica)

- **`GET /documentos/{id}/transiciones`**
  - Retorna los estados válidos desde el estado actual
  - Considera si el tipo requiere revisión jurídica

### 6. Frontend - Nueva pantalla Documentos
**Archivo: `frontend/documentos.html`** (NUEVO)

#### Componentes:
- **Tabla de documentos**: ID, asunto, tipo, plantilla, creador, estado (badge), consecutivo, acciones
- **Filtros**: Por estado, búsqueda por asunto
- **Modal "Nuevo documento"**:
  - Selecciona tipo y plantilla
  - Genera inputs dinámicos basados en campos_json de la plantilla
  - Botón "Generar documento" (POST /create + POST /generar)
  
- **Modal "Ver documento"**:
  - Muestra detalles, estado actual, fecha de creación/emisión
  - Links de descarga Word/PDF
  - Botones de acción según transiciones válidas:
    - "Aprobar y Firmar" (transiciones permitidas)
    - "Devolver" (si hay estado de devolución)
  - Caja de observaciones para devoluciones
  - Sección de campos (futura: edición de valores)

#### Estados visuales (badges con colores):
- BORRADOR: Gris
- EN_REVISION_JURIDICA / EN_REVISION_GERENCIAL: Amarillo
- APROBADO_JURIDICA / APROBADO_GERENCIA: Azul claro
- FIRMADO: Verde
- FINALIZADO: Verde oscuro
- DEVUELTO_*: Rojo

### 7. Frontend - JavaScript
**Archivo: `frontend/js/documentos.js`** (NUEVO)

#### Funciones principales:
- **`cargarDocumentos()`**: Carga tabla con filtros
- **`abrirModalNuevoDoc()`**: Abre modal para crear documento
- **`cargarCamposPlantilla()`**: Al seleccionar plantilla, carga campos dinámicamente
- **`generarDocumento()`**: POST /create + POST /generar
- **`verDocumento(docId)`**: Abre modal con detalles y acciones
- **`firmarDocumento()`**: POST /firmar con cambio de estado
- **`devolverDocumento()`**: Devuelve a BORRADOR con observaciones
- **`obtenerTransiciones()`**: GET /transiciones para mostrar acciones disponibles

### 8. Frontend - Layout actualizado
**Archivo: `frontend/js/layout.js`**
- Link de "Documentos" ahora apunta a `./documentos.html`

---

## Flujo operativo completo

### 1. Crear documento
1. Usuario hace clic en "Nuevo documento"
2. Selecciona tipo de documento y plantilla
3. Sistema carga campos dinámicos (basados en campos_json de plantilla)
4. Usuario completa valores de campos
5. Clic en "Generar documento":
   - POST `/documentos/create` → crea documento en BORRADOR
   - POST `/documentos/{id}/generar` → genera Word reemplazando {{campo}} con valores
   - Documento guardado en `/static/documentos/{id}_borrador.docx`

### 2. Revisión y firmas
1. Documento va a EN_REVISION_JURIDICA (si el tipo lo requiere) o EN_REVISION_GERENCIAL
2. Usuario de jurídica/gerencia abre el documento:
   - Ve estado actual
   - Descarga Word para revisar
   - Si aprueba: Clic "Aprobar y Firmar" → POST `/documentos/{id}/firmar`
     - Sistema incrustra firma (imagen + nombre + cargo) en Word
     - Cambia estado a siguiente (APROBADO_JURIDICA / APROBADO_GERENCIA)
     - Nuevo Word guardado como `/static/documentos/{id}_firmado.docx`
   - Si objeta: Clic "Devolver" + ingresa observaciones → devuelve a BORRADOR

### 3. Finalización
1. Cuando llega a PENDIENTE_FINALIZACION:
   - Usuario hace clic "Aprobar y Firmar" (último paso)
   - POST `/documentos/{id}/firmar` con estado FINALIZADO
   - Sistema:
     - Incrustra última firma
     - Genera PDF desde Word firmado → `/static/documentos/{id}_final.pdf`
     - Asigna consecutivo (ej: RES-001)
     - Actualiza fecha_emision a NOW()
     - Guarda ruta_pdf_final
2. Usuario descarga PDF final

### 4. Devoluciones
- En cualquier fase de revisión, puede devolver a BORRADOR con observaciones
- Documento vuelve al inicio del flujo para correcciones
- Usuario original corrige y reenía

---

## Arquitectura de directorios de archivos

```
media/
  documentos/
    1_borrador.docx          # Documento Word generado (con placeholders reemplazados)
    1_firmado.docx          # Documento Word con firma incrustrada
    1_final.pdf             # PDF final generado
    2_borrador.docx
    ...
  firmas/
    firma_usuario_1.png     # Imagen de firma del usuario 1
    firma_usuario_2.png
    ...
  plantillas/
    plantilla_resolucion.docx   # Plantilla con {{campo1}}, {{campo2}}, etc.
    plantilla_circular.docx
    ...
```

---

## Notas técnicas

### Placeholders en plantillas
Las plantillas deben usar formato **{{nombre_campo}}** para los placeholders. docxtpl se encargará de reemplazarlos automáticamente.

### LibreOffice
Para generar PDF, el sistema requiere **LibreOffice instalado**. Se detecta automáticamente en:
- **Windows**: C:\Program Files\LibreOffice\program\soffice.exe
- **Linux**: /usr/bin/libreoffice
- **macOS**: /Applications/LibreOffice.app

Si no encuentra LibreOffice, la conversión a PDF fallaará gracefully (sin crash).

### Firmas digitales
- Las imágenes de firma se suben desde el perfil de usuario (futura implementación)
- Se almacenan en `/media/firmas/firma_usuario_{id}.png`
- Al firmar, se incrustan automáticamente en el documento

### Seguridad
- Todos los endpoints validan permisos según rol (modulo 6: documentos)
- Solo usuarios autenticados pueden ver/crear/modificar documentos
- La firma incrustra datos del usuario actual (usuario_token.id_usuario)

---

## Mejoras futuras

1. **Tabla de observaciones**: Almacenar observaciones de devoluciones
2. **Gestión de firmas de usuarios**: Pantalla para subir/editar imagen de firma
3. **Búsqueda avanzada**: Filtros por fecha, usuario, consecutivo
4. **Auditoría**: Log de cambios de estado con usuario y timestamp
5. **Notificaciones**: Alertar cuando documento llega a etapa de revisión
6. **Flujos personalizados**: Permitir customizar estados según tipo de documento
7. **Validación de campos**: Campos requeridos, tipos de dato específicos
8. **Vista previa de Word**: Mostrar vista previa antes de finalizar
9. **Descarga en lote**: Descargar múltiples documentos
10. **Integración con firma electrónica**: Firma digital en el PDF

