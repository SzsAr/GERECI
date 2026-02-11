# Guía de Plantillas Word con docxtpl - Sistema GERECI

## ¿Cómo funciona el sistema de plantillas?

El sistema utiliza **docxtpl** para generar documentos Word dinámicos desde plantillas con **placeholders en formato Jinja2**.

### Flujo completo:

1. **Diseñas la plantilla en Word** con el formato visual que desees (logos, tablas, estilos)
2. **Insertas variables** donde quieres que aparezcan los datos dinámicos
3. **Subes el archivo .docx** mediante el endpoint `/plantillas/{id}/upload-archivo`
4. **Creas documentos** que usan esa plantilla
5. **El sistema reemplaza** automáticamente los placeholders con valores reales

---

## Sintaxis de placeholders (Jinja2)

### 1. Variables simples
```
{{ nombre_variable }}
```

**Ejemplos:**
```
Resolución número: {{ consecutivo }}
Fecha: {{ fecha }}
Asunto: {{ asunto }}
Generado por: {{ usuario_nombre }}
```

---

### 2. Condicionales
```
{% if condicion %}
  Texto si es verdadero
{% else %}
  Texto si es falso
{% endif %}
```

**Ejemplo:**
```
Estado: {% if aprobado %}APROBADO{% else %}RECHAZADO{% endif %}

{% if observaciones %}
Observaciones: {{ observaciones }}
{% endif %}
```

---

### 3. Bucles (para listas/tablas)
```
{% for item in lista %}
  {{ item.propiedad }}
{% endfor %}
```

**Ejemplo de tabla:**
```
| Producto         | Cantidad | Precio    |
|------------------|----------|-----------|
{% for prod in productos %}
| {{ prod.nombre }} | {{ prod.cantidad }} | {{ prod.precio }} |
{% endfor %}
```

**Ejemplo de lista:**
```
{% for item in items %}
  - {{ item.descripcion }}: {{ item.cantidad }} unidades
{% endfor %}
```

---

## Variables del sistema disponibles

Estas variables están **siempre disponibles** en todas las plantillas:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `{{ consecutivo }}` | Número consecutivo del documento | "15" o "RES-015" |
| `{{ fecha }}` | Fecha de emisión | "2026-02-09" |
| `{{ fecha_emision }}` | Fecha completa de emisión | "2026-02-09" |
| `{{ asunto }}` | Asunto del documento | "Solicitud de compra" |
| `{{ usuario_nombre }}` | Usuario que creó el documento | "Juan Pérez" |
| `{{ tipo_documento }}` | Tipo (Resolución, Circular) | "Resolución" |
| `{{ plantilla_nombre }}` | Nombre de la plantilla | "Resolución estándar" |

---

## Campos personalizados

Cuando creas un documento con `valores_campos`, todas esas propiedades están disponibles:

**Crear documento:**
```json
{
  "id_plantilla": 1,
  "asunto": "Solicitud de equipos",
  "valores_campos": {
    "solicitante": "Ana García",
    "unidad": "Sistemas",
    "cargo": "Coordinadora",
    "observaciones": "Urgente para el proyecto X",
    "items": [
      {"descripcion": "Laptop Dell", "cantidad": 2, "precio": 1500},
      {"descripcion": "Mouse inalámbrico", "cantidad": 5, "precio": 25}
    ]
  }
}
```

**En la plantilla Word:**
```
Solicitud presentada por: {{ solicitante }}
Cargo: {{ cargo }}
Unidad: {{ unidad }}

Listado de equipos:
{% for item in items %}
  - {{ item.descripcion }} ({{ item.cantidad }} unidades) - ${{ item.precio }}
{% endfor %}

Total items: {{ items|length }}

{% if observaciones %}
Observaciones especiales: {{ observaciones }}
{% endif %}
```

---

## Ejemplo completo de plantilla de Resolución

```
                        RESOLUCIÓN {{ consecutivo }}

Fecha: {{ fecha }}
Tipo: {{ tipo_documento }}

ASUNTO: {{ asunto }}

Por medio de la presente, el/la {{ cargo }} {{ solicitante }} de la 
unidad {{ unidad }}, solicita lo siguiente:

{% if items %}
DETALLE DE SOLICITUD:
{% for item in items %}
  {{ loop.index }}. {{ item.descripcion }}
     - Cantidad: {{ item.cantidad }}
     - Justificación: {{ item.justificacion }}
{% endfor %}
{% endif %}

CONSIDERANDO:
{% for considerando in considerandos %}
  {{ loop.index }}. {{ considerando }}
{% endfor %}

RESUELVE:
{% if aprobado %}
Aprobar la presente solicitud según los términos establecidos.
{% else %}
No aprobar la solicitud por las siguientes razones:
{{ razon_rechazo }}
{% endif %}

{% if observaciones %}
OBSERVACIONES:
{{ observaciones }}
{% endif %}

Generado por: {{ usuario_nombre }}
Sistema GERECI - {{ fecha }}

____________________________
Firma
```

---

## Filtros útiles de Jinja2

```
{{ variable|upper }}           - En mayúsculas: "HOLA"
{{ variable|lower }}           - En minúsculas: "hola"
{{ variable|capitalize }}      - Primera letra mayúscula: "Hola"
{{ variable|title }}           - Título: "Hola Mundo"
{{ lista|length }}             - Cantidad de elementos: "5"
{{ numero|round(2) }}          - Redondear: "10.50"
{{ fecha|strftime('%d/%m/%Y') }} - Formatear fecha (si es datetime)
```

---

## Endpoints del sistema

### 1. Subir archivo de plantilla
```http
POST /plantillas/{plantilla_id}/upload-archivo
Content-Type: multipart/form-data

archivo: [archivo.docx]
```

### 2. Ver placeholders de una plantilla
```http
GET /plantillas/{plantilla_id}/placeholders

Response:
{
  "plantilla_id": 1,
  "nombre_plantilla": "Resolución",
  "variables_encontradas": ["consecutivo", "fecha", "asunto", "solicitante"],
  "listas_bucles": ["items", "considerandos"],
  "condicionales": ["aprobado", "observaciones"],
  "total_placeholders": 8
}
```

### 3. Guía de placeholders
```http
GET /plantillas/guia-placeholders
```

### 4. Generar documento desde plantilla
```http
POST /documentos/{documento_id}/generar-word
```

---

## Consejos y buenas prácticas

1. **Diseña primero en Word**: crea el documento con todo el formato visual (logos, estilos, tablas)
2. **Reemplaza valores por placeholders**: donde antes ponías datos fijos, pon `{{ variable }}`
3. **Usa nombres descriptivos**: `{{ nombre_solicitante }}` es mejor que `{{ ns }}`
4. **Prueba con datos de ejemplo**: crea un documento de prueba para ver si los placeholders funcionan
5. **Usa condicionales para campos opcionales**: evita espacios vacíos si un campo no tiene valor
6. **Tablas dinámicas**: usa `{% for %}` dentro de las celdas de una tabla de Word
7. **Mantén formato consistente**: los placeholders heredan el formato del texto donde están

---

## Limitaciones

- Solo archivos **.docx** (formato Office 2007+)
- Máximo **10MB** por archivo
- Los placeholders deben estar en el **cuerpo del documento** (no en encabezados/pies de página en esta versión)
- No se pueden modificar imágenes dinámicamente (las imágenes son estáticas)

---

## Solución de problemas

**"Plantilla no tiene archivo asociado"**
→ Debes subir el .docx mediante `/plantillas/{id}/upload-archivo`

**"Variable no definida"**
→ Asegúrate de incluir esa variable en `valores_campos` al crear el documento

**"Error al generar PDF"**
→ Verifica que LibreOffice esté instalado en el servidor

**"Formato incorrecto"**
→ Asegúrate de usar `{{ }}` para variables y `{% %}` para lógica

---

## Flujo completo de ejemplo

1. **Crear plantilla base:**
```http
POST /plantillas
{
  "id_tipo": 3,
  "nombre": "Resolución estándar",
  "campos_json": {"solicitante": "varchar", "unidad": "varchar"},
  "descripcion": "Plantilla para resoluciones"
}
```

2. **Subir archivo Word:**
```http
POST /plantillas/5/upload-archivo
[archivo: resolucion_template.docx]
```

3. **Ver qué placeholders tiene:**
```http
GET /plantillas/5/placeholders
```

4. **Crear documento:**
```http
POST /documentos/create
{
  "id_plantilla": 5,
  "asunto": "Compra de equipos",
  "valores_campos": {
    "solicitante": "Juan Pérez",
    "unidad": "Sistemas",
    "items": [...]
  }
}
```

5. **Generar Word:**
```http
POST /documentos/1/generar-word
```

6. **Enviar a aprobación:**
```http
PUT /documentos/1/estado
{"nuevo_estado": "ENVIADO_JURIDICA"}
```

7. **Al finalizar → PDF automático:**
```http
PUT /documentos/1/estado
{"nuevo_estado": "FINALIZADO"}
```

---

## Recursos adicionales

- Documentación oficial docxtpl: https://docxtpl.readthedocs.io/
- Sintaxis Jinja2: https://jinja.palletsprojects.com/

---

**Sistema GERECI - Gestión de Resoluciones y Circulares**  
Versión 1.0 - Febrero 2026
