# Contexto para el agente de soporte

## Sistema de Gestión de Documentos

El módulo de documentos es el más complejo del sistema GERECI.

### Backend
- ✅ Endpoint: `GET /documentos/{id}/datos`
  - Retorna todos los datos del documento en formato **JSON**
  - Incluye: id, asunto, contenido, estado, valores_campos, tipo, plantilla, usuario, etc.
  - Respeta permisos de módulo

---

## Estado actual del proyecto
- **Generación de PDF**: Deshabilitada temporalmente.
- **Backend**: Corriendo correctamente en `http://127.0.0.1:8000`
- **Base de datos**: MySQL `gereci` con todas las tablas operativas

## Dependencias Python actuales
Todas las dependencias relacionadas con JasperReports fueron removidas del proyecto.

Dependencias requeridas:
- fastapi, uvicorn
- sqlalchemy, pymysql
- python-dotenv
- pydantic, pydantic-settings, annotated-types
- python-jose, passlib[bcrypt]
- docxtpl, pillow
- email-validator
- httpx, httpcore, anyio, h11, websockets
- lxml

## Cómo levantar el proyecto
```bash
cd C:\GERECI\backend
C:\GERECI\venv\Scripts\python.exe -m uvicorn main:app --reload
```

O ejecutar: `& C:\GERECI\start_backend.bat`

## Rutas clave
- Backend app: `backend/`
- Routers: `backend/app/router/` - todos los endpoints API
- CRUD: `backend/app/crud/` - lógica de BD
- Schemas: `backend/app/schemas/` - validaciones Pydantic
- Media salida: `backend/media/documentos_generados`

## Endpoints principales
- `POST /auth/token` - Login (OAuth2)
- `GET /documentos` - Listar documentos
- `POST /documentos/create` - Crear documento
- `GET /documentos/{id}` - Obtener documento
- `POST /documentos/{id}/generar-pdf` - Stub (no implementado)

## Base de datos
- Host: localhost
- Usuario: root
- Password: 1234
- Base: gereci
- Tablas principales: usuarios, documentos, plantillas, roles, permisos, etc.

## Próximos pasos sugeridos
1. Implementar alternativa para generación de PDF (ReportLab, WeasyPrint, etc.)
2. O mantener endpoint como stub si no se requiere por ahora
