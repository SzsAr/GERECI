# Implementación: Limpieza automática de archivos .docx

## 📌 Objetivo
Eliminar automáticamente los archivos `.docx` temporales cuando un documento se finaliza o se elimina, para evitar sobrecarga de archivos en el servidor.

## ✅ Cambios realizados

### 1. `backend/app/utils/document_generator.py` ✨ NUEVA FUNCIÓN

**Función agregada:** `eliminar_archivo_documento()`

```python
def eliminar_archivo_documento(documento_id: int, ruta_relativa: Optional[str] = None) -> bool:
    """
    Eliminar archivo .docx de un documento de la carpeta media/documentos.
    Si no se proporciona ruta_relativa, intenta eliminar los archivos conocidos.
    
    Args:
        documento_id: ID del documento
        ruta_relativa: Ruta relativa del archivo (/static/documentos/...)
        
    Returns:
        True si se eliminó, False si no encontró archivo
    """
```

**Características:**
- Expone la ruta específica del archivo si se proporciona
- Intenta eliminar patrones comunes de nombres (`{id}_borrador.docx`, `{id}_final.docx`, etc.)
- Manejo seguro de errores: registra advertencias pero no interrumpe el flujo
- Retorna `bool` para indicar si se eliminó algún archivo

### 2. `backend/app/router/documentos.py` ✏️

#### 2.1 Import actualizado
```python
from app.utils.document_generator import (
    generar_word_desde_plantilla,
    incrustar_firma,
    convertir_word_a_pdf,
    eliminar_archivo_documento,  # ← NUEVO
    DOCUMENTOS_DIR
)
```

#### 2.2 Endpoint: `PUT /{documento_id}/estado` - Cambio a FINALIZADO

**Nuevo comportamiento:** Cuando se finaliza un documento (FINALIZADO) y se genera PDF exitosamente:

```python
if ruta_pdf:
    crud_documentos.update_documento(
        db,
        documento_id,
        DocumentoUpdate(ruta_pdf_final=ruta_pdf)
    )
    
    # Eliminar archivos .docx para liberar espacio
    try:
        eliminar_archivo_documento(documento_id)
        logger.info(f"Archivos .docx del documento {documento_id} eliminados")
    except Exception as e:
        logger.warning(f"No se pudieron eliminar archivos .docx del documento {documento_id}: {e}")
    
    return {
        "message": "Documento finalizado y PDF generado correctamente",
        "nuevo_estado": "FINALIZADO",
        "consecutivo": consecutivo,
        "ruta_word": ruta_word_final,  # ← Información histórica
        "ruta_pdf": ruta_pdf
    }
```

**Puntos clave:**
- Los `.docx` se eliminan SOLO después de generar PDF exitosamente
- Permite que el frontend reporte la ruta en el response (para referencia histórica)
- Los logs registran si la eliminación fue exitosa o falló
- No interrumpe el flujo si hay error en eliminación

#### 2.3 Endpoint: `DELETE /{documento_id}` - Eliminar documento

**Nuevo comportamiento:** Cuando se elimina un documento en estado BORRADOR:

```python
# Obtener ruta del Word generado para eliminar después
ruta_word = documento.get('ruta_word_generado') if isinstance(documento, dict) else documento.ruta_word_generado

# Eliminar documento de la base de datos
from sqlalchemy import text
query = text("DELETE FROM documentos WHERE id = :documento_id")
db.execute(query, {"documento_id": documento_id})
db.commit()

# Eliminar archivos .docx asociados
try:
    eliminar_archivo_documento(documento_id, ruta_word)
    logger.info(f"Archivos .docx del documento {documento_id} eliminados")
except Exception as e:
    logger.warning(f"No se pudieron eliminar archivos .docx del documento {documento_id}: {e}")

return {"message": "Documento eliminado correctamente"}
```

**Puntos clave:**
- Se obtiene la ruta del Word ANTES de borrar de BD
- Se elimina de BD primero, luego se intenta eliminar archivos
- Manejo robusto de errores: no interrumpe si falla eliminación de archivos
- Intentará eliminar la ruta específica y patrones comunes

---

## 📊 Beneficios

| Aspecto | Impacto |
|--------|--------|
| **Espacio en servidor** | ✅ Reduce significativamente (sin .docx temporales) |
| **Mantenimiento** | ✅ Automático (no requiere limpieza manual) |
| **Confiabilidad** | ✅ Mantiene PDF (el archivo final) |
| **Rendimiento** | ✅ Menos archivos en disco = I/O más rápido |
| **Tolerancia a fallos** | ✅ Si falla eliminación, documento igual queda finalizado |

---

## 🔄 Flujo de eliminación

```
FINALIZAR DOCUMENTO
    ↓
├─ Validar permisos
├─ Cambiar estado a FINALIZADO
├─ Asignar consecutivo (trigger)
├─ Generar WORD final con firmas
├─ Generar PDF
├─ SI PDF exitoso:
│   ├─ Guardar ruta PDF en BD
│   ├─ Eliminar .docx de media/documentos ✨ NUEVO
│   └─ Retornar success
└─ SI PDF falló: documento queda FINALIZADO sin PDF

ELIMINAR DOCUMENTO (BORRADOR)
    ↓
├─ Verificar permisos
├─ Verificar estado = BORRADOR
├─ Obtener ruta de .docx
├─ Eliminar de BD
├─ Eliminar .docx de media/documentos ✨ NUEVO
└─ Retornar success
```

---

## 🧪 Testing recomendado

1. **Caso: Finalizar documento**
   - ✅ Crear documento → generar Word → finalizar
   - ✅ Verificar que PDF se genera
   - ✅ Verificar que `media/documentos/` NO tiene .docx del documento
   - ✅ Verificar que logs registran eliminación

2. **Caso: Eliminar documento en BORRADOR**
   - ✅ Crear documento → generar Word
   - ✅ Eliminar documento
   - ✅ Verificar que BD no tiene el documento
   - ✅ Verificar que `media/documentos/` NO tiene .docx del documento

3. **Caso: Error en eliminación de archivo**
   - ✅ Finalizar/eliminar documento
   - ✅ Verificar que DB actualiza correctamente aunque falle eliminación
   - ✅ Verificar logs de advertencia

---

## 📝 Notas técnicas

- **Idempotencia:** La función `eliminar_archivo_documento()` es segura para llamar múltiples veces
- **Seguridad:** Solo intenta eliminar arquivos `.docx` en la carpeta `media/documentos`
- **Logging:** Todos los intentos de eliminación se registran (info/warning según resultado)
- **Compatibilidad:** Soporta rutas web (`/static/...`) y rutas físicas
