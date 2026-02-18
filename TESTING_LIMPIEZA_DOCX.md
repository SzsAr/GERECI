# 🧪 Testing - Limpieza automática de archivos .docx

## Flujos testeables

### Escenario 1: Documento devuelto y eliminado ✅

**Objetivo:** Validar que se elimine `.docx` cuando se devuelve y luego se elimina el documento

**Pasos:**
1. Crear documento → estado BORRADOR
2. Generar Word → `POST /{documento_id}/generar-word`
   - Verificar: `media/documentos/` tiene `.docx`
3. Cambiar estado a EN_REVISION_JURIDICA → `PUT /{documento_id}/estado`
   - Estado: `EN_REVISION_JURIDICA`
4. **Devolver a DEVUELTO_JURIDICA** → `PUT /{documento_id}/estado`
   - Estado: `DEVUELTO_JURIDICA`
   - Agregar observaciones: "Necesita correcciones"
   - ✅ VALIDAR: `media/documentos/` NO tiene `.docx` (eliminado al devolver)
   - ✅ VALIDAR: Logs registran eliminación exitosa
5. **Eliminar documento** → `DELETE /{documento_id}`
   - ✅ Estado ahora permite DEVUELTO_JURIDICA
   - ✅ VALIDAR: Elimina exitosamente
   - ✅ VALIDAR: BD no tiene el documento

**Resultado esperado:**
- `.docx` se elimina cuando se devuelve
- Documento en estado DEVUELTO puede eliminarse directamente
- No necesita volver a BORRADOR
- Logs muestran: "Archivos .docx del documento X eliminados al devolver"

---

### Escenario 2: Documento finalizado ✅

**Objetivo:** Validar que se elimine `.docx` cuando se finaliza (y genera PDF)

**Pasos:**
1. Crear documento → BORRADOR
2. Generar Word → `POST /{documento_id}/generar-word`
   - `.docx` existe en `media/documentos/`
3. Enviar a revisión y aprobar completamente hasta APROBADO_GERENCIA
4. **Pasar a FINALIZADO** → `PUT /{documento_id}/estado`
   - Estado: `FINALIZADO`
   - Sistema genera PDF automáticamente
   - ✅ VALIDAR: `media/documentos/` tiene PDF pero NO `.docx`
   - ✅ VALIDAR: Logs muestran "Archivos .docx del documento X eliminados"

**Resultado esperado:**
- PDF se genera y queda guardado
- `.docx` se eliminan después de generar PDF
- Solo queda el PDF en el servidor

---

### Escenario 3: Eliminación de BORRADOR ✅

**Objetivo:** Validar limpieza cuando se elimina un documento

**Pasos:**
1. Crear documento → BORRADOR
2. Generar Word → `POST /{documento_id}/generar-word`
   - `.docx` existe
3. **Eliminar documento** → `DELETE /{documento_id}`
   - ✅ VALIDAR: BD no tiene el documento
   - ✅ VALIDAR: `media/documentos/` NO tiene `.docx`
   - ✅ VALIDAR: Logs muestran "Archivos .docx del documento X eliminados"

**Resultado esperado:**
- Documento se elimina de BD
- `.docx` se elimina del servidor
- Limpieza completa

---

### Escenario BONO: Validar que no se puede eliminar en otros estados

**Objetivo:** Confirmar que solo BORRADOR y DEVUELTO se pueden eliminar

**Pasos:**
```bash
# Intentar eliminar documento en EN_REVISION_JURIDICA (debe fallar)
DELETE /documentos/{doc_id}
# Response esperado: 400 "Solo se pueden eliminar documentos en estado BORRADOR o DEVUELTO"

# Intentar eliminar documento en APROBADO_GERENCIA (debe fallar)
DELETE /documentos/{doc_id}
# Response esperado: 400 "Solo se pueden eliminar documentos en estado BORRADOR o DEVUELTO"

# Intentar eliminar documento FINALIZADO (debe fallar)
DELETE /documentos/{doc_id}
# Response esperado: 400 "Solo se pueden eliminar documentos en estado BORRADOR o DEVUELTO"
```

**Resultado esperado:**
- ✅ Solo BORRADOR, DEVUELTO_JURIDICA, DEVUELTO_GERENCIA se pueden eliminar
- ✅ Otros estados retornan error 400 con mensaje claro
- ✅ BD se protege contra eliminación accidental de documentos en revisión/aprobación

---

### Testing desde SQL
```sql
-- Crear documento de prueba
INSERT INTO documentos (
    id_tipo, id_plantilla, usuario_genera,
    Asunto, estado
) VALUES (1, 1, 1, 'Documento Test Limpieza', 'BORRADOR');

-- Obtener ID generado
SELECT LAST_INSERT_ID() AS doc_id;

-- Consultar estado
SELECT id, estado, ruta_word_generado, ruta_pdf_final 
FROM documentos 
WHERE id = <doc_id>;

-- Verificar cambios de estado
SELECT id, estado
FROM documentos 
WHERE id = <doc_id>
ORDER BY DATE(fecha_creacion) DESC;
```

---

## Verificación en filesystem

### Antes de prueba
```powershell
# Verificar carpeta de documentos
ls C:\GERECI\media\documentos\
```

### Después de devolver/finalizar/eliminar
```powershell
# Debería estar vacío o sin el .docx del documento
ls C:\GERECI\media\documentos\
```

---

## Logs a buscar

### Limpieza correcta
```
INFO: Archivos .docx del documento 123 eliminados al devolver
INFO: Archivos .docx del documento 123 eliminados
```

### Si hay errores
```
WARNING: No se pudieron eliminar archivos .docx del documento 123: [error]
```

---

## Checklist de testing

### Flujo 1 - Devolución y eliminación
- [ ] Documento se crea en BORRADOR
- [ ] `.docx` se genera correctamente
- [ ] Documento se devuelve (DEVUELTO_JURIDICA/GERENCIA)
- [ ] `.docx` desaparece de `media/documentos/` (eliminado al devolver)
- [ ] Logs registran eliminación al devolver
- [ ] Documento en estado DEVUELTO se puede eliminar (nueva funcionalidad)
- [ ] BD se actualiza correctamente
- [ ] No hay `.docx` leftovers en disco

### Flujo 2 - Finalización
- [ ] Documento fluye hasta APROBADO_GERENCIA
- [ ] Estado cambia a FINALIZADO
- [ ] PDF se genera
- [ ] `.docx` se elimina de `media/documentos/`
- [ ] PDF permanece en `media/documentos/`
- [ ] Logs registran eliminación
- [ ] Consecutivo se asigna correctamente

### Flujo 3 - Eliminación desde BORRADOR
- [ ] Documento en BORRADOR con `.docx` generado
- [ ] DELETE devuelve success
- [ ] BD no tiene el documento
- [ ] `media/documentos/` no tiene `.docx`
- [ ] Logs registran eliminación

### Flujo 4 - Validación de restricciones (NUEVO)
- [ ] No se puede eliminar documento en EN_REVISION_JURIDICA (error 400)
- [ ] No se puede eliminar documento en APROBADO_GERENCIA (error 400)
- [ ] No se puede eliminar documento en FINALIZADO (error 400)
- [ ] Se puede eliminar documento en BORRADOR (success)
- [ ] Se puede eliminar documento en DEVUELTO_JURIDICA (success - NUEVA)
- [ ] Se puede eliminar documento en DEVUELTO_GERENCIA (success - NUEVA)

---

## Endpoints para testing

```bash
# Crear documento
POST /documentos/create
{
  "id_tipo": 1,
  "id_plantilla": 1,
  "asunto": "Test limpieza .docx",
  "valores_campos": {}
}

# Generar Word
POST /documentos/{doc_id}/generar-word

# Cambiar estado a revisión
PUT /documentos/{doc_id}/estado
{
  "nuevo_estado": "EN_REVISION_JURIDICA"
}

# Devolver
PUT /documentos/{doc_id}/estado
{
  "nuevo_estado": "DEVUELTO_JURIDICA",
  "descripcion_cambio": "Necesita correcciones"
}

# Finalizar
PUT /documentos/{doc_id}/estado
{
  "nuevo_estado": "FINALIZADO"
}

# Eliminar
DELETE /documentos/{doc_id}
```

---

## Casos edge case

1. **Devolver múltiples veces**
   - Crear → Generar → Devolver → Generar nuevo → Devolver
   - ✅ Debe eliminar solo el `.docx` actual

2. **Error en eliminación**
   - Simular archivo bloqueado/permisos
   - ✅ Documento debe finalizarse/devolverse igual
   - ✅ Logs registran warning

3. **Archivo ya eliminado**
   - Intentar eliminar documento sin `.docx`
   - ✅ No debe fallar, logs registran intento

