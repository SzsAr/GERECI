"""
Router for plantillas management - gestión de plantillas y tablas dinámicas
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json

from core.database import get_db
from app.api.dependencies import get_current_user
from app.crud.permisos import verify_permissions
from app.crud import plantillas as crud_plantillas
from app.schemas.plantillas import PlantillaCreate, PlantillaUpdate, PlantillaOut
from app.schemas.users import UserOut

router = APIRouter()
modulo = 9  # Módulo 9: plantillas


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_plantilla(
    plantilla: PlantillaCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear una plantilla y su tabla dinámica asociada.
    Requiere permiso de insertar en módulo Plantillas.
    
    Args:
        plantilla: PlantillaCreate con id_tipo, nombre, campos_json, descripcion
        
    Returns:
        Dict con id de la plantilla, nombre, tabla dinámica creada y campos
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear plantillas'
            )
        
        # Crear plantilla (y su tabla dinámica automáticamente)
        plantilla_id = crud_plantillas.create_plantilla(
            db,
            id_tipo=plantilla.id_tipo,
            nombre=plantilla.nombre,
            campos_json=plantilla.campos_json,
            descripcion=plantilla.descripcion
        )
        
        return {
            "message": "Plantilla creada correctamente",
            "id": plantilla_id,
            "nombre": plantilla.nombre,
            "id_tipo": plantilla.id_tipo,
            "campos_json": plantilla.campos_json,
            "descripcion": plantilla.descripcion
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_all_plantillas(
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las plantillas activas.
    Requiere permiso de seleccionar en módulo Plantillas.
    Retorna Response con JSON serializado manualmente para preservar orden de campos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver plantillas'
            )
        
        plantillas = crud_plantillas.get_all_plantillas(db)
        
        # Convertir datetime a string para serialización JSON
        for p in plantillas:
            if p.get('fecha_creacion'):
                p['fecha_creacion'] = p['fecha_creacion'].isoformat()
        
        # Serializar manualmente con json.dumps para preservar orden (sort_keys=False)
        json_content = json.dumps(plantillas, ensure_ascii=False, sort_keys=False, default=str)
        
        # Retornar Response con JSON pre-serializado
        return Response(
            content=json_content,
            media_type="application/json; charset=utf-8"
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tipo/{id_tipo}", response_model=List[PlantillaOut])
def get_plantillas_by_tipo(
    id_tipo: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener plantillas de un tipo de documento específico.
    Requiere permiso de seleccionar en módulo Plantillas.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver plantillas'
            )
        
        plantillas = crud_plantillas.get_plantillas_by_tipo(db, id_tipo)
        return plantillas
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plantilla_id}", response_model=PlantillaOut)
def get_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener una plantilla por ID.
    Requiere permiso de seleccionar en módulo Plantillas.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver plantillas'
            )
        
        plantilla = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        return plantilla
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{plantilla_id}", response_model=dict)
def update_plantilla(
    plantilla_id: int,
    plantilla_update: PlantillaUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Actualizar una plantilla (nombre, descripción, estado).
    NO se pueden cambiar los campos_json ni id_tipo.
    Requiere permiso de actualizar en módulo Plantillas.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar plantillas'
            )
        
        # Verificar que la plantilla existe
        plantilla = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Actualizar
        success = crud_plantillas.update_plantilla(
            db,
            plantilla_id,
            nombre=plantilla_update.nombre,
            descripcion=plantilla_update.descripcion,
            estado=plantilla_update.estado
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="No se realizaron cambios")
        
        return {"message": "Plantilla actualizada correctamente"}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{plantilla_id}", response_model=dict)
def delete_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar una plantilla y su tabla dinámica asociada.
    Requiere permiso de borrar en módulo Plantillas.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar plantillas'
            )
        
        # Verificar que la plantilla existe
        plantilla = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Eliminar (también elimina la tabla dinámica)
        success = crud_plantillas.delete_plantilla(db, plantilla_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo eliminar la plantilla")
        
        return {"message": "Plantilla eliminada correctamente"}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plantilla_id}/upload-archivo", response_model=dict)
async def upload_archivo_plantilla(
    plantilla_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Subir archivo .docx de plantilla con placeholders Jinja2.
    El archivo Word debe contener variables en formato {{ nombre_variable }}.
    
    Ejemplos de placeholders válidos:
    - Variables simples: {{ consecutivo }}, {{ fecha }}, {{ asunto }}
    - Condicionales: {% if aprobado %}Texto{% endif %}
    - Bucles: {% for item in items %}{{ item.nombre }}{% endfor %}
    
    Requiere permiso de actualizar en módulo Plantillas.
    Solo acepta archivos .docx.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para subir archivos de plantillas'
            )
        
        # Verificar que la plantilla existe
        plantilla = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Validar tipo de archivo
        if not archivo.filename.lower().endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser .docx"
            )
        
        # Validar content-type
        if archivo.content_type not in [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/octet-stream'
        ]:
            raise HTTPException(
                status_code=400,
                detail="Tipo de archivo inválido. Solo se aceptan archivos .docx"
            )
        
        # Leer contenido del archivo
        contenido = await archivo.read()
        
        # Validar tamaño (máximo 10MB)
        if len(contenido) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="El archivo es demasiado grande. Máximo 10MB"
            )
        
        # Guardar archivo
        resultado = crud_plantillas.guardar_archivo_plantilla(
            db,
            plantilla_id,
            contenido,
            archivo.filename
        )
        
        return {
            "message": "Archivo de plantilla subido correctamente",
            "plantilla_id": plantilla_id,
            "nombre_archivo": resultado["nombre_archivo"],
            "ruta_almacenamiento": resultado["ruta_almacenamiento"]
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/guia-placeholders", response_model=dict)
def obtener_guia_placeholders(
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener guía de placeholders disponibles para usar en plantillas Word.
    Muestra ejemplos de sintaxis Jinja2 para variables, condicionales y bucles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado'
            )
        
        return {
            "message": "Guía de placeholders para plantillas Word con docxtpl",
            "sintaxis_basica": {
                "variables_simples": "{{ nombre_variable }}",
                "ejemplo": "Resolución {{ consecutivo }} de fecha {{ fecha }}"
            },
            "richtext_piloto": {
                "sintaxis": "{{r rt_contenido }}",
                "nota": "Piloto activo solo para el campo 'contenido'. Si no se usa, {{ contenido }} sigue funcionando en modo clásico."
            },
            "condicionales": {
                "sintaxis": "{% if condicion %}Texto si verdadero{% else %}Texto si falso{% endif %}",
                "ejemplo": "{% if aprobado %}APROBADO{% else %}RECHAZADO{% endif %}"
            },
            "bucles": {
                "sintaxis": "{% for item in lista %}{{ item.propiedad }}{% endfor %}",
                "ejemplo": "{% for producto in productos %}{{ producto.nombre }}: {{ producto.cantidad }}{% endfor %}"
            },
            "variables_sistema": {
                "consecutivo": "Número consecutivo del documento (asignado al finalizar)",
                "fecha": "Fecha de emisión del documento",
                "fecha_emision": "Fecha de emisión (formato completo)",
                "asunto": "Asunto del documento",
                "usuario_nombre": "Nombre del usuario que crea el documento",
                "tipo_documento": "Tipo de documento (Resolución, Circular, etc)",
                "plantilla_nombre": "Nombre de la plantilla"
            },
            "campos_personalizados": "Los campos definidos en 'valores_campos' al crear el documento estarán disponibles como {{ nombre_campo }}",
            "ejemplo_completo": """
RESOLUCIÓN {{ consecutivo }}

Fecha: {{ fecha }}
Asunto: {{ asunto }}

Por medio de la presente, {{ usuario_nombre }}.

{% if items %}
Listado de elementos:
{% for item in items %}
  - {{ item.descripcion }}: {{ item.cantidad }} unidades
{% endfor %}
{% endif %}

Observaciones: {{ observaciones }}
            """
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plantilla_id}/placeholders", response_model=dict)
def obtener_placeholders_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener lista de placeholders (variables) definidos en la plantilla Word.
    Analiza el archivo .docx y extrae todas las variables {{ variable }},
    bucles {% for %} y condicionales {% if %}.
    
    Útil para saber qué campos debe rellenar el usuario al crear un documento.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado'
            )
        
        # Verificar que la plantilla existe
        plantilla = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Extraer placeholders
        placeholders = crud_plantillas.extraer_placeholders_de_plantilla(plantilla_id, db)
        
        return {
            "plantilla_id": plantilla_id,
            "nombre_plantilla": plantilla.get('nombre'),
            "nombre_archivo": plantilla.get('nombre_archivo'),
            **placeholders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


