# Plan: Mostrar Imágenes de Firma en Documentos Word

**Fecha:** 09 de Marzo 2026  
**Problema:** Los documentos Word muestran la RUTA del archivo de firma en lugar de la IMAGEN

---

## 1. ANÁLISIS DEL PROBLEMA

### Estado Actual
- **Plantilla Word**: Contiene placeholders `{{gerente_firma}}`, `{{unidad_firma}}`, `{{juridica_firma}}`
- **BD**: Campo `usuarios.firma` almacena rutas como `/static/firmas/db55cb1c-476d-480b-9d69-74e0a348eed8.png`
- **Código actual** (`generar_context_con_firmas`):
  ```python
  context['gerente_firma'] = firma_gerente.get('firma_imagen', '') or ''
  # Resultado: context['gerente_firma'] = "/static/firmas/xxxxx.png"
  ```
- **Resultado en Word**: Se imprime el string de ruta literal, NO la imagen

### Por qué no funciona
docxtpl no puede insertar imágenes desde strings de ruta. Cuando haces:
```python
doc_template.render({'gerente_firma': '/static/firmas/xxxx.png'})
```
docxtpl simplemente imprime el texto "/static/firmas/xxxx.png" en el documento.

---

## 2. SOLUCIÓN TÉCNICA

### La clase InlineImage de docxtpl
Para insertar imágenes, docxtpl requiere objetos `InlineImage`:

```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

doc_template = DocxTemplate(plantilla_path)

# ✅ CORRECTO: Pasar objeto InlineImage
context['gerente_firma'] = InlineImage(doc_template, ruta_imagen, width=Mm(30))

# ❌ INCORRECTO: Pasar string
context['gerente_firma'] = '/static/firmas/xxxx.png'
```

### Parámetros de InlineImage
- **tpl**: El objeto DocxTemplate (necesario para context de docx)
- **image_descriptor**: Ruta completa del archivo o BytesIO
- **width**: Ancho (opcional) - usar `Mm()` o `Inches()` de `docx.shared`
- **height**: Alto (opcional) - si no se especifica, mantiene proporción

---

## 3. PLAN DE IMPLEMENTACIÓN

### Opción A: Modificar `generar_word_desde_plantilla()` (RECOMENDADA)
**Ubicación:** `backend/app/utils/document_generator.py`

**Cambios:**
1. Importar: `from docxtpl import DocxTemplate, InlineImage`
2. Importar: `from docx.shared import Mm`
3. Después de cargar el template, ANTES de render():
   ```python
   # Convertir rutas de firma en objetos InlineImage
   campos_firma = ['gerente_firma', 'unidad_firma', 'juridica_firma']
   for campo in campos_firma:
       if campo in valores_campos and valores_campos[campo]:
           ruta = valores_campos[campo]
           
           # Convertir /static/firmas/xxx.png → backend/media/firmas/xxx.png
           if ruta.startswith('/static/'):
               ruta = ruta.replace('/static/', str(MEDIA_DIR) + '/')
           
           # Crear ruta completa
           ruta_completa = Path(ruta) if Path(ruta).is_absolute() else MEDIA_DIR / ruta
           
           # Si existe el archivo, crear InlineImage
           if ruta_completa.exists():
               valores_campos[campo] = InlineImage(
                   doc_template, 
                   str(ruta_completa), 
                   width=Mm(30)  # ~3cm de ancho
               )
           else:
               # Si no existe, vaciar el campo
               valores_campos[campo] = ''
   ```

**Ventajas:**
- ✅ Cambio en un solo lugar
- ✅ Afecta automáticamente a todos los flujos (FIRMADO, FINALIZADO, PDF)
- ✅ No requiere cambios en CRUD ni router
- ✅ Mantiene separación de responsabilidades (CRUD prepara data, utils formatea)

### Opción B: Modificar `generar_context_con_firmas()`
**Ubicación:** `backend/app/crud/documentos.py`

**Problema:** Requiere pasar el objeto `doc_template` desde router → CRUD, rompiendo la arquitectura actual.

❌ **NO RECOMENDADA** - Acopla mucho el código y requiere cambios en múltiples lugares.

---

## 4. DETALLES DE IMPLEMENTACIÓN

### Mapeo de Rutas
```python
BD Storage:      /static/firmas/db55cb1c-476d-480b-9d69-74e0a348eed8.png
↓
Ruta Real:       C:\GERECI\backend\media\firmas\db55cb1c-476d-480b-9d69-74e0a348eed8.png
                 (MEDIA_DIR / "firmas" / "db55cb1c-476d-480b-9d69-74e0a348eed8.png")
```

### Dimensiones de Firma
Tamaños sugeridos:
- **width=Mm(30)** → ~3cm (tamaño discreto, profesional)
- **width=Mm(40)** → ~4cm (tamaño medio)
- **width=Mm(50)** → ~5cm (tamaño grande)

Se puede hacer configurable o extraer de la plantilla.

### Manejo de Errores
1. **Archivo no existe**: Dejar campo vacío `''`
2. **Ruta es None o vacía**: Dejar campo vacío
3. **Formato de imagen no soportado**: Dejar vacío (docxtpl soporta PNG, JPG, GIF)
4. **Archivo corrupto**: Catch Exception y dejar vacío

---

## 5. ARCHIVOS A MODIFICAR

### backend/app/utils/document_generator.py

**Líneas ~1-15 (Imports):**
```python
# AGREGAR:
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
```

**Líneas ~50-58 (dentro de generar_word_desde_plantilla, ANTES de render):**
```python
# AGREGAR ANTES DE: doc_template.render(valores_campos)

# Convertir campos de firma de string → InlineImage
campos_firma = ['gerente_firma', 'unidad_firma', 'juridica_firma']
for campo in campos_firma:
    if campo in valores_campos and valores_campos[campo]:
        ruta_firma = valores_campos[campo]
        
        # Convertir ruta relativa/web a ruta absoluta del sistema
        if isinstance(ruta_firma, str) and ruta_firma.startswith('/static/'):
            ruta_firma = ruta_firma.replace('/static/', '')
        
        # Construir ruta completa
        ruta_completa = MEDIA_DIR / ruta_firma.lstrip('/')
        
        # Si existe el archivo, crear InlineImage
        if ruta_completa.exists():
            try:
                valores_campos[campo] = InlineImage(
                    doc_template, 
                    str(ruta_completa), 
                    width=Mm(30)
                )
                logger.info(f"Firma {campo} convertida a imagen: {ruta_completa}")
            except Exception as e:
                logger.warning(f"Error al cargar firma {campo}: {e}")
                valores_campos[campo] = ''
        else:
            logger.warning(f"Archivo de firma no encontrado: {ruta_completa}")
            valores_campos[campo] = ''
```

---

## 6. TESTING

### Test Manual
1. Tomar documento 47 (ya tiene firmas registradas)
2. Llamar endpoint `/generar-word` con doc_id=47
3. Abrir el Word generado
4. **Verificar:** Debe aparecer la IMAGEN de firma, no la ruta de texto

### Test Automatizado (opcional)
```python
# Script: test_firmas_imagen.py
from backend.app.utils.document_generator import generar_word_desde_plantilla
from backend.app.crud.documentos import generar_context_con_firmas
from backend.core.database import get_db

db = next(get_db())
context = generar_context_con_firmas(db, 47)

# Verificar que el context tiene rutas de string
assert isinstance(context['gerente_firma'], str)

# Generar Word
plantilla_path = "backend/media/plantillas/7145eb42-4d7a-4bce-b85b-d93834106aa6.docx"
word_path = generar_word_desde_plantilla(plantilla_path, 47, context)

# Verificar que InlineImage se aplicó (visual, requiere abrir Word)
print(f"Word generado: {word_path}")
print("Abrir manualmente y verificar imágenes de firma")
```

---

## 7. RIESGOS Y CONSIDERACIONES

### ✅ Ventajas
- Implementación limpia y centralizada
- No rompe funcionalidad existente (si no hay firma, queda vacío como ahora)
- Compatible con todos los flujos (FIRMADO, FINALIZADO, PDF)
- Fácil de revertir si hay problemas

### ⚠️ Riesgos
- **Tamaño de archivo Word**: Las imágenes incrustadas aumentan el tamaño
  - Mitigación: Comprimir imágenes al subirlas (ya se hace en backend)
- **Formatos no soportados**: Si alguien sube BMP, TIFF, etc.
  - Mitigación: Validar formato en upload (solo PNG/JPG)
- **Resolución de imagen**: Firmas de baja calidad se verán pixeladas
  - Mitigación: Establecer tamaño mínimo en upload (300x100 px)

### 🔍 Testing Crítico
- Probar con documento SIN firmas (debe quedar vacío sin error)
- Probar con firma que no existe en disco (debe manejar gracefully)
- Probar con 1, 2 y 3 firmas (Circular vs Resolución)
- Verificar que PDF final también muestra imágenes (Word → PDF)

---

## 8. RESUMEN EJECUTIVO

**¿Qué hacer?**
Agregar 15-20 líneas de código en `document_generator.py` para convertir strings de ruta en objetos `InlineImage` antes de renderizar.

**¿Dónde?**
Archivo: `backend/app/utils/document_generator.py`  
Función: `generar_word_desde_plantilla()`  
Ubicación: Líneas ~50-58 (ANTES de `doc_template.render()`)

**¿Cuándo probar?**
Documento 47 (Resolución con 3 firmas ya registradas)

**¿Riesgo?**
🟢 BAJO - Cambio aislado, fácil de revertir, no afecta BD ni API

**¿Tiempo estimado?**
- Implementación: 15 minutos
- Testing: 10 minutos
- **Total: 25 minutos**
