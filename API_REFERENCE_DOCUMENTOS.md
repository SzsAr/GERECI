# API Reference - Documentos

## Base URL
```
http://localhost:8000
```

## Endpoints

### Obtener documentos
```
GET /documentos/?estado=BORRADOR&usuario_id=1
```
**Respuesta:**
```json
[
  {
    "id": 1,
    "id_tipo": 1,
    "id_plantilla": 1,
    "usuario_genera": 1,
    "asunto": "Circular sobre actualización",
    "consecutivo": null,
    "fecha_creacion": "2026-01-24T10:30:00",
    "fecha_emision": null,
    "ruta_word_generado": "/static/documentos/1_borrador.docx",
    "ruta_pdf_final": null,
    "estado": "BORRADOR",
    "tipo_nombre": "Circular Normativa",
    "plantilla_nombre": "Plantilla Circular",
    "usuario_nombre": "Admin User"
  }
]
```

### Obtener documento por ID
```
GET /documentos/{documento_id}
```

### Crear documento
```
POST /documentos/create
Content-Type: application/json

{
  "id_tipo": 1,
  "id_plantilla": 1,
  "asunto": "Documento de prueba",
  "valores_campos": {
    "nombre": "Juan Pérez",
    "cargo": "Coordinador",
    "fecha": "24/01/2026"
  }
}
```
**Respuesta:**
```json
{
  "message": "Documento creado correctamente",
  "documento_id": 5,
  "estado": "BORRADOR"
}
```

### Generar Word desde plantilla
```
POST /documentos/{documento_id}/generar
```
**Respuesta:**
```json
{
  "message": "Documento Word generado correctamente",
  "ruta_word": "/static/documentos/5_borrador.docx"
}
```

### Firmar documento (cambiar estado + incrustar firma)
```
POST /documentos/{documento_id}/firmar
Content-Type: application/x-www-form-urlencoded

nuevo_estado=EN_REVISION_GERENCIAL
```
**Respuesta (estado intermedio):**
```json
{
  "message": "Firma incrustrada y estado actualizado",
  "nuevo_estado": "EN_REVISION_GERENCIAL",
  "ruta_word": "/static/documentos/5_firmado.docx"
}
```

**Respuesta (FINALIZADO):**
```json
{
  "message": "Documento finalizado correctamente",
  "nuevo_estado": "FINALIZADO",
  "ruta_word": "/static/documentos/5_firmado.docx",
  "ruta_pdf": "/static/documentos/5_final.pdf",
  "consecutivo": "C-N-001"
}
```

### Cambiar estado (endpoint alternativo)
```
PUT /documentos/{documento_id}/estado
Content-Type: application/json

{
  "nuevo_estado": "EN_REVISION_JURIDICA",
  "descripcion_cambio": "Enviado a revisión jurídica"
}
```

### Actualizar documento
```
PUT /documentos/{documento_id}
Content-Type: application/json

{
  "asunto": "Documento actualizado",
  "valores_campos": {
    "nombre": "Carlos López"
  }
}
```

### Obtener transiciones válidas
```
GET /documentos/{documento_id}/transiciones
```
**Respuesta:**
```json
{
  "estado_actual": "BORRADOR",
  "transiciones_validas": ["EN_REVISION_JURIDICA"]
}
```

### Eliminar documento (solo BORRADOR)
```
DELETE /documentos/{documento_id}
```
**Respuesta:**
```json
{
  "message": "Documento eliminado correctamente"
}
```

---

## Estados y transiciones

### Sin revisión jurídica (ej: Circular Normativa)
```
BORRADOR
  ↓
EN_REVISION_GERENCIAL
  ↓
APROBADO_GERENCIA
  ↓
FIRMADO
  ↓
PENDIENTE_FINALIZACION
  ↓
FINALIZADO
```

### Con revisión jurídica (ej: Resolución)
```
BORRADOR
  ↓
EN_REVISION_JURIDICA
  ↓
APROBADO_JURIDICA
  ↓
EN_REVISION_GERENCIAL
  ↓
APROBADO_GERENCIA
  ↓
FIRMADO
  ↓
PENDIENTE_FINALIZACION
  ↓
FINALIZADO
```

### Devoluciones
```
EN_REVISION_JURIDICA → DEVUELTO_JURIDICA → BORRADOR
EN_REVISION_GERENCIAL → DEVUELTO_GERENCIA → BORRADOR
```

---

## Descargas de archivos

### Word generado
```
GET /static/documentos/{documento_id}_borrador.docx
```

### Word firmado
```
GET /static/documentos/{documento_id}_firmado.docx
```

### PDF final (solo si FINALIZADO)
```
GET /static/documentos/{documento_id}_final.pdf
```

---

## Errores comunes

### 403 Unauthorized
```json
{
  "detail": "Usuario no autorizado para crear documentos"
}
```
**Solución:** Verificar permisos en tabla permisos (modulo 6)

### 404 Not Found
```json
{
  "detail": "Documento no encontrado"
}
```
**Solución:** Verificar ID del documento

### 400 Transición inválida
```json
{
  "detail": "Transición no permitida de BORRADOR a FINALIZADO. Estados válidos: ['EN_REVISION_JURIDICA']"
}
```
**Solución:** Seguir flujo de estados

---

## Headers requeridos

```
Authorization: Bearer <token_jwt>
Content-Type: application/json  (para POST/PUT con JSON)
Content-Type: application/x-www-form-urlencoded  (para POST /firmar)
```

---

## Filtros disponibles

### GET /documentos/
- `estado`: BORRADOR, EN_REVISION_JURIDICA, EN_REVISION_GERENCIAL, APROBADO_JURIDICA, APROBADO_GERENCIA, FIRMADO, PENDIENTE_FINALIZACION, FINALIZADO
- `usuario_id`: ID del usuario que creó el documento

**Ejemplo:**
```
GET /documentos/?estado=FINALIZADO&usuario_id=2
```
