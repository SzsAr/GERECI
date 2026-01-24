# Cambios realizados - Módulo Documentos GERECI

## 📋 Resumen ejecutivo
Se implementó completamente el módulo de Documentos con flujo de creación → revisiones (jurídica/gerencia) → firmas → finalización con generación de PDF y asignación automática de consecutivos.

---

## 📁 Archivos modificados

### Backend

#### 1. `backend/app/schemas/documentos.py` ✏️
**Cambios:**
- Agregó campo `valores_campos: Optional[Dict[str, Any]]` a `DocumentoCreate`
- Agregó campo `valores_campos` a `DocumentoUpdate`
- Agregó campos `tipo_nombre`, `plantilla_nombre`, `usuario_nombre` a `DocumentoOut` (para JOINs)

#### 2. `backend/app/crud/documentos.py` ✏️
**Cambios:**
- Mejoró `get_documento_by_id()`: Añadió JOINs con tipos_documentos, plantillas, usuarios
- Mejoró `get_all_documentos()`: Añadió JOINs con tipos_documentos, plantillas, usuarios
- Mejoró `cambiar_estado_documento()`: Valida transiciones antes de cambiar
- **NUEVA función:** `obtener_transiciones_validas()`: Retorna estados válidos según estado actual y requiere_juridica
- Mejoró `necesita_revision_juridica()`: Ahora retorna bool correctamente

#### 3. `backend/app/router/documentos.py` ✏️
**Cambios:**
- Añadió imports para archivos, FormData, rutas
- **NUEVO endpoint:** `POST /documentos/{id}/generar`
  - Genera Word desde plantilla con docxtpl
  - Reemplaza {{campo}} con valores_campos
  - Guarda en `/static/documentos/{id}_borrador.docx`
  
- **NUEVO endpoint:** `POST /documentos/{id}/firmar`
  - Incrustra firma (imagen + nombre + cargo) en Word
  - Cambia estado validando transiciones
  - Si FINALIZADO: genera PDF + asigna consecutivo
  - Retorna rutas de Word y PDF
  
- **NUEVO endpoint:** `GET /documentos/{id}/transiciones`
  - Retorna estados válidos desde el estado actual
  - Usado por frontend para mostrar botones de acción

#### 4. `backend/app/utils/document_generator.py` 🆕
**ARCHIVO NUEVO**

Contiene utilidades para:
- **`generar_word_desde_plantilla()`**: Renderiza plantilla Word con docxtpl
- **`incrustar_firma()`**: Añade imagen + nombre + cargo al Word
- **`convertir_word_a_pdf()`**: Convierte usando LibreOffice CLI
- **`guardar_firma_usuario()`**: Almacena imagen de firma en `/static/firmas/`
- **`_obtener_ruta_libreoffice()`**: Detecta LibreOffice automáticamente

#### 5. `backend/app/utils/__init__.py` 🆕
**ARCHIVO NUEVO**
- Inicializa paquete utils

---

### Frontend

#### 1. `frontend/documentos.html` 🆕
**ARCHIVO NUEVO**

Contiene:
- **Tabla de documentos** con filtros (estado, asunto)
- **Modal "Nuevo documento"**
  - Selecciona tipo + plantilla
  - Pinta inputs dinámicos basados en campos_json
  - Genera Word
  
- **Modal "Ver documento"**
  - Muestra detalles y estado
  - Descargas Word/PDF
  - Botones "Aprobar y Firmar" / "Devolver"
  - Caja de observaciones para devoluciones

#### 2. `frontend/js/documentos.js` 🆕
**ARCHIVO NUEVO**

Contiene:
- **`initDocumentosPage()`**: Inicialización
- **`cargarDocumentos()`**: GET /documentos con filtros
- **`cargarTiposYPlantillas()`**: Carga selectores
- **`generarDocumento()`**: POST /create + POST /generar
- **`verDocumento(docId)`**: Abre modal con detalles
- **`firmarDocumento()`**: POST /firmar
- **`devolverDocumento()`**: Devuelve a BORRADOR con observaciones
- **`agregarCampoInput()`**: UI dinámica para campos
- Funciones de binding de eventos

#### 3. `frontend/js/layout.js` ✏️
**Cambios:**
- Cambió link de Documentos de `href="#"` a `href="./documentos.html"`

---

## 📊 Librerías instaladas

```
docxtpl==0.20.2          # Renderizar plantillas Word
python-docx==1.2.0       # Manipular .docx
Pillow==12.1.0           # Procesar imágenes de firmas
lxml==6.0.2              # Dependencia de python-docx
```

**Instaladas vía:** `pip install docxtpl python-docx Pillow`

---

## 🗂️ Estructura de archivos generados

```
media/
  documentos/
    {documento_id}_borrador.docx     ← Generado por POST /generar
    {documento_id}_firmado.docx      ← Generado por POST /firmar (con firma)
    {documento_id}_final.pdf         ← Generado al llegar a FINALIZADO
    
  firmas/
    firma_usuario_{usuario_id}.png   ← Subidas por usuario (futura: subir imagen)
    
  plantillas/
    plantilla_resolucion.docx        ← Plantillas maestras con {{campo}}
    plantilla_circular.docx
    ...
```

---

## 🔄 Flujo de datos

### Crear documento
```
Frontend (formulario)
  ↓
POST /documentos/create (asunto, tipo, plantilla, valores_campos)
  ↓ (Backend crea en BD en estado BORRADOR)
  ↓
POST /documentos/{id}/generar (renderiza Word con docxtpl)
  ↓ (Guarda en /media/documentos/{id}_borrador.docx)
  ↓
Frontend actualiza tabla con nuevo documento
```

### Firmar documento
```
Frontend (modal documento, clic "Aprobar y Firmar")
  ↓
POST /documentos/{id}/firmar (nuevo_estado)
  ↓ (Backend valida transición)
  ↓
Incrustra firma + nombre + cargo
  ↓ (Guarda en /media/documentos/{id}_firmado.docx)
  ↓
Si nuevo_estado == FINALIZADO:
  → Genera PDF
  → Asigna consecutivo
  → Actualiza fecha_emision
  ↓
Frontend descarga Word o PDF
```

---

## ✅ Funcionalidades implementadas

### Backend
- [x] Creación de documentos en BORRADOR
- [x] Generación automática de Word desde plantilla
- [x] Reemplazo de placeholders {{campo}}
- [x] Incrusión de firmas (imagen + nombre + cargo)
- [x] Validación de transiciones de estado
- [x] Flujos diferenciados (con/sin revisión jurídica)
- [x] Generación de PDF al finalizar
- [x] Asignación automática de consecutivos
- [x] JOINs en listados (tipo_nombre, plantilla_nombre, usuario_nombre)
- [x] Endpoints: /create, /generar, /firmar, /transiciones, /estado

### Frontend
- [x] Pantalla de Documentos con tabla
- [x] Filtros por estado y búsqueda por asunto
- [x] Modal crear documento con campos dinámicos
- [x] Modal ver documento con detalles
- [x] Descargas Word/PDF
- [x] Botones de acción (Aprobar, Devolver) según estado
- [x] Observaciones en devoluciones
- [x] Visualización de estados con badges de colores
- [x] Link en sidebar hacia documentos.html

---

## ⚙️ Configuración requerida

### Base de datos
- Tablas creadas: documentos, tipos_documentos, plantillas, usuarios, control_consecutivos
- FK correctas entre tablas
- Permisos configurados en tabla permisos (modulo 6: documentos)

### Servidor
- FastAPI en ejecución
- Carpeta `/media/documentos/` con permisos de escritura
- Carpeta `/media/firmas/` con permisos de escritura
- LibreOffice instalado (opcional, para PDF)

### Frontend
- Archivos HTML/JS en carpeta `/frontend/`
- `api.js` con `API_BASE` correctamente configurado
- `layout.js` para navbar y sidebar

---

## 🧪 Testing

Ver `GUIA_PRUEBA_DOCUMENTOS.md` para:
- Pasos para crear plantilla de prueba
- Crear primer documento
- Flujo completo con jurídica
- Prueba de devoluciones
- Troubleshooting

---

## 📝 Notas

- **Placeholders en Word:** Usar formato `{{nombre_campo}}` (con llaves dobles)
- **Estados válidos:**
  - Con jurídica: BORRADOR → EN_REVISION_JURIDICA → APROBADO_JURIDICA → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → PENDIENTE_FINALIZACION → FINALIZADO
  - Sin jurídica: BORRADOR → EN_REVISION_GERENCIAL → APROBADO_GERENCIA → FIRMADO → PENDIENTE_FINALIZACION → FINALIZADO
- **Consecutivos:** Se asignan automáticamente al pasar a FINALIZADO (formato: CODIGO-NUMERO, ej: RES-001)
- **PDF:** Se genera automáticamente desde Word al finalizar (requiere LibreOffice)

---

**Fecha de conclusión:** 24/01/2026  
**Estado:** ✅ Listo para pruebas
