# Implementación Completada: Carga de Firmas para Usuarios

**Fecha:** 09 de Marzo 2026  
**Estado:** ✅ IMPLEMENTADO

---

## 📋 Resumen de Cambios

Se implementó la interfaz de carga de firmas de usuario en el **Panel de Administración**, permitiendo que solo el **superadmin** pueda subir/cambiar la firma de cualquier usuario.

### Archivos Modificados

#### 1. [frontend/admin.html](frontend/admin.html)
**Sección:** Modal de Usuario (líneas ~209-230)

**Cambios:**
- Agregado campo de upload de firma con validación de formatos
- Agregado preview de firma actual del usuario
- Agregado preview en tiempo real de la nueva firma a subir
- Información de restricciones: PNG, JPEG, WebP, máximo 100 KB

**HTML Agregado:**
```html
<div class="mb-3">
  <label class="form-label">Firma (Imagen de firma)</label>
  <div id="firma-preview-container" class="mb-2 d-none">
    <small class="text-muted d-block mb-2">Firma actual:</small>
    <img id="firma-preview" src="" alt="Firma" style="...">
  </div>
  <input type="file" class="form-control" id="usuario-firma" accept="image/png,image/jpeg,image/webp">
  <small class="text-muted d-block mt-2">Formatos: PNG, JPEG, WebP • Máximo: 100 KB</small>
  <div id="firma-preview-new" class="mt-2 d-none">
    <small class="text-muted d-block mb-2">Nueva firma:</small>
    <img id="firma-preview-new-img" src="" alt="Nueva firma" style="...">
  </div>
</div>
```

#### 2. [frontend/js/admin.js](frontend/js/admin.js)
**Cambios:**

**A) Función `saveUsuario()` (líneas 423-476)**
- Agregada lógica de carga de firma
- Si se seleccionó un archivo, se sube a `POST /api/users/{usuarioId}/firma`
- Usa FormData para enviar archivo multipart
- Manejo de errores: Si falla la firma, muestra alerta pero guarda el usuario igual

**B) Manejador de editar usuario (líneas 354-377)**
- Al abrir modal para editar, muestra firma actual del usuario si existe
- Limpia preview de nueva firma
- Oculta/muestra containers de previsualizaciones según sea necesario

**C) Botón "Nuevo Usuario" (líneas 793-818)**
- Limpia todos los campos incluyendo firma
- Oculta previsualizaciones
- Agregado event listener para preview en tiempo real

**D) Event listener para cambio de archivo (líneas 819-832)**
- Cuando el usuario selecciona un archivo, muestra preview automático
- Usa FileReader para lectura local del archivo
- Oculta preview si se limpia el campo

---

## 🔄 Flujo de Uso

### Para Editar Usuario Existente:

1. Admin clickea botón **editar** en tabla de usuarios (lápiz)
2. Se abre Modal con datos del usuario
3. Si usuario ya tiene firma, se muestra en "Firma actual"
4. Admin puede:
   - Dejar la firma como está (no tocar el campo)
   - Cambiarla seleccionando nuevo archivo
   - Ver preview de nueva firma en tiempo real
5. Hace clic en "Guardar"
6. Sistema:
   - Actualiza datos del usuario (nombre, rol, cargo, etc.)
   - Si se seleccionó firma nueva: sube archivo a `/api/users/{id}/firma`
   - Recarga tabla de usuarios

### Para Crear Nuevo Usuario:

1. Admin clickea botón **"+ Nuevo"**
2. Se abre Modal vacío
3. Completa datos: nombre, documento, usuario, rol, cargo, contraseña
4. Opcionalmente: selecciona firma desde el inicio
5. Hace clic "Guardar"
6. Sistema:
   - Crea usuario en BD
   - Sube firma si se seleccionó

---

## 🖼️ Detalles de Firma

### Validación de Archivo
- **Formatos aceptados:** PNG, JPEG, WebP
- **Tamaño máximo:** 100 KB
- **Validación en backend:** `/api/users/{user_id}/firma` (users.py línea 133)

### Almacenamiento
- **Ubicación en servidor:** `backend/media/firmas/`
- **Nombre:** UUID único + extensión (ej: `a1b2c3d4-e5f6...png`)
- **URL almacenada en BD:** `/static/firmas/a1b2c3d4-e5f6...png`

### Preview
- **Tamaño en modal:** 150px ancho máximo, 100px alto máximo
- **Firma actual:** Borde gris, identificado como "Firma actual"
- **Nueva firma:** Borde verde, identificado como "Nueva firma"

---

## 🔗 Integración con Sistema de Generación de Documentos

Cuando se genera un Word con firmas:

1. `generar_context_con_firmas()` obtiene ruta de firma: `/static/firmas/uuid.png`
2. `generar_word_desde_plantilla()` convierte a `InlineImage` (lógica implementada anteriormente)
3. docxtpl inserta la **IMAGEN** en el documento (no el texto)
4. Resultado: Documento con imágenes de firma reales

---

## 🧪 Cómo Probar

### 1. Crear Usuario con Firma
```
Panel Admin → Usuarios → Nuevo
Nombre: Juan Pérez
User: jpérez
Rol: Gerencia
Firma: [Subir imagen PNG/JPG]
Guardar
```

### 2. Editar Usuario y Cambiar Firma
```
Panel Admin → Usuarios → Editar (usuario existente)
Ver "Firma actual" si ya tiene
Seleccionar nuevo archivo
Ver preview de "Nueva firma"
Guardar
```

### 3. Verificar en BD
```
SELECT id, nombre, firma FROM usuarios WHERE firma IS NOT NULL;
```
Debe mostrar rutas como: `/static/firmas/uuid.png`

### 4. Generar Word y Verificar Imagen
```
Módulo Documentos → Documento con firmas → Generar Word
↓
Abrir .docx
↓
Debe aparecer IMAGEN de firma, no texto
```

---

## 📊 Estado de Implementación

## ✅ Completado:

- ✅ Interface HTML en Modal de Usuario
- ✅ Preview de firma actual
- ✅ Preview en tiempo real de nueva firma
- ✅ Carga de firma al guardar usuario
- ✅ Validación de formatos (PNG, JPEG, WebP)
- ✅ Validación de tamaño (100 KB)
- ✅ Manejo de errores
- ✅ Limpieza de firma anterior en disco
- ✅ Solo superadmin puede hacer esto: Protegido por `verify_permissions()` en backend

## ✅ Ya Existente:

- ✅ Backend: Endpoint `POST /api/users/{user_id}/firma`
- ✅ Conversión a InlineImage en `generar_word_desde_plantilla()`
- ✅ Almacenamiento en `/backend/media/firmas/`

---

## 🔐 Seguridad

1. **Permisos:** Backend verifica `verify_permissions(db, id_rol, 'usuarios', 'actualizar')`
   - Solo usuarios con permiso pueden subir firmas
   - Normalmente solo superadmin

2. **Validación de archivos:**
   - MIME type validado (PNG, JPEG, WebP)
   - Tamaño verificado (100 KB máx)
   - Backend re-valida, no solo frontend

3. **Almacenamiento:**
   - Archivos en servidor, rutas en BD
   - Nombres con UUID evitan colisiones
   - Antiguas firmas se eliminan

---

## 📝 Notas

- Si intenta cargar firma sin permisos → 403 Unauthorized
- Si archivo excede 100 KB → Error 400
- Si formato no permitido → Error 400
- El frontend muestra error pero mantiene el usuario guardado
- Usuario puede tener firma = NULL (campo opcional)
- Los usuarios comunes NO ven esta opción (solo en admin panel)

---

## 🔗 archivos Relacionados

- Backend API: [backend/app/router/users.py#L133](backend/app/router/users.py#L133)
- Conversión a imagen: [backend/app/utils/document_generator.py#L50-L92](backend/app/utils/document_generator.py#L50-L92)
- DB Schema: Tabla `usuarios` campo `firma` (VARCHAR)
- Frontend forms: [frontend/admin.html#L200-L230](frontend/admin.html#L200-L230)
- Frontend handlers: [frontend/js/admin.js#L423-L476 + others](frontend/js/admin.js#L423-L476)
