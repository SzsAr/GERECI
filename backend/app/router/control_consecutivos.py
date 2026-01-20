"""
Router for control_consecutivos management
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from core.database import get_db
from app.api.dependencies import get_current_user
from app.crud.permisos import verify_permissions
from app.crud import control_consecutivos as crud_consecutivos
from app.schemas.control_consecutivos import ConsecutivoOut, ConsecutivoCreate, ConsecutivoReset
from app.schemas.users import UserOut

router = APIRouter()
modulo = 5  # Módulo 5: consecutivos


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_consecutivo(
    consecutivo: ConsecutivoCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Crear control de consecutivo para un tipo de documento - requiere permiso de insertar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para crear consecutivos')

        success = crud_consecutivos.create_consecutivo(
            db,
            consecutivo.id_tipo_documento,
            consecutivo.numero_inicial
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Ya existe un consecutivo para este tipo de documento")
        
        return {
            "message": "Consecutivo creado correctamente",
            "id_tipo_documento": consecutivo.id_tipo_documento,
            "numero_inicial": consecutivo.numero_inicial
        }
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Ya existe un consecutivo para este tipo de documento")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ConsecutivoOut])
def list_consecutivos(
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Listar todos los consecutivos - requiere permiso de seleccionar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para ver consecutivos')

        return crud_consecutivos.get_all_consecutivos(db)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id_tipo_documento}", response_model=ConsecutivoOut)
def get_consecutivo(
    id_tipo_documento: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Obtener consecutivo por tipo de documento - requiere permiso de seleccionar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para ver consecutivos')

        consecutivo = crud_consecutivos.get_consecutivo_by_id_tipo(db, id_tipo_documento)
        if not consecutivo:
            raise HTTPException(status_code=404, detail="Consecutivo no encontrado")
        
        return consecutivo
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id_tipo_documento}", status_code=status.HTTP_200_OK)
def update_consecutivo(
    id_tipo_documento: int,
    data: ConsecutivoReset,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Cambiar manualmente el número del consecutivo - requiere permiso de actualizar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para cambiar consecutivos')

        # Verificar que existe
        consecutivo = crud_consecutivos.get_consecutivo_by_id_tipo(db, id_tipo_documento)
        if not consecutivo:
            raise HTTPException(status_code=404, detail="Consecutivo no encontrado")

        success = crud_consecutivos.reset_consecutivo(db, id_tipo_documento, data.nuevo_numero)
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo cambiar el consecutivo")
        
        return {
            "message": "Consecutivo actualizado correctamente",
            "id_tipo_documento": id_tipo_documento,
            "nuevo_numero": data.nuevo_numero
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id_tipo_documento}", status_code=status.HTTP_200_OK)
def delete_consecutivo(
    id_tipo_documento: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Eliminar control de consecutivo - requiere permiso de borrar"""
    try:
        id_rol = user_token.id_rol
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(status_code=403, detail='Usuario no autorizado para eliminar consecutivos')

        # Verificar que existe
        consecutivo = crud_consecutivos.get_consecutivo_by_id_tipo(db, id_tipo_documento)
        if not consecutivo:
            raise HTTPException(status_code=404, detail="Consecutivo no encontrado")

        success = crud_consecutivos.delete_consecutivo(db, id_tipo_documento)
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo eliminar el consecutivo")
        
        return {"message": "Consecutivo eliminado correctamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
