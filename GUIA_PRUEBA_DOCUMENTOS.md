# Guía de prueba - Módulo Documentos GERECI

## Requisitos previos

1. **Base de datos activa** con tablas creadas:
   - documentos
   - tipos_documentos
   - plantillas
   - usuarios
   - control_consecutivos
   - observaciones (opcional para registrar devoluciones)

2. **LibreOffice instalado** (para conversión Word → PDF)
   - Windows: Descargar de https://www.libreoffice.org/download/
   - Linux: `sudo apt-get install libreoffice`
   - macOS: Descargar .dmg de sitio oficial

3. **Venv activado** con librerías instaladas:
   ```bash
   cd "RUTA_DEL_PROYECTO"
   .\venv\Scripts\Activate.ps1  # Windows
   # source venv/bin/activate  # Linux/macOS
   ```

## Pasos para probar

### 1. Crear una plantilla de prueba

1. Abrir Word/LibreOffice Writer
2. Crear documento simple con texto y placeholders:
   ```
   DOCUMENTO: {{tipo_documento}}
   
   ASUNTO: {{asunto}}
   
   CREADO POR: {{usuario}}
   
   CONTENIDO:
   {{contenido}}
   
   Fecha: {{fecha}}
   ```
3. Guardar como `/backend/media/plantillas/plantilla_prueba.docx`
4. En la pantalla de Administración → Plantillas:
   - Crear nueva plantilla
   - Nombre: "Plantilla Prueba"
   - Tipo: Circular Normativa (o Resolución si requiere jurídica)
   - Subir archivo
   - Campos: tipo_documento, asunto, usuario, contenido, fecha

### 2. Iniciar servidor backend

```bash
cd backend
python main.py
```

El servidor estará en `http://localhost:8000`

### 3. Acceder a frontend

1. Abrir `http://localhost:8000/static/frontend/index.html` (o `file:///...` en local)
2. Login con credenciales de admin
3. Ir a "Documentos" en sidebar

### 4. Crear primer documento

1. Clic en "Nuevo documento"
2. Llenar:
   - Asunto: "Prueba de documento"
   - Tipo: "Circular Normativa"
   - Plantilla: "Plantilla Prueba"
3. Completar campos:
   - tipo_documento: "Circular"
   - usuario: "Usuario Prueba"
   - contenido: "Contenido de prueba"
   - fecha: "24/01/2026"
4. Clic "Generar documento"
   - Sistema crea documento en BORRADOR
   - Genera Word con placeholders reemplazados
   - Guardado en `/static/documentos/1_borrador.docx`

### 5. Revisar documento

1. En tabla de documentos, clic en ícono "Ver" (documento #1)
2. Verificar:
   - Estado: BORRADOR
   - Link de descarga de Word funcionando
   - Botón "Aprobar y Firmar" visible

### 6. Firmar documento (sin requisito de jurídica)

1. En modal de documento, clic "Aprobar y Firmar"
2. Sistema:
   - Incrustra nombre de usuario + cargo al final del Word
   - Cambia estado a EN_REVISION_GERENCIAL (salto automático)
   - Guarda como `/static/documentos/1_firmado.docx`

### 7. Flujo completo (si se requiere jurídica)

1. Cambiar tipo de documento a "Resolución" (requiere_juridica = 1)
2. Crear nuevo documento con este tipo
3. Sistema enviará a EN_REVISION_JURIDICA primero
4. Login con usuario de jurídica:
   - Ver documento en estado EN_REVISION_JURIDICA
   - Clic "Aprobar y Firmar"
   - Estado → APROBADO_JURIDICA + firma incrustrada
5. Login con usuario de gerencia:
   - Ver documento en APROBADO_JURIDICA
   - Debe ir a EN_REVISION_GERENCIAL
   - Clic "Aprobar y Firmar"
   - Estado → APROBADO_GERENCIA
6. Último paso (FIRMADO):
   - Clic "Aprobar y Firmar"
   - Estado → PENDIENTE_FINALIZACION
7. Finalización:
   - Clic "Aprobar y Firmar" (último)
   - Sistema:
     - Crea PDF desde Word
     - Asigna consecutivo (RES-001, RES-002, etc.)
     - Actualiza fecha_emision
     - Documentopasa a FINALIZADO
   - Link de descarga PDF disponible

### 8. Prueba de devolución

1. Crear documento en estado EN_REVISION_GERENCIAL
2. Clic "Devolver"
3. Ingresar observaciones: "Revisar sintaxis"
4. Sistema devuelve a BORRADOR
5. Usuario original puede editar y reenvidar

## Verificaciones clave

✅ **POST /documentos/create**
- Crea documento en BORRADOR
- Retorna documento_id
- Checkear en DB: INSERT en tabla documentos

✅ **POST /documentos/{id}/generar**
- Carga plantilla Word
- Reemplaza {{campo}} con valores
- Guarda en `/media/documentos/{id}_borrador.docx`
- Actualiza ruta_word_generado en DB

✅ **GET /documentos/** (con JOINs)
- Retorna lista con tipo_nombre, plantilla_nombre, usuario_nombre
- Filtros por estado funcionando

✅ **GET /documentos/{id}/transiciones**
- Retorna estados válidos según el estado actual
- Valida si requiere_juridica

✅ **POST /documentos/{id}/firmar**
- Incrustra firma (imagen + nombre + cargo)
- Cambia estado (valida transición)
- Si FINALIZADO: genera PDF + asigna consecutivo
- Checkear archivos guardados en `/media/documentos/`

✅ **Links de descargas**
- Word: GET `/static/documentos/{id}_borrador.docx` (o _firmado.docx)
- PDF: GET `/static/documentos/{id}_final.pdf` (solo si FINALIZADO)

## Troubleshooting

### Error: "Plantilla no encontrada"
- Verificar que archivo está en `/backend/media/plantillas/`
- Ruta debe estar como `/static/plantillas/archivo.docx`

### Error: "LibreOffice no encontrado"
- Instalar LibreOffice
- Verificar PATH (Windows: buscar soffice.exe)
- Sistema continuará sin PDF (no crash)

### Documentos no se generan
- Verificar permisos en `/media/documentos/`
- Asegurarse de que la carpeta existe
- Logs de FastAPI mostrarán errores específicos

### Estado no cambia
- Verificar transiciones válidas: GET `/documentos/{id}/transiciones`
- Asegurarse de que estado actual está en la lista
- Verificar permisos del usuario (modulo 6)

## Datos de prueba recomendados

**Usuarios:**
- Admin (para crear documentos)
- Usuario jurídica (para revisar si requiere_juridica)
- Usuario gerencia (para revisar siempre)

**Tipos de documentos:**
- Circular Normativa (requiere_juridica = 0)
- Circular Informativa (requiere_juridica = 0)
- Resolución (requiere_juridica = 1)

**Roles:**
- Admin: permisos en todos los módulos
- Jurídico: permiso en documentos (seleccionar, actualizar)
- Gerencia: permiso en documentos (seleccionar, actualizar)

---

**Fecha de implementación:** 24/01/2026  
**Estado:** ✅ Operativo
