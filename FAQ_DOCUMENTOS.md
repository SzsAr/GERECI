# FAQ - Módulo Documentos GERECI

## Preguntas frecuentes

### General

**P: ¿Cuál es el flujo principal de un documento?**  
R: BORRADOR → (Revisión jurídica si aplica) → Revisión gerencial → Firmas → Finalización → FINALIZADO. En cualquier revisión se puede devolver con observaciones.

**P: ¿Qué requiere LibreOffice?**  
R: Para generar PDFs. Si no está instalado, los documentos se generarán en Word pero el PDF no se creará (el sistema no falla).

**P: ¿Cuándo se asigna el consecutivo?**  
R: Automáticamente cuando el documento llega a estado FINALIZADO. No se puede asignar manualmente.

**P: ¿Se pueden editar los campos después de crear el documento?**  
R: En la versión 1.0, los campos se establecen al generar. Edición de campos es mejora futura.

---

### Plantillas

**P: ¿Cómo se definen los campos en una plantilla?**  
R: Usando placeholders `{{nombre_campo}}` en el Word. docxtpl automáticamente los reemplazará.

**P: ¿Puedo tener espacios en los nombres de campos?**  
R: No recomendado. Usar nombres sin espacios: `{{nombre_usuario}}` en vez de `{{nombre usuario}}`.

**P: ¿Qué pasa si una plantilla no tiene placeholders?**  
R: El documento se genera igual, sin cambios (útil para plantillas fijas).

**P: ¿Soporta imágenes en las plantillas?**  
R: Sí, las imágenes existentes se preservan. docxtpl solo reemplaza texto en placeholders.

**P: ¿Puedo tener tablas con placeholders?**  
R: Sí, docxtpl soporta placeholders dentro de tablas. La firma se añade al final del documento.

---

### Firmas

**P: ¿Cómo se sube la imagen de firma?**  
R: Futura funcionalidad. Por ahora, colocar el archivo `firma_usuario_{id}.png` en `/media/firmas/`.

**P: ¿En qué posición se incrustra la firma?**  
R: Al final del documento, con imagen encima, nombre en negrita y cargo en gris.

**P: ¿Qué formato debe tener la imagen de firma?**  
R: PNG recomendado. Se redimensiona a 1.5 pulgadas de ancho. Soporta JPG y otros formatos que Pillow pueda leer.

**P: ¿Se incrustan múltiples firmas?**  
R: Sí, cada vez que alguien "aprueba y firma", se incrustra su firma al documento (acumulativo).

**P: ¿Qué pasa si el usuario no tiene imagen de firma?**  
R: Se incrustra igual nombre + cargo sin imagen. El sistema no falla.

---

### Estados y transiciones

**P: ¿Por qué algunos tipos de documento van a jurídica?**  
R: Porque `tipos_documentos.requiere_juridica = 1`. Resoluciones generalmente requieren revisión legal.

**P: ¿Puedo cambiar el flujo de estados?**  
R: La lógica está en `crud_documentos.obtener_transiciones_validas()`. Se puede customizar según necesidad.

**P: ¿Se puede devolver un documento desde cualquier estado?**  
R: Solo desde EN_REVISION_JURIDICA y EN_REVISION_GERENCIAL. Desde otros estados no hay botón de devolución.

**P: ¿Qué significa PENDIENTE_FINALIZACION?**  
R: Estado intermedio antes de FINALIZADO. Representa que el documento está listo pero aún no tiene consecutivo ni PDF.

**P: ¿Puedo saltar estados?**  
R: No, las transiciones están validadas. Si intenta saltar, el sistema retorna error 400.

---

### Documentos generados

**P: ¿Dónde se guardan los archivos generados?**  
R: En `/backend/media/documentos/`. Sirven desde `/static/documentos/`.

**P: ¿Cuántos Worddocumentos se generan por documento?**  
R: Hasta 3:
  - `{id}_borrador.docx` (sin firma)
  - `{id}_firmado.docx` (con firma, puede ser múltiple)
  - `{id}_final.pdf` (solo si FINALIZADO)

**P: ¿Puedo descargar el documento en cualquier momento?**  
R: Sí, si tiene ruta_word_generado. El Word se actualiza cada vez que firma alguien.

**P: ¿Se puede descargar PDF antes de finalizar?**  
R: No, solo aparece el link cuando el documento está en FINALIZADO.

**P: ¿Qué tamaño máximo tiene un documento?**  
R: Word tiene límite de ~32 MB. Imágenes de firma deben ser pequeñas (<500 KB).

---

### Permisos y seguridad

**P: ¿Qué permisos necesito para crear documentos?**  
R: Permiso 'insertar' en módulo 6 (documentos).

**P: ¿Todos pueden ver todos los documentos?**  
R: Sí, si tienen permiso 'seleccionar'. Filtrado por usuario y estado disponible.

**P: ¿Se valida que el usuario puede firmar?**  
R: Se valida que tiene permiso 'actualizar'. El rol del usuario no se valida específicamente (mejora futura).

**P: ¿Se registra quién firmó?**  
R: El nombre del usuario se incrustra en el Word. Para auditoría, ver tabla observaciones (futura).

**P: ¿Puedo borrar documentos?**  
R: Solo si están en BORRADOR. Otros estados están protegidos.

---

### Frontend

**P: ¿Por qué no aparecen los botones de acción?**  
R: Hay dos razones:
  1. El documento no tiene transiciones válidas (llegó a FINALIZADO)
  2. Falta cargar transiciones desde `/transiciones` endpoint

**P: ¿Cómo se cargan los campos dinámicamente?**  
R: Al seleccionar una plantilla, `documentos.js` lee `campos_json` y pinta un input por cada campo.

**P: ¿Puedo multiseleccionar documentos?**  
R: No en versión 1.0. Descarga en lote es mejora futura.

**P: ¿Se actualiza la tabla automáticamente?**  
R: No. Se recarga al filtrar o crear/editar documento. Polling automático es mejora futura.

**P: ¿Funciona en móvil?**  
R: Bootstrap 5 es responsive, pero algunos campos pueden ser ajustados para mejor UX móvil.

---

### Errores comunes

**P: Error "Plantilla no encontrada"**  
R: Revisar que:
  1. Archivo existe en `/backend/media/plantillas/`
  2. Campo `ruta_almacenamiento` en BD tiene valor correcto
  3. Ruta no tiene `/static/` al buscar archivo local

**P: Error "LibreOffice no encontrado"**  
R: Instalar LibreOffice. En Windows buscar instalación automática en:
  - C:\Program Files\LibreOffice\program\soffice.exe
  - C:\Program Files (x86)\LibreOffice\program\soffice.exe

**P: Transición no permitida de X a Y**  
R: Revisar GET `/documentos/{id}/transiciones` para ver estados válidos desde el actual.

**P: Usuario no autorizado**  
R: Verificar en tabla `permisos`:
  - id_rol del usuario
  - modulo = 6 (documentos)
  - permiso = 'insertar', 'seleccionar', 'actualizar', 'borrar'

**P: Documento no se genera**  
R: Revisar:
  1. ¿Tengo permisos? (permiso 'actualizar')
  2. ¿Plantilla existe? (revisar BD)
  3. ¿Ruta correcta? (ruta_almacenamiento debe ser válida)
  4. ¿Espacio en disco? (en `/media/documentos/`)

---

### Observaciones y devoluciones

**P: ¿Se guardan las observaciones?**  
R: En versión 1.0 no. Se muestran en modal pero no se persisten. Futura: guardar en tabla observaciones.

**P: ¿Puedo devolver un documento múltiples veces?**  
R: Sí, el documento vuelve a BORRADOR cada vez y puede ser reenviado.

**P: ¿Se notifica al usuario cuando se devuelve?**  
R: No automáticamente. Futura: agregar notificaciones por email.

**P: ¿Dónde se ven las observaciones guardadas?**  
R: Futura funcionalidad. Ver tabla `observaciones` en BD.

---

### PDF y conversión

**P: ¿Por qué el PDF se genera solo al finalizar?**  
R: Porque el documento todavía tiene cambios. Una vez finalizado, está fijo y se genera el PDF para archivar.

**P: ¿Se puede cambiar a PDF antes?**  
R: Mejora futura: generar PDF en cualquier momento (para vista previa).

**P: ¿Qué pasa si LibreOffice tarda mucho?**  
R: Timeout de 30 segundos. Si tarda más, retorna error pero no crash.

**P: ¿Se puede usar convertapi en vez de LibreOffice?**  
R: Sí, mejora futura. Actualmente solo soporta CLI de LibreOffice.

**P: El PDF no tiene las firmas incrustradas**  
R: El PDF se genera desde el Word que ya tiene firmas incrustradas. Si las firmas no aparecen en Word, tampoco en PDF.

---

### Consecutivos

**P: ¿Cómo funciona la numeración?**  
R: Por tipo de documento. Cada tipo tiene su propia secuencia.
  - Circular Normativa: C-N-001, C-N-002, ...
  - Resolución: RES-001, RES-002, ...

**P: ¿Qué pasa si reinicio el servidor?**  
R: Nada. Los consecutivos están en `control_consecutivos` en BD. Se recuperan del último número.

**P: ¿Puedo resetear los consecutivos?**  
R: Sí, editando `control_consecutivos.ultimo_numero` en BD. Cuidado: no crear duplicados.

**P: ¿Puedo personalizar el formato del consecutivo?**  
R: Sí, editar `crud_documentos.asignar_consecutivo()` línea donde se genera el formato.

---

### Rendimiento

**P: ¿Cuántos documentos puede manejar?**  
R: Teoricamente ilimitado. Performance depende de:
  - Tamaño de archivos
  - Velocidad de disco
  - Performance de LibreOffice (conversión)

**P: ¿Cuánto tarda generar un documento?**  
R: Típicamente 0.5-1 segundo (docxtpl es muy rápido). Conversión a PDF tarda 2-5 segundos.

**P: ¿Se pueden generar documentos en paralelo?**  
R: Sí, cada petición es independiente. FastAPI maneja concurrencia automáticamente.

---

### Backup y recuperación

**P: ¿Se backupean los documentos Word/PDF?**  
R: No automáticamente. Están en `/media/documentos/`. Incluir en estrategia de backup.

**P: ¿Qué pasa si se borra un archivo Word?**  
R: Documento sigue existiendo en BD pero link de descarga estará roto. Es recuperable reenviando.

**P: ¿Se puede recuperar un documento eliminado?**  
R: Sí, si tiene backup de BD. Solo se puede eliminar BORRADORES.

---

## Contacto y soporte

Para problemas específicos no cubiertos aquí:
1. Revisar logs de FastAPI: `python main.py` en terminal
2. Revisar logs del navegador: F12 → Console
3. Revisar BD: Verificar datos en tabla `documentos`
4. Verificar permisos: Tabla `permisos`
5. Ejecutar GET `/documentos/{id}/transiciones` para debuguear estado

---

**Última actualización:** 24/01/2026
