"""
Router for plantillas management
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import json
import uuid

from core.database import get_db
from app.api.dependencies import get_current_user
from app.crud.permisos import verify_permissions
from app.crud import plantillas as crud_plantillas
from app.schemas.plantillas import PlantillaCreate, PlantillaUpdate, PlantillaOut
from app.schemas.users import UserOut

router = APIRouter()
modulo = 9  # Módulo 9: plantillas

# Directorio para guardar plantillas (archivos Word)
PLANTILLAS_DIR = Path(__file__).parent.parent.parent / "media" / "plantillas"
PLANTILLAS_DIR.mkdir(parents=True, exist_ok=True)

# Tipos MIME permitidos para plantillas (solo .docx)
ALLOWED_MIMETYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_plantilla(
    id_tipo: int = Form(...),
    nombre: str = Form(...),
    nombre_archivo: str = Form(None),
    campos_json: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Crear plantilla y subir archivo Word - requiere permiso de insertar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para crear plantillas')

        # Validar MIME
        if file.content_type not in ALLOWED_MIMETYPES:
            raise HTTPException(
                status_code=400,
                detail="Tipo de archivo no permitido. Solo se aceptan archivos .docx (Word 2007+)"
            )

        contents = file.file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )

        # Si no proporciona nombre_archivo, usar el del upload
        if not nombre_archivo:
            nombre_archivo = file.filename

        # Guardar archivo con nombre único
        ext = file.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = PLANTILLAS_DIR / filename
        with open(filepath, "wb") as f:
            f.write(contents)

        ruta_publica = f"/static/plantillas/{filename}"

        # Parsear campos_json si viene como string
        campos_dict = None
        if campos_json:
            try:
                campos_dict = json.loads(campos_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="campos_json no es un JSON válido")

        plantilla_id = crud_plantillas.create_plantilla(
            db,
            id_tipo,
            nombre,
            nombre_archivo,
            ruta_publica,
            campos_dict,
        )
        return {
            "message": "Plantilla creada correctamente",
            "id": plantilla_id,
            "nombre_archivo": nombre_archivo,
            "ruta": ruta_publica,
            "campos_json": campos_dict,
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PlantillaOut])
def list_plantillas(
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Listar todas las plantillas - acceso para usuarios autenticados"""
    try:
        return crud_plantillas.get_all_plantillas(db)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plantilla_id}", response_model=PlantillaOut)
def get_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Obtener una plantilla por ID - requiere permiso de seleccionar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para ver plantillas')

        plantilla_db = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla_db:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        return plantilla_db
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{plantilla_id}", status_code=status.HTTP_200_OK)
def update_plantilla(
    plantilla_id: int,
    id_tipo: int = Form(None),
    nombre: str = Form(None),
    nombre_archivo: str = Form(None),
    campos_json: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Actualizar plantilla y/o subir nuevo archivo Word - requiere permiso de actualizar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para actualizar plantillas')

        plantilla_db = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla_db:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        # plantilla_db viene como Mapping; usar acceso por clave
        ruta_almacenamiento = plantilla_db.get("ruta_almacenamiento")
        campos_dict = None

        # Si se proporciona archivo, procesarlo
        if file and file.filename:
            # Validar MIME
            if file.content_type not in ALLOWED_MIMETYPES:
                raise HTTPException(
                    status_code=400,
                    detail="Tipo de archivo no permitido. Solo se aceptan archivos .docx (Word 2007+)"
                )

            contents = file.file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // (1024 * 1024)} MB"
                )

            # Eliminar archivo anterior si existe
            if plantilla_db.get("ruta_almacenamiento"):
                old_filename = plantilla_db["ruta_almacenamiento"].split("/")[-1]
                old_filepath = PLANTILLAS_DIR / old_filename
                if old_filepath.exists():
                    old_filepath.unlink()

            # Guardar nuevo archivo
            ext = file.filename.split(".")[-1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = PLANTILLAS_DIR / filename
            with open(filepath, "wb") as f:
                f.write(contents)

            ruta_almacenamiento = f"/static/plantillas/{filename}"

            # Si no proporciona nombre_archivo, usar el del nuevo upload
            if not nombre_archivo:
                nombre_archivo = file.filename

        # Parsear campos_json si viene como string
        if campos_json:
            try:
                campos_dict = json.loads(campos_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="campos_json no es un JSON válido")

        success = crud_plantillas.update_plantilla(
            db,
            plantilla_id,
            id_tipo,
            nombre,
            nombre_archivo,
            ruta_almacenamiento,
            campos_dict,
        )
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la plantilla")
        return {"message": "Plantilla actualizada correctamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plantilla_id}", status_code=status.HTTP_200_OK)
def delete_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Eliminar una plantilla - requiere permiso de borrar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para eliminar plantillas')

        plantilla_db = crud_plantillas.get_plantilla_by_id(db, plantilla_id)
        if not plantilla_db:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")

        success = crud_plantillas.delete_plantilla(db, plantilla_id)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo eliminar la plantilla")
        return {"message": "Plantilla eliminada correctamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
